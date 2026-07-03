"""
DETECH — Punto de entrada FastAPI.
"""

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
from pathlib import Path

from .api import analyze, report, config as config_router

app = FastAPI(
    title="DETECH",
    description="Herramienta de detección de anomalías en código fuente Python.",
    version="0.1.0",
)

# Montar el frontend estático
_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")

# Registrar routers de la API
app.include_router(analyze.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(config_router.router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root():
    """Sirve el frontend."""
    index_path = _FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "DETECH API activa. Documentación en /docs"}


@app.get("/health", tags=["Sistema"])
async def health():
    """Endpoint de salud del servicio."""
    return {"status": "ok", "version": "0.1.0"}
