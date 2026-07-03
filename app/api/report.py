from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from ..reports.generator import generate_html_report

router = APIRouter(tags=["Reportes"])


@router.post("/report")
async def generate_report(
    report_data: dict,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
):
    """
    Genera un reporte descargable a partir de los datos del análisis.

    Args:
        report_data: JSON retornado por /api/analyze.
        format: Formato de salida — 'html' (default) o 'pdf'.

    Returns:
        Archivo HTML o PDF para descarga.
    """
    if not report_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos de reporte.")

    # Generación de HTML
    try:
        html_content = generate_html_report(report_data)
        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=detech_report.html"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar HTML: {e}")
