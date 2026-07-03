from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..config.config_manager import ConfigManager

router = APIRouter(tags=["Configuración"])


@router.get("/config")
async def get_config():
    """Retorna la configuración activa (valores por defecto)."""
    config = ConfigManager()
    return config.as_dict()
