from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.core.config import get_settings

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
def dashboard_home():
    settings = get_settings()
    html = f"""
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{settings.app_name} {settings.app_version}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin:0; font-family:Segoe UI,Arial,sans-serif; background:#070b18; color:#f5f7fb; }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:46px 22px; }}
    .hero {{ border:1px solid rgba(255,255,255,.12); background:linear-gradient(135deg,#101a34,#0b1020 55%,#141027); border-radius:26px; padding:34px; box-shadow:0 24px 70px rgba(0,0,0,.35); }}
    .badge {{ display:inline-block; padding:8px 12px; border-radius:999px; background:rgba(87,115,255,.18); color:#bfc9ff; font-weight:700; font-size:13px; letter-spacing:.3px; }}
    h1 {{ margin:18px 0 8px; font-size:42px; line-height:1.1; }}
    p {{ color:#b9c2d6; font-size:17px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:14px; margin-top:22px; }}
    .card {{ border:1px solid rgba(255,255,255,.1); background:rgba(255,255,255,.045); border-radius:18px; padding:18px; }}
    .card b {{ display:block; font-size:15px; color:#fff; margin-bottom:7px; }}
    a {{ color:#9fb0ff; text-decoration:none; font-weight:700; }}
    code {{ background:rgba(255,255,255,.08); border-radius:8px; padding:3px 7px; }}
    .footer {{ margin-top:20px; color:#7d879d; font-size:13px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <span class="badge">ONLINE • CORE {settings.app_version} • PADRÃO OFICIAL</span>
      <h1>DSYSTEM SERVER CORE</h1>
      <p>Base central para empresas, usuários, permissões, módulos, auditoria e sincronização das ramificações DSYSTEM.</p>
      <div class="grid">
        <div class="card"><b>Status</b><a href="/api/status">/api/status</a><br><small>Saúde básica da API.</small></div>
        <div class="card"><b>Visão Core</b><a href="/api/core/overview">/api/core/overview</a><br><small>Resumo do banco e módulos.</small></div>
        <div class="card"><b>Padrão Oficial</b><a href="/api/core/official-standards">/api/core/official-standards</a><br><small>Nomes, slugs e module_codes oficiais.</small></div>
        <div class="card"><b>Documentação API</b><a href="/docs">/docs</a><br><small>Swagger para testar as rotas.</small></div>
        <div class="card"><b>Servidor Local/Rede</b><a href="/api/core/network-info">/api/core/network-info</a><br><small>Mostra URLs para configurar STUDIO e GO.</small></div>
        <div class="card"><b>Login inicial</b><code>master</code> / <code>master123</code><br><small>Empresa: <code>dsystem-master</code></small></div>
      </div>
      <p class="footer">Marco atual: modo Servidor Local em Rede para o desktop servidor DSYSTEM CORE. Use o IP da máquina no DS STUDIO GO e no DSYSTEM STUDIO.</p>
    </section>
  </div>
</body>
</html>
"""
    return HTMLResponse(html)
