from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("company_id", "module_code", "external_id", name="uq_customer_sync_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sync_source: Mapped[str] = mapped_column(String(80), default="desktop_sync", nullable=False)

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    document: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_created_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_updated_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("company_id", "module_code", "external_id", name="uq_appointment_sync_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sync_source: Mapped[str] = mapped_column(String(80), default="desktop_sync", nullable=False)

    customer_external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    professional_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    start_at: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    end_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_created_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_updated_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TransactionRecord(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("company_id", "module_code", "external_id", name="uq_transaction_sync_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sync_source: Mapped[str] = mapped_column(String(80), default="desktop_sync", nullable=False)

    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(220), nullable=False)
    amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    transaction_date: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    customer_external_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_created_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_updated_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Professional(Base):
    __tablename__ = "professionals"
    __table_args__ = (
        UniqueConstraint("company_id", "module_code", "external_id", name="uq_professional_sync_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sync_source: Mapped[str] = mapped_column(String(80), default="desktop_sync", nullable=False)

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_created_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_updated_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ServiceCatalog(Base):
    __tablename__ = "services"
    __table_args__ = (
        UniqueConstraint("company_id", "module_code", "external_id", name="uq_service_sync_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sync_source: Mapped[str] = mapped_column(String(80), default="desktop_sync", nullable=False)

    name: Mapped[str] = mapped_column(String(180), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_created_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_updated_at: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
