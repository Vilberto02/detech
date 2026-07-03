"""
Generador de Reportes HTML.
Usa Jinja2 para generar el reporte en HTML que luego puede ser impreso como PDF desde el cliente.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _build_context(report_data: dict) -> dict:
    """Construye el contexto de datos para la plantilla Jinja2."""
    # Agrupar anomalías por categoría para el resumen
    categories: dict = {}
    for file in report_data.get("files", []):
        for a in file.get("anomalies", []):
            cat = a.get("category", "other")
            categories.setdefault(cat, []).append(a)

    category_labels = {
        "legibility": "Legibilidad",
        "complexity": "Complejidad",
        "dead_code":  "Código Muerto",
        "security":   "Seguridad",
        "style":      "Estilo",
        "custom":     "Personalizados",
        "system":     "Sistema",
    }

    return {
        "report":       report_data,
        "summary":      report_data.get("summary", {}),
        "files":        report_data.get("files", []),
        "categories":   categories,
        "cat_labels":   category_labels,
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


def generate_html_report(report_data: dict) -> str:
    """
    Genera el reporte en formato HTML usando la plantilla Jinja2.

    Args:
        report_data: Dict con la estructura retornada por /api/analyze.

    Returns:
        String con el HTML completo del reporte.
    """
    template = _env.get_template("report.html.j2")
    context = _build_context(report_data)
    return template.render(**context)



