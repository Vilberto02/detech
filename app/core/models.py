"""
Modelos de datos centrales.
Define las estructuras de datos utilizadas en todo el sistema.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Anomaly:
    """Representa una anomalía detectada en el código fuente."""
    file: str          # Ruta relativa del archivo analizado
    line: int          # Número de línea donde se detectó la anomalía
    rule_id: str       # Identificador único de la regla que la detectó
    category: str      # Categoría: legibility | complexity | dead_code | security | style
    severity: str      # Nivel: critical | warning | info
    message: str       # Descripción legible del problema
    context: str = ""  # Fragmento de código relevante (línea o bloque)


@dataclass
class FileResult:
    """Resultado del análisis de un archivo individual."""
    filepath: str
    total_lines: int
    anomalies: List[Anomaly] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)  # Métricas extraídas del archivo para análisis estadístico

    @property
    def critical_count(self) -> int:
        return sum(1 for a in self.anomalies if a.severity == "critical")

    @property
    def warning_count(self) -> int:
        return sum(1 for a in self.anomalies if a.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for a in self.anomalies if a.severity == "info")

    @property
    def total_anomalies(self) -> int:
        return len(self.anomalies)


@dataclass
class Report:
    """Reporte completo de análisis (puede incluir múltiples archivos)."""
    files: List[FileResult] = field(default_factory=list)
    statistics: dict = field(default_factory=dict)  # Análisis estadístico y outliers a nivel batch

    @property
    def total_anomalies(self) -> int:
        return sum(f.total_anomalies for f in self.files)

    @property
    def critical_count(self) -> int:
        return sum(f.critical_count for f in self.files)

    @property
    def warning_count(self) -> int:
        return sum(f.warning_count for f in self.files)

    @property
    def info_count(self) -> int:
        return sum(f.info_count for f in self.files)

    def anomalies_by_category(self) -> dict:
        """Agrupa todas las anomalías por categoría."""
        result: dict = {}
        for file_result in self.files:
            for anomaly in file_result.anomalies:
                result.setdefault(anomaly.category, []).append(anomaly)
        return result
