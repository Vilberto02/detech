"""
Motor de Reglas (RuleEngine).
Orquesta todos los detectores y produce el resultado del análisis de un archivo.
"""

import re
from pathlib import Path
from typing import List

from ..core.models import Anomaly, FileResult
from ..core.input_loader import load_file
from ..core.tokenizer import tokenize_source, get_lines
from ..core.metrics import (
    count_lines_of_code,
    estimate_cyclomatic_complexity,
    max_nesting_depth,
    has_mixed_indentation,
    get_function_metrics,
    count_imports,
)
from ..config.config_manager import ConfigManager
from ..detectors.legibility import LegibilityDetector
from ..detectors.complexity import ComplexityDetector
from ..detectors.dead_code import DeadCodeDetector
from ..detectors.security import SecurityDetector
from ..detectors.style import StyleDetector


class RuleEngine:
    """
    Orquestador del análisis estático.
    Aplica todos los detectores registrados sobre un archivo de código fuente.
    """

    def __init__(self, config: ConfigManager):
        self.config = config
        self._detectors = [
            LegibilityDetector(config),
            ComplexityDetector(config),
            DeadCodeDetector(config),
            SecurityDetector(config),
            StyleDetector(config),
        ]

    def analyze_file(self, filepath: str | Path) -> FileResult:
        """
        Analiza un archivo Python y retorna su FileResult con todas las anomalías.

        Args:
            filepath: Ruta al archivo .py a analizar.

        Returns:
            FileResult con las anomalías encontradas.
        """
        filepath = str(filepath)

        # 1. Cargar archivo
        source, lines = load_file(filepath)

        # 2. Tokenizar
        tokens = tokenize_source(source, filepath)

        # 3. Calcular métricas
        metrics = {
            "loc": count_lines_of_code(lines, tokens),
            "cyclomatic_complexity": estimate_cyclomatic_complexity(tokens),
            "max_nesting_depth": max_nesting_depth(lines),
            "mixed_indentation": has_mixed_indentation(lines),
            "functions": get_function_metrics(tokens, lines),
            "imports": count_imports(tokens),
        }

        # 4. Ejecutar detectores
        all_anomalies: List[Anomaly] = []
        for detector in self._detectors:
            try:
                found = detector.detect(filepath, lines, tokens, metrics)
                all_anomalies.extend(found)
            except Exception as exc:
                # Los detectores no deben detener el análisis completo
                all_anomalies.append(Anomaly(
                    file=filepath,
                    line=0,
                    rule_id="SYS000",
                    category="system",
                    severity="warning",
                    message=f"Error interno en detector '{type(detector).__name__}': {exc}",
                    context="",
                ))

        # 5. Aplicar patrones personalizados del usuario
        all_anomalies.extend(self._apply_custom_patterns(filepath, lines))

        # 6. Ordenar por línea
        all_anomalies.sort(key=lambda a: a.line)

        return FileResult(
            filepath=filepath,
            total_lines=metrics["loc"]["total"],
            anomalies=all_anomalies,
            metrics=metrics,
        )

    def _apply_custom_patterns(self, filepath: str, lines: List[str]) -> List[Anomaly]:
        """Aplica los patrones regex personalizados definidos por el usuario en detech.yaml."""
        anomalies = []
        for pattern_def in self.config.custom_patterns:
            pid = pattern_def.get("id", "CUSTOM")
            name = pattern_def.get("name", pid)
            regex_str = pattern_def.get("pattern", "")
            severity = pattern_def.get("severity", "info")
            message = pattern_def.get("message", f"Patrón '{name}' detectado.")

            if not regex_str:
                continue
            try:
                regex = re.compile(regex_str)
            except re.error:
                continue

            for i, line in enumerate(lines, start=1):
                if regex.search(line):
                    anomalies.append(Anomaly(
                        file=filepath,
                        line=i,
                        rule_id=pid,
                        category="custom",
                        severity=severity,
                        message=message,
                        context=line.strip()[:120],
                    ))
        return anomalies
