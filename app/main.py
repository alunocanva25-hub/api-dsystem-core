from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routes import admin, audit, auth, business, companies, dashboard, modules, product_config, standards, status, sync, users, go_compat, go_complete, network

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API central inicial do ecossistema DSYSTEM.",
)

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
