from __future__ import annotations

import base64
import binascii
import calendar
import json
import re
import secrets
import hashlib
import uuid
from datetime import date, datetime, timedelta
from typing import Any
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.business import Appointment, Customer, Professional, ServiceCatalog
from app.models.company import Company
from app.models.public_booking import PublicBookingConfig, SingleUseBookingLink
from app.models.user import User
from app.routes.deps import get_current_user

router = APIRouter(tags=["public-booking"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))

PT_MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

DEFAULT_BOOKING_SETTINGS: dict[str, Any] = {
    "studio_nome": "DSYSTEM STUDIO",
    "marca_texto": "DSYSTEM STUDIO",
    "logo_data_url": "",
    "tema": "claro",
    "horario_inicio": "08:00",
    "horario_fim": "18:00",
    "intervalo_min": 15,
    "tempo_pausa_min": 10,
    "max_agendamentos_dia": 20,
    "funcionamento_dias": "1,2,3,4,5",
    "mostrar_selo": False,
    "agendamento_online_modo": "flexivel",
    "agendamento_online_horarios_fixos": "08:00,10:00,14:00,16:00",
    "agendamento_online_meses_modo": "todos",
    "agendamento_online_meses": "1,2,3,4,5,6,7,8,9,10,11,12",
}

ALLOWED_SETTINGS = set(DEFAULT_BOOKING_SETTINGS)

# Campos cuja autoridade pertence ao DS Go. O endpoint do Studio nunca pode
# sobrescrevê-los depois que a configuração central existe.
DS_GO_AUTHORITY_SETTINGS = {
    "agendamento_online_modo",
    "agendamento_online_horarios_fixos",
    "agendamento_online_meses_modo",
    "agendamento_online_meses",
}


def _studio_payload_respecting_ds_go_authority(payload: dict[str, Any], has_existing: bool) -> dict[str, Any]:
    safe = dict(payload or {})
    # O Studio não manda no liga/desliga. Se ainda não houver configuração,
    # nasce desativada até o Master publicar pelo DS Go.
    safe.pop("enabled", None)
    if not has_existing:
        safe["enabled"] = False

    raw_settings = safe.get("settings")
    if isinstance(raw_settings, dict):
        settings = dict(raw_settings)
        for key in DS_GO_AUTHORITY_SETTINGS:
            settings.pop(key, None)
        safe["settings"] = settings
    else:
        # Compatibilidade com payload legado que envia settings na raiz.
        for key in DS_GO_AUTHORITY_SETTINGS:
            safe.pop(key, None)
    safe["source"] = str(safe.get("source") or "desktop_sync")[:80]
    return safe


def _company_by_slug(db: Session, slug: str) -> Company:
    company = (
        db.query(Company)
        .filter(Company.slug == slug.strip(), Company.is_active == True)  # noqa: E712
        .first()
    )
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return company


def _config_record(db: Session, company_id: int) -> PublicBookingConfig | None:
    return db.query(PublicBookingConfig).filter(PublicBookingConfig.company_id == company_id).first()


def _settings(record: PublicBookingConfig | None) -> dict[str, Any]:
    out = dict(DEFAULT_BOOKING_SETTINGS)
    if record and isinstance(record.settings_json, dict):
        out.update({k: v for k, v in record.settings_json.items() if k in ALLOWED_SETTINGS})
    return out


def _normalize_settings(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key in ALLOWED_SETTINGS:
        if key in payload:
            cleaned[key] = payload[key]

    for key in ("intervalo_min", "tempo_pausa_min", "max_agendamentos_dia"):
        if key in cleaned:
            try:
                cleaned[key] = max(0, int(cleaned[key]))
            except Exception:
                cleaned.pop(key, None)

    if "mostrar_selo" in cleaned:
        cleaned["mostrar_selo"] = bool(cleaned["mostrar_selo"])

    if "agendamento_online_modo" in cleaned:
        modo = str(cleaned["agendamento_online_modo"] or "flexivel").strip().lower()
        cleaned["agendamento_online_modo"] = "fixo" if modo == "fixo" else "flexivel"

    if "funcionamento_dias" in cleaned:
        cleaned["funcionamento_dias"] = _normalize_work_days(cleaned["funcionamento_dias"])

    if "agendamento_online_horarios_fixos" in cleaned:
        cleaned["agendamento_online_horarios_fixos"] = ",".join(_normalize_fixed_times(cleaned["agendamento_online_horarios_fixos"]))

    if "agendamento_online_meses_modo" in cleaned:
        mode = str(cleaned.get("agendamento_online_meses_modo") or "todos").strip().lower()
        cleaned["agendamento_online_meses_modo"] = mode if mode in {"todos", "um", "personalizado"} else "todos"

    if "agendamento_online_meses" in cleaned:
        cleaned["agendamento_online_meses"] = _normalize_booking_months(cleaned.get("agendamento_online_meses"))

    for key in ("horario_inicio", "horario_fim"):
        if key in cleaned:
            try:
                cleaned[key] = datetime.strptime(str(cleaned[key]), "%H:%M").strftime("%H:%M")
            except Exception:
                cleaned.pop(key, None)

    for key in ("studio_nome", "marca_texto", "tema"):
        if key in cleaned:
            cleaned[key] = str(cleaned[key] or "").strip()[:180]

    # V1.0.1.14: identidade visual sincronizada pelo DSYSTEM STUDIO.
    # Aceita somente imagens comuns em data URL, com limite para não inflar
    # excessivamente o payload/banco da CORE.
    if "logo_data_url" in cleaned:
        logo = str(cleaned.get("logo_data_url") or "").strip()
        if not logo:
            cleaned["logo_data_url"] = ""
        else:
            match = re.fullmatch(r"data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=]+)", logo, re.IGNORECASE)
            if not match or len(logo) > 2_200_000:
                cleaned.pop("logo_data_url", None)
            else:
                try:
                    raw = base64.b64decode(match.group(2), validate=True)
                    if len(raw) > 1_600_000:
                        cleaned.pop("logo_data_url", None)
                except (ValueError, binascii.Error):
                    cleaned.pop("logo_data_url", None)
    return cleaned


def _normalize_work_days(raw: Any) -> str:
    values: list[int] = []
    if isinstance(raw, (list, tuple, set)):
        parts = raw
    else:
        parts = str(raw or "").replace(";", ",").split(",")
    for part in parts:
        try:
            value = int(str(part).strip())
        except Exception:
            continue
        if 1 <= value <= 7 and value not in values:
            values.append(value)
    values.sort()
    return ",".join(str(v) for v in values) or "1,2,3,4,5"


def _work_days(cfg: dict[str, Any]) -> set[int]:
    return {int(x) for x in _normalize_work_days(cfg.get("funcionamento_dias")).split(",") if x}


def _work_days_label(cfg: dict[str, Any]) -> str:
    labels = {1: "Seg", 2: "Ter", 3: "Qua", 4: "Qui", 5: "Sex", 6: "Sáb", 7: "Dom"}
    return ", ".join(labels[d] for d in range(1, 8) if d in _work_days(cfg))


def _is_work_day(day_iso: str, cfg: dict[str, Any]) -> bool:
    try:
        d = datetime.strptime(day_iso, "%Y-%m-%d").date()
    except Exception:
        return False
    return (d.weekday() + 1) in _work_days(cfg)


def _normalize_fixed_times(raw: Any) -> list[str]:
    if isinstance(raw, (list, tuple, set)):
        parts = list(raw)
    else:
        parts = str(raw or "").replace(";", ",").replace("\n", ",").split(",")
    result: list[str] = []
    for part in parts:
        try:
            value = datetime.strptime(str(part).strip(), "%H:%M").strftime("%H:%M")
        except Exception:
            continue
        if value not in result:
            result.append(value)
    return sorted(result)


def _normalize_booking_months(raw: Any) -> str:
    if isinstance(raw, (list, tuple, set)):
        parts = list(raw)
    else:
        parts = str(raw or "").replace(";", ",").replace("\n", ",").split(",")
    values: list[int] = []
    for part in parts:
        try:
            value = int(str(part).strip())
        except Exception:
            continue
        if 1 <= value <= 12 and value not in values:
            values.append(value)
    values.sort()
    return ",".join(str(v) for v in values)


def _allowed_booking_months(cfg: dict[str, Any]) -> set[int]:
    mode = str(cfg.get("agendamento_online_meses_modo") or "todos").strip().lower()
    if mode == "todos":
        return set(range(1, 13))
    raw = _normalize_booking_months(cfg.get("agendamento_online_meses"))
    values = {int(x) for x in raw.split(",") if x}
    if not values:
        return set(range(1, 13))
    if mode == "um":
        return {min(values)}
    return values


def _calendar_month_bases(cfg: dict[str, Any], horizon_months: int = 12) -> list[date]:
    ref = date.today()
    allowed = _allowed_booking_months(cfg)
    result: list[date] = []
    for offset in range(max(1, horizon_months)):
        base = date(ref.year + ((ref.month - 1 + offset) // 12), ((ref.month - 1 + offset) % 12) + 1, 1)
        if base.month in allowed:
            result.append(base)
    return result


def _parse_iso_dt(value: Any) -> datetime | None:
    text = str(value or "").strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _day_appointments(db: Session, company_id: int, day_iso: str) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(
            Appointment.company_id == company_id,
            Appointment.is_deleted == False,  # noqa: E712
            Appointment.start_at.like(f"{day_iso}%"),
        )
        .all()
    )


def _day_count(db: Session, company_id: int, day_iso: str) -> int:
    return len(_day_appointments(db, company_id, day_iso))


def _day_full(db: Session, company_id: int, day_iso: str, cfg: dict[str, Any]) -> bool:
    try:
        limit = int(cfg.get("max_agendamentos_dia") or 0)
    except Exception:
        limit = 0
    return limit > 0 and _day_count(db, company_id, day_iso) >= limit


def _service(db: Session, company_id: int, external_id: str) -> ServiceCatalog:
    item = (
        db.query(ServiceCatalog)
        .filter(
            ServiceCatalog.company_id == company_id,
            ServiceCatalog.external_id == external_id,
            ServiceCatalog.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return item


def _professional(db: Session, company_id: int, external_id: str | None) -> Professional | None:
    if not external_id:
        return None
    item = (
        db.query(Professional)
        .filter(
            Professional.company_id == company_id,
            Professional.external_id == external_id,
            Professional.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return item


def _slot_conflicts(db: Session, company_id: int, start: datetime, end: datetime) -> bool:
    for appt in _day_appointments(db, company_id, start.date().isoformat()):
        status_txt = str(appt.status or "").strip().lower()
        if status_txt in {"cancelado", "cancelled", "excluido"}:
            continue
        current_start = _parse_iso_dt(appt.start_at)
        current_end = _parse_iso_dt(appt.end_at)
        if current_start is None:
            continue
        current_end = current_end or (current_start + timedelta(minutes=60))
        if start < current_end and end > current_start:
            return True
    return False


def _available_slots(
    db: Session,
    company_id: int,
    day_iso: str,
    service: ServiceCatalog,
    cfg: dict[str, Any],
) -> list[str]:
    try:
        selected_day = datetime.strptime(day_iso, "%Y-%m-%d").date()
    except Exception:
        return []
    if (
        selected_day < date.today()
        or selected_day.month not in _allowed_booking_months(cfg)
        or not _is_work_day(day_iso, cfg)
        or _day_full(db, company_id, day_iso, cfg)
    ):
        return []

    duration = int(service.duration_minutes or 60)
    pause = max(0, int(cfg.get("tempo_pausa_min") or 0))
    start_label = str(cfg.get("horario_inicio") or "08:00")
    end_label = str(cfg.get("horario_fim") or "18:00")
    try:
        day_start = datetime.strptime(f"{day_iso} {start_label}", "%Y-%m-%d %H:%M")
        day_end = datetime.strptime(f"{day_iso} {end_label}", "%Y-%m-%d %H:%M")
    except Exception:
        return []

    mode = str(cfg.get("agendamento_online_modo") or "flexivel").lower()
    if mode == "fixo":
        base_times = _normalize_fixed_times(cfg.get("agendamento_online_horarios_fixos"))
    else:
        interval = max(5, int(cfg.get("intervalo_min") or 15))
        cursor = day_start
        base_times: list[str] = []
        while cursor < day_end:
            base_times.append(cursor.strftime("%H:%M"))
            cursor += timedelta(minutes=interval)

    slots: list[str] = []
    now = datetime.now()
    for hour in base_times:
        try:
            start = datetime.strptime(f"{day_iso} {hour}", "%Y-%m-%d %H:%M")
        except Exception:
            continue
        end = start + timedelta(minutes=duration + pause)
        if start < day_start or end > day_end:
            continue
        if start <= now:
            continue
        if not _slot_conflicts(db, company_id, start, end):
            slots.append(hour)
    return slots


def _calendar_data(db: Session, company_id: int, cfg: dict[str, Any], months: int = 12) -> list[dict[str, Any]]:
    today = date.today()
    cal = calendar.Calendar(firstweekday=6)
    result: list[dict[str, Any]] = []
    for base in _calendar_month_bases(cfg, horizon_months=months):
        year, month = base.year, base.month
        counts: dict[str, int] = {}
        rows = (
            db.query(Appointment)
            .filter(
                Appointment.company_id == company_id,
                Appointment.is_deleted == False,  # noqa: E712
                Appointment.start_at.like(f"{year:04d}-{month:02d}%"),
            )
            .all()
        )
        for item in rows:
            dt = _parse_iso_dt(item.start_at)
            if not dt:
                continue
            if str(item.status or "").strip().lower() in {"cancelado", "cancelled", "excluido"}:
                continue
            key = dt.date().isoformat()
            counts[key] = counts.get(key, 0) + 1
        try:
            limit = int(cfg.get("max_agendamentos_dia") or 20)
        except Exception:
            limit = 20
        weeks: list[list[dict[str, Any] | None]] = []
        for week in cal.monthdatescalendar(year, month):
            row: list[dict[str, Any] | None] = []
            for d in week:
                if d.month != month:
                    row.append(None)
                    continue
                iso = d.isoformat()
                count = counts.get(iso, 0)
                if d < today:
                    state = "past"
                elif not _is_work_day(iso, cfg):
                    state = "off"
                elif limit > 0 and count >= limit:
                    state = "full"
                elif count:
                    state = "busy"
                else:
                    state = "free"
                row.append({"day": d.day, "date": iso, "count": count, "status": state, "is_today": d == today})
            weeks.append(row)
        result.append({"label": f"{PT_MONTHS[month - 1]} {year}", "year": year, "month": month, "weeks": weeks})
    return result


def _digits(value: Any) -> str:
    return re.sub(r"\D+", "", str(value or ""))


def _mask_phone(value: Any) -> str:
    digits = _digits(value)
    if len(digits) >= 4:
        return f"••••-{digits[-4:]}"
    return "WhatsApp cadastrado" if digits else ""


def _next_str_code(db: Session, company_id: int) -> str:
    rows = (
        db.query(Customer.external_id)
        .filter(Customer.company_id == company_id, Customer.external_id.like("STR%"))
        .all()
    )
    used = set()
    for (external_id,) in rows:
        match = re.fullmatch(r"STR(\d{4})", str(external_id or "").strip().upper())
        if match:
            used.add(int(match.group(1)))
    for number in range(10000):
        if number not in used:
            return f"STR{number:04d}"
    raise HTTPException(status_code=409, detail="Limite de códigos STR atingido para esta empresa")


def _public_base(request: Request) -> str:
    configured = str(get_settings().public_booking_base_url or "").strip().rstrip("/")
    if configured:
        return configured
    return str(request.base_url).rstrip("/") + "/agendamento-publico"


def _public_url(request: Request, slug: str) -> str:
    return f"{_public_base(request)}/{slug}"


def _direct_url(request: Request, slug: str) -> str:
    return str(request.base_url).rstrip("/") + f"/agendamento-publico/{slug}"


def _save_config(db: Session, company_id: int, payload: dict[str, Any], source: str) -> PublicBookingConfig:
    existing = _config_record(db, company_id)
    settings_payload = payload.get("settings") if isinstance(payload.get("settings"), dict) else payload
    cleaned = _normalize_settings(settings_payload)
    replace = bool(payload.get("replace", False))
    enabled = payload.get("enabled")

    if not existing:
        existing = PublicBookingConfig(
            company_id=company_id,
            is_enabled=bool(True if enabled is None else enabled),
            settings_json={**DEFAULT_BOOKING_SETTINGS, **cleaned},
            source=source,
        )
        db.add(existing)
    else:
        current = {} if replace else _settings(existing)
        current.update(cleaned)
        existing.settings_json = current
        if enabled is not None:
            existing.is_enabled = bool(enabled)
        existing.source = source
    db.commit()
    db.refresh(existing)
    return existing


def _config_response(request: Request, company: Company, record: PublicBookingConfig | None) -> dict[str, Any]:
    cfg = _settings(record)
    return {
        "ok": True,
        "company": {"id": company.id, "name": company.name, "slug": company.slug},
        "enabled": bool(record.is_enabled) if record else False,
        "source": record.source if record else None,
        "settings": cfg,
        "public_url": _public_url(request, company.slug),
        "direct_url": _direct_url(request, company.slug),
        "updated_at": record.updated_at.isoformat() if record and hasattr(record.updated_at, "isoformat") else (str(record.updated_at) if record else None),
    }


def _single_use_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _single_use_url(request: Request, slug: str, token: str) -> str:
    return f"{_public_base(request)}/{slug}/t/{token}"


def _single_use_link_by_token(db: Session, company_id: int, token: str) -> SingleUseBookingLink | None:
    token_hash = _single_use_token_hash(token)
    return (
        db.query(SingleUseBookingLink)
        .filter(
            SingleUseBookingLink.company_id == company_id,
            SingleUseBookingLink.token_hash == token_hash,
            SingleUseBookingLink.is_active == True,  # noqa: E712
        )
        .first()
    )


def _single_use_client(db: Session, company_id: int, link: SingleUseBookingLink) -> Customer | None:
    return (
        db.query(Customer)
        .filter(
            Customer.company_id == company_id,
            Customer.external_id == link.customer_external_id,
            Customer.is_deleted == False,  # noqa: E712
        )
        .first()
    )


@router.get("/api/booking/config")
def booking_config_me(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return _config_response(request, company, _config_record(db, company.id))


@router.put("/api/booking/config")
def booking_config_update(payload: dict[str, Any], request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    record = _save_config(db, company.id, payload, str(payload.get("source") or "ds_go")[:80])
    return _config_response(request, company, record)


@router.post("/api/booking/temporary-links")
def create_temporary_booking_link(payload: dict[str, Any], request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    record = _config_record(db, company.id)
    if not record or not record.is_enabled:
        raise HTTPException(status_code=409, detail="A Agenda Online está desativada. Ative antes de gerar um link temporário.")

    client_ref = str(payload.get("client_ref") or payload.get("customer_external_id") or "").strip()
    if not client_ref:
        raise HTTPException(status_code=400, detail="Cliente não informado")
    customer = (
        db.query(Customer)
        .filter(
            Customer.company_id == company.id,
            Customer.external_id == client_ref,
            Customer.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente não encontrado na CORE")

    db.query(SingleUseBookingLink).filter(
        SingleUseBookingLink.company_id == company.id,
        SingleUseBookingLink.customer_external_id == customer.external_id,
        SingleUseBookingLink.is_active == True,  # noqa: E712
        SingleUseBookingLink.used_at.is_(None),
    ).update({"is_active": False}, synchronize_session=False)

    token = secrets.token_urlsafe(32)
    link = SingleUseBookingLink(
        company_id=company.id,
        customer_external_id=customer.external_id,
        token_hash=_single_use_token_hash(token),
        created_by_user_id=current_user.id,
        is_active=True,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {
        "ok": True,
        "single_use": True,
        "client_ref": customer.external_id,
        "client_name": customer.name,
        "url": _single_use_url(request, company.slug, token),
    }


@router.post("/api/studio/public-booking/config")
def studio_booking_config_update(payload: dict[str, Any], request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    existing = _config_record(db, company.id)
    safe_payload = _studio_payload_respecting_ds_go_authority(payload, has_existing=existing is not None)
    record = _save_config(db, company.id, safe_payload, str(safe_payload.get("source") or "desktop_sync")[:80])
    return _config_response(request, company, record)


@router.get("/api/public/booking/{slug}/config")
def public_booking_config(slug: str, request: Request, db: Session = Depends(get_db)):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    if not record or not record.is_enabled:
        raise HTTPException(status_code=404, detail="Agenda Online indisponível")
    data = _config_response(request, company, record)
    data["services"] = [
        {"id": s.external_id, "name": s.name, "price": float(s.price or 0), "duration_minutes": int(s.duration_minutes or 60)}
        for s in db.query(ServiceCatalog).filter(ServiceCatalog.company_id == company.id, ServiceCatalog.is_deleted == False).order_by(ServiceCatalog.name).all()  # noqa: E712
    ]
    data["professionals"] = [
        {"id": p.external_id, "name": p.name}
        for p in db.query(Professional).filter(Professional.company_id == company.id, Professional.is_deleted == False).order_by(Professional.name).all()  # noqa: E712
    ]
    return data


@router.get("/api/public/booking/{slug}/clients/search")
def public_client_search(slug: str, q: str = Query(default="", min_length=2, max_length=80), db: Session = Depends(get_db)):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    if not record or not record.is_enabled:
        raise HTTPException(status_code=404, detail="Agenda Online indisponível")

    raw = q.strip()
    upper = raw.upper()
    digits = _digits(raw)
    query = db.query(Customer).filter(Customer.company_id == company.id, Customer.is_deleted == False)  # noqa: E712

    exact_str = None
    if re.fullmatch(r"STR\d{1,4}", upper):
        exact_str = "STR" + upper[3:].zfill(4)
    elif digits and len(digits) <= 4 and not any(c.isalpha() for c in raw):
        exact_str = f"STR{int(digits):04d}"

    candidates: list[Customer] = []
    if exact_str:
        candidates.extend(query.filter(Customer.external_id == exact_str).limit(4).all())
    if digits and len(digits) >= 8:
        # Telefones são heterogêneos no legado; filtramos uma amostra e comparamos somente dígitos.
        for item in query.order_by(Customer.updated_at.desc()).limit(500).all():
            phone_digits = _digits(item.phone)
            if phone_digits and (phone_digits.endswith(digits) or digits.endswith(phone_digits)):
                candidates.append(item)
                if len(candidates) >= 8:
                    break
    if len(raw) >= 3:
        candidates.extend(query.filter(Customer.name.ilike(f"%{raw}%")).order_by(Customer.name).limit(8).all())

    unique: dict[int, Customer] = {}
    for item in candidates:
        unique[item.id] = item
    items = []
    for item in list(unique.values())[:8]:
        sigla = item.external_id if re.fullmatch(r"STR\d{4}", str(item.external_id or "").upper()) else ""
        items.append({
            "id": item.external_id,
            "client_ref": item.external_id,
            "external_id": item.external_id,
            "sigla": sigla,
            "nome": item.name,
            "whatsapp": _mask_phone(item.phone),
            "whatsapp_masked": _mask_phone(item.phone),
        })
    return {"items": items}


@router.get("/api/public/booking/{slug}/availability")
def public_availability(
    slug: str,
    data: str,
    servico_id: str,
    profissional_id: str | None = None,
    db: Session = Depends(get_db),
):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    if not record or not record.is_enabled:
        raise HTTPException(status_code=404, detail="Agenda Online indisponível")
    cfg = _settings(record)
    service = _service(db, company.id, servico_id)
    _professional(db, company.id, profissional_id)
    slots = _available_slots(db, company.id, data, service, cfg)
    return {
        "horarios": slots,
        "data": data,
        "disponivel": bool(slots),
        "lotado": _day_full(db, company.id, data, cfg),
        "funcionamento": _is_work_day(data, cfg),
    }


def _create_public_customer(db: Session, company: Company, name: str, phone: str) -> Customer:
    # Tenta alguns códigos em caso de corrida concorrente.
    for _ in range(5):
        code = _next_str_code(db, company.id)
        raw = {
            "source": "online_booking",
            "sigla": code,
            "codigo": code,
            "client_code": code,
            "customer_code": code,
            "studio_code": code,
        }
        customer = Customer(
            company_id=company.id,
            module_code="studio",
            external_id=code,
            sync_source="online_booking",
            name=name,
            phone=phone or None,
            email=None,
            document=None,
            notes="Cliente criado pela Agenda Online DSYSTEM",
            raw_payload=json.dumps(raw, ensure_ascii=False),
            is_deleted=False,
        )
        db.add(customer)
        try:
            db.flush()
            return customer
        except Exception:
            db.rollback()
    raise HTTPException(status_code=409, detail="Não foi possível gerar o código do cliente. Tente novamente.")


def _create_booking(
    *,
    db: Session,
    company: Company,
    record: PublicBookingConfig,
    existing_client_ref: str,
    client_name: str,
    phone: str,
    service_external_id: str,
    professional_external_id: str | None,
    day_iso: str,
    hour: str,
    notes: str,
) -> Appointment:
    cfg = _settings(record)
    service = _service(db, company.id, service_external_id)
    professional = _professional(db, company.id, professional_external_id)

    try:
        start = datetime.strptime(f"{day_iso} {hour}", "%Y-%m-%d %H:%M")
    except Exception:
        raise HTTPException(status_code=400, detail="Data ou horário inválido")

    available = _available_slots(db, company.id, day_iso, service, cfg)
    if hour not in available:
        raise HTTPException(status_code=409, detail="Esse horário não está mais disponível. Escolha outro horário.")

    customer: Customer | None = None
    if existing_client_ref:
        customer = (
            db.query(Customer)
            .filter(
                Customer.company_id == company.id,
                Customer.external_id == existing_client_ref,
                Customer.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente não encontrado. Faça a busca novamente.")
        client_name = customer.name
        phone = customer.phone or phone
    else:
        client_name = client_name.strip()
        if not client_name:
            raise HTTPException(status_code=400, detail="Informe o nome do cliente")
        customer = _create_public_customer(db, company, client_name, phone)

    pause = max(0, int(cfg.get("tempo_pausa_min") or 0))
    end = start + timedelta(minutes=int(service.duration_minutes or 60) + pause)
    external_id = f"ONLINE-{uuid.uuid4().hex.upper()}"
    raw = {
        "source": "online_booking",
        "sync_source": "online_booking",
        "origin": "online_booking",
        "client_uid": customer.external_id,
        "phone": phone,
        "service_external_id": service.external_id,
        "professional_external_id": professional.external_id if professional else None,
        "pending_desktop_pull": True,
        "desktop_imported": False,
    }
    appointment = Appointment(
        company_id=company.id,
        module_code="studio",
        external_id=external_id,
        sync_source="online_booking",
        customer_external_id=customer.external_id,
        customer_name=client_name,
        professional_name=professional.name if professional else "",
        service_name=service.name,
        start_at=start.strftime("%Y-%m-%dT%H:%M:%S"),
        end_at=end.strftime("%Y-%m-%dT%H:%M:%S"),
        status="Agendado",
        notes=notes.strip() or None,
        raw_payload=json.dumps(raw, ensure_ascii=False),
        is_deleted=False,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.post("/api/public/booking/{slug}/appointments")
def public_create_appointment(slug: str, payload: dict[str, Any], db: Session = Depends(get_db)):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    if not record or not record.is_enabled:
        raise HTTPException(status_code=404, detail="Agenda Online indisponível")
    appointment = _create_booking(
        db=db,
        company=company,
        record=record,
        existing_client_ref=str(payload.get("client_ref") or payload.get("cliente_id") or "").strip(),
        client_name=str(payload.get("client_name") or payload.get("cliente_nome") or payload.get("name") or "").strip(),
        phone=str(payload.get("phone") or payload.get("whatsapp") or "").strip(),
        service_external_id=str(payload.get("service_id") or payload.get("servico_id") or "").strip(),
        professional_external_id=str(payload.get("professional_id") or payload.get("profissional_id") or "").strip() or None,
        day_iso=str(payload.get("date") or payload.get("data") or "").strip(),
        hour=str(payload.get("time") or payload.get("hora") or "").strip(),
        notes=str(payload.get("notes") or payload.get("observacoes") or "").strip(),
    )
    return {
        "ok": True,
        "appointment": {
            "id": appointment.id,
            "external_id": appointment.external_id,
            "source": appointment.sync_source,
            "customer_external_id": appointment.customer_external_id,
            "customer_name": appointment.customer_name,
            "service_name": appointment.service_name,
            "professional_name": appointment.professional_name,
            "start_at": appointment.start_at,
            "end_at": appointment.end_at,
            "status": appointment.status,
        },
    }


@router.api_route("/agendamento-publico/{slug}/t/{token}", methods=["GET", "POST"], response_class=HTMLResponse)
def public_booking_single_use_page(
    request: Request,
    slug: str,
    token: str,
    db: Session = Depends(get_db),
    servico_id: str = Form(default=""),
    profissional_id: str = Form(default=""),
    data: str = Form(default=""),
    hora: str = Form(default=""),
    observacoes: str = Form(default=""),
):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    cfg = _settings(record)
    if not record or not record.is_enabled:
        return templates.TemplateResponse(
            request=request,
            name="agendamento_publico_fechada.html",
            context={"cfg": cfg, "company_name": company.name or company.slug},
            status_code=200,
        )

    link = _single_use_link_by_token(db, company.id, token)
    if not link or link.used_at is not None:
        return templates.TemplateResponse(
            request=request,
            name="agendamento_publico_link_encerrado.html",
            context={"cfg": cfg, "company_name": company.name or company.slug},
            status_code=200,
        )
    customer = _single_use_client(db, company.id, link)
    if not customer:
        link.is_active = False
        db.commit()
        return templates.TemplateResponse(
            request=request,
            name="agendamento_publico_link_encerrado.html",
            context={"cfg": cfg, "company_name": company.name or company.slug},
            status_code=200,
        )

    error_message = None
    if request.method == "POST":
        reserved_at = datetime.now()
        updated = (
            db.query(SingleUseBookingLink)
            .filter(
                SingleUseBookingLink.id == link.id,
                SingleUseBookingLink.is_active == True,  # noqa: E712
                SingleUseBookingLink.used_at.is_(None),
            )
            .update({"used_at": reserved_at}, synchronize_session=False)
        )
        db.commit()
        if updated != 1:
            return templates.TemplateResponse(
                request=request,
                name="agendamento_publico_link_encerrado.html",
                context={"cfg": cfg, "company_name": company.name or company.slug},
                status_code=200,
            )
        try:
            appointment = _create_booking(
                db=db,
                company=company,
                record=record,
                existing_client_ref=customer.external_id,
                client_name=customer.name,
                phone=customer.phone or "",
                service_external_id=servico_id.strip(),
                professional_external_id=profissional_id.strip() or None,
                day_iso=data.strip(),
                hour=hora.strip(),
                notes=observacoes.strip(),
            )
            link = db.query(SingleUseBookingLink).filter(SingleUseBookingLink.id == link.id).first()
            if link:
                link.appointment_external_id = appointment.external_id
                link.is_active = False
                db.commit()
            return templates.TemplateResponse(
                request=request,
                name="agendamento_publico_sucesso.html",
                context={
                    "appointment_code": appointment.external_id,
                    "new_booking_url": None,
                    "single_use_completed": True,
                    "theme": cfg.get("tema") or "claro",
                },
            )
        except HTTPException as exc:
            db.rollback()
            link = db.query(SingleUseBookingLink).filter(SingleUseBookingLink.id == link.id).first()
            if link:
                link.used_at = None
                link.is_active = True
                db.commit()
            error_message = str(exc.detail)
        except Exception:
            db.rollback()
            link = db.query(SingleUseBookingLink).filter(SingleUseBookingLink.id == link.id).first()
            if link:
                link.used_at = None
                link.is_active = True
                db.commit()
            error_message = "Não foi possível concluir o agendamento agora. Tente novamente."

    services = [
        {"id": s.external_id, "nome": s.name, "preco": float(s.price or 0), "duracao_min": int(s.duration_minutes or 60)}
        for s in db.query(ServiceCatalog).filter(ServiceCatalog.company_id == company.id, ServiceCatalog.is_deleted == False).order_by(ServiceCatalog.name).all()  # noqa: E712
    ]
    professionals = [
        {"id": p.external_id, "nome": p.name}
        for p in db.query(Professional).filter(Professional.company_id == company.id, Professional.is_deleted == False).order_by(Professional.name).all()  # noqa: E712
    ]
    return templates.TemplateResponse(
        request=request,
        name="agendamento_publico.html",
        context={
            "title": "Agendamento Online",
            "servicos": services,
            "profissionais": professionals,
            "cfg": cfg,
            "public_calendar": json.dumps(_calendar_data(db, company.id, cfg), ensure_ascii=False),
            "dias_funcionamento_label": _work_days_label(cfg),
            "client_search_url": f"/api/public/booking/{company.slug}/clients/search",
            "availability_url": f"/api/public/booking/{company.slug}/availability",
            "error_message": error_message,
            "temporary_mode": True,
            "temporary_client": {
                "external_id": customer.external_id,
                "name": customer.name,
                "phone": customer.phone or "",
            },
        },
    )


@router.api_route("/agendamento-publico/{slug}", methods=["GET", "POST"], response_class=HTMLResponse)
def public_booking_page(
    request: Request,
    slug: str,
    db: Session = Depends(get_db),
    ja_cliente: str = Form(default="0"),
    cliente_id: str = Form(default=""),
    cliente_nome: str = Form(default=""),
    nome: str = Form(default=""),
    sobrenome: str = Form(default=""),
    whatsapp: str = Form(default=""),
    servico_id: str = Form(default=""),
    profissional_id: str = Form(default=""),
    data: str = Form(default=""),
    hora: str = Form(default=""),
    observacoes: str = Form(default=""),
):
    company = _company_by_slug(db, slug)
    record = _config_record(db, company.id)
    cfg = _settings(record)
    if not record or not record.is_enabled:
        return templates.TemplateResponse(
            request=request,
            name="agendamento_publico_fechada.html",
            context={
                "cfg": cfg,
                "company_name": company.name or company.slug,
            },
            status_code=200,
        )
    error_message = None

    if request.method == "POST":
        try:
            full_name = cliente_nome.strip() or " ".join(p for p in (nome.strip(), sobrenome.strip()) if p).strip()
            appointment = _create_booking(
                db=db,
                company=company,
                record=record,
                existing_client_ref=cliente_id.strip() if ja_cliente == "1" else "",
                client_name=full_name,
                phone=whatsapp.strip(),
                service_external_id=servico_id.strip(),
                professional_external_id=profissional_id.strip() or None,
                day_iso=data.strip(),
                hour=hora.strip(),
                notes=observacoes.strip(),
            )
            return templates.TemplateResponse(
                request=request,
                name="agendamento_publico_sucesso.html",
                context={
                    "appointment_code": appointment.external_id,
                    "new_booking_url": _direct_url(request, company.slug),
                    "theme": cfg.get("tema") or "claro",
                },
            )
        except HTTPException as exc:
            db.rollback()
            error_message = str(exc.detail)
        except Exception:
            db.rollback()
            error_message = "Não foi possível concluir o agendamento agora. Tente novamente."

    services = [
        {"id": s.external_id, "nome": s.name, "preco": float(s.price or 0), "duracao_min": int(s.duration_minutes or 60)}
        for s in db.query(ServiceCatalog).filter(ServiceCatalog.company_id == company.id, ServiceCatalog.is_deleted == False).order_by(ServiceCatalog.name).all()  # noqa: E712
    ]
    professionals = [
        {"id": p.external_id, "nome": p.name}
        for p in db.query(Professional).filter(Professional.company_id == company.id, Professional.is_deleted == False).order_by(Professional.name).all()  # noqa: E712
    ]
    return templates.TemplateResponse(
        request=request,
        name="agendamento_publico.html",
        context={
            "title": "Agendamento Online",
            "servicos": services,
            "profissionais": professionals,
            "cfg": cfg,
            "public_calendar": json.dumps(_calendar_data(db, company.id, cfg), ensure_ascii=False),
            "dias_funcionamento_label": _work_days_label(cfg),
            "client_search_url": f"/api/public/booking/{company.slug}/clients/search",
            "availability_url": f"/api/public/booking/{company.slug}/availability",
            "error_message": error_message,
            "temporary_mode": False,
            "temporary_client": None,
        },
    )


@router.get("/agendamento-publico", response_class=HTMLResponse)
def public_booking_root(request: Request, empresa: str | None = None, db: Session = Depends(get_db)):
    if empresa:
        company = _company_by_slug(db, empresa)
        return RedirectResponse(url=_direct_url(request, company.slug), status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    enabled = (
        db.query(PublicBookingConfig, Company)
        .join(Company, Company.id == PublicBookingConfig.company_id)
        .filter(PublicBookingConfig.is_enabled == True, Company.is_active == True)  # noqa: E712
        .limit(2)
        .all()
    )
    if len(enabled) == 1:
        return RedirectResponse(url=_direct_url(request, enabled[0][1].slug), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return HTMLResponse(
        "<html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='font-family:sans-serif;padding:32px'><h2>Agenda Online DSYSTEM</h2><p>Use o link de agendamento fornecido pela empresa.</p></body></html>",
        status_code=200,
    )
