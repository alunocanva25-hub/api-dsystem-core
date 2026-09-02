from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core.config import get_settings
from app.routes import admin, audit, auth, business, companies, dashboard, modules, product_config, standards, status, sync, users, go_compat, go_complete, network, public_booking

settings = get_settings()
APP_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API central inicial do ecossistema DSYSTEM.",
)


app.mount("/public-static", StaticFiles(directory=str(APP_DIR / "static")), name="public_static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(status.router)
app.include_router(standards.router)
app.include_router(product_config.router)
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(users.router)
app.include_router(modules.router)
app.include_router(sync.router)
app.include_router(business.router)
app.include_router(audit.router)
app.include_router(go_compat.router)
app.include_router(go_complete.router)
app.include_router(network.router)
app.include_router(public_booking.router)


# V1.0.1.12 — autoridade da Agenda Online no DS Go + marcador de deploy.
# Ele permite confirmar que o código publicado realmente contém a Agenda Online,
# mesmo quando APP_VERSION no ambiente foi preenchido manualmente.
BUILD_ID = "DSYSTEM_SERVER_CORE_V1.0.1.12_AUTORIDADE_AGENDA_DS_GO"
EXPECTED_PUBLIC_BOOKING_ROUTE = "/agendamento-publico/{slug}"


def _registered_booking_routes() -> list[str]:
    return sorted(
        {
            str(getattr(route, "path", ""))
            for route in app.routes
            if "booking" in str(getattr(route, "path", "")).lower()
            or "agendamento-publico" in str(getattr(route, "path", "")).lower()
        }
    )


@app.get("/api/core/deploy-info", tags=["core-deploy"])
def deploy_info():
    routes = _registered_booking_routes()
    return {
        "ok": True,
        "build_id": BUILD_ID,
        "configured_app_version": settings.app_version,
        "public_booking_router_loaded": EXPECTED_PUBLIC_BOOKING_ROUTE in routes,
        "expected_public_booking_route": EXPECTED_PUBLIC_BOOKING_ROUTE,
        "booking_routes": routes,
    }


# Linha visível nos logs do Render a cada boot deste build.
_booking_routes_at_boot = _registered_booking_routes()
print(
    f"[DSYSTEM DEPLOY] {BUILD_ID} | "
    f"public_booking_router_loaded={EXPECTED_PUBLIC_BOOKING_ROUTE in _booking_routes_at_boot} | "
    f"routes={_booking_routes_at_boot}"
)
