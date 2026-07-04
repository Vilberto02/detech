import os
import tempfile
from pathlib import Path
from typing import List

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from ..config.config_manager import ConfigManager
from ..core.rule_engine import RuleEngine
from ..core.models import Report

router = APIRouter(tags=["Análisis"])


@router.post("/analyze")
async def analyze(
    files: List[UploadFile] = File(...),
    min_severity: str = Form("info"),
):
    """
    Recibe uno o más archivos .py, los analiza y retorna el reporte en JSON.

    Args:
        files: Lista de archivos .py subidos.

    Returns:
        JSON con el reporte de anomalías.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos.")

    config = ConfigManager()
    engine = RuleEngine(config)
    report = Report()

    with tempfile.TemporaryDirectory() as tmpdir:
        for upload in files:
            filename = upload.filename or "archivo.py"
            tmp_path = Path(tmpdir) / filename
            content = await upload.read()
            tmp_path.write_bytes(content)

            try:
                file_result = engine.analyze_file(tmp_path)
                # Reemplazar ruta temporal con nombre original
                file_result.filepath = filename
                for anomaly in file_result.anomalies:
                    anomaly.file = filename
                report.files.append(file_result)
            except Exception as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"Error al analizar '{filename}': {str(exc)}",
                )

    if not report.files:
        raise HTTPException(
            status_code=400,
            detail="Ninguno de los archivos subidos es válido.",
        )

    _compute_statistics(report)

    return _serialize_report(report, min_severity=min_severity)


def _compute_statistics(report: Report):
    """Calcula estadísticas agregadas y detecta outliers (ej. por complejidad)."""
    if not report.files:
        return

    complexities = []
    lines = []
    for fr in report.files:
        if "cyclomatic_complexity" in fr.metrics:
            complexities.append(fr.metrics["cyclomatic_complexity"])
        if "loc" in fr.metrics:
            lines.append(fr.metrics["loc"]["total"])

    def calc_stats(values):
        if not values:
            return {"mean": 0, "max": 0}
        return {"mean": round(sum(values) / len(values), 2), "max": max(values)}

    report.statistics = {
        "complexity": calc_stats(complexities),
        "loc": calc_stats(lines)
    }


def _serialize_report(report: Report, min_severity: str = "info") -> dict:
    """Serializa el Report a un dict JSON-compatible, filtrando por severidad."""
    severity_levels = {"info": 0, "warning": 1, "critical": 2}
    min_level = severity_levels.get(min_severity.lower(), 0)
    return {
        "summary": {
            "total_files": len(report.files),
            "total_anomalies": report.total_anomalies,
            "critical": report.critical_count,
            "warning": report.warning_count,
            "info": report.info_count,
        },
        "files": [
            {
                "filepath": fr.filepath,
                "total_lines": fr.total_lines,
                "anomaly_count": sum(1 for a in fr.anomalies if severity_levels.get(a.severity, 0) >= min_level),
                "critical": fr.critical_count,
                "warning": fr.warning_count,
                "info": fr.info_count,
                "anomalies": [
                    {
                        "line": a.line,
                        "rule_id": a.rule_id,
                        "category": a.category,
                        "severity": a.severity,
                        "message": a.message,
                        "context": a.context,
                    }
                    for a in fr.anomalies
                    if severity_levels.get(a.severity, 0) >= min_level
                ],
            }
            for fr in report.files
        ],
        "statistics": report.statistics,
    }
