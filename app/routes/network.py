import socket
from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(prefix="/api/core", tags=["core-network"])


def _get_ipv4_addresses():
    addresses = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in addresses:
                addresses.append(ip)
    except Exception:
        pass
    # fallback: discover primary outbound interface without sending data
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127.") and ip not in addresses:
            addresses.append(ip)
    except Exception:
        pass
    return addresses


@router.get("/network-info")
def network_info():
    settings = get_settings()
    ips = _get_ipv4_addresses()
    port = 8000
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "mode": "SERVIDOR_LOCAL_REDE",
        "bind_host": "0.0.0.0",
        "port": port,
        "local_url": f"http://localhost:{port}",
        "local_docs": f"http://localhost:{port}/docs",
        "network_urls": [f"http://{ip}:{port}" for ip in ips],
        "network_docs": [f"http://{ip}:{port}/docs" for ip in ips],
        "go_configuration_tip": "No DS STUDIO GO em outro dispositivo, use http://IP-DO-SERVIDOR:8000, não use localhost.",
        "company_slug_default": settings.default_company_slug,
    }
