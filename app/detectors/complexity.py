"""
Detector de anomalías de Complejidad.
"""

from typing import List

from .base import BaseDetector
from ..core.models import Anomaly


class ComplexityDetector(BaseDetector):
    """Detecta anomalías relacionadas con la complejidad del código."""

    category = "complexity"

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []

        if self.is_enabled("high_complexity"):
            anomalies.extend(self._check_complexity(filepath, metrics))

        if self.is_enabled("deep_nesting"):
            anomalies.extend(self._check_nesting(filepath, metrics))

        if self.is_enabled("too_many_params"):
            anomalies.extend(self._check_params(filepath, metrics))

        if self.is_enabled("high_coupling"):
            anomalies.extend(self._check_coupling(filepath, metrics))

        return anomalies

    def _check_complexity(self, filepath, metrics) -> List[Anomaly]:
        """
        Reporta complejidad por función (unidad estándar de McCabe).
        Si el archivo no tiene funciones (script plano), usa la métrica global.
        """
        limit = self.config.get_threshold("max_complexity", 10)
        functions = metrics.get("functions", [])
        anomalies = []

        for func in functions:
            complexity = func.get("cyclomatic_complexity", 1)
            if complexity > limit:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=func["start_line"],
                    rule_id="CPX001",
                    category=self.category,
                    severity="critical",
                    message=(
                        f"La función '{func['name']}' tiene complejidad ciclomática "
                        f"estimada {complexity} (máximo: {limit})."
                    ),
                    context=f"def {func['name']}(...)",
                ))

        if not functions:
            complexity = metrics.get("cyclomatic_complexity", 1)
            if complexity > limit:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=1,
                    rule_id="CPX001",
                    category=self.category,
                    severity="critical",
                    message=(
                        f"Alta complejidad ciclomática estimada: {complexity} "
                        f"(máximo: {limit}). El archivo contiene demasiadas ramificaciones."
                    ),
                    context="",
                ))

        return anomalies

    def _check_nesting(self, filepath, metrics) -> List[Anomaly]:
        limit = self.config.get_threshold("max_nesting_depth", 4)
        depth = metrics.get("max_nesting_depth", 0)
        if depth > limit:
            return [Anomaly(
                file=filepath,
                line=1,
                rule_id="CPX002",
                category=self.category,
                severity="warning",
                message=(
                    f"Anidamiento excesivo detectado: profundidad máxima {depth} "
                    f"(máximo: {limit} niveles)."
                ),
                context="",
            )]
        return []

    def _check_params(self, filepath, metrics) -> List[Anomaly]:
        limit = self.config.get_threshold("max_parameters", 5)
        anomalies = []
        for func in metrics.get("functions", []):
            if func["param_count"] > limit:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=func["start_line"],
                    rule_id="CPX003",
                    category=self.category,
                    severity="warning",
                    message=(
                        f"La función '{func['name']}' tiene {func['param_count']} parámetros "
                        f"(máximo: {limit}). Considere usar un objeto de configuración."
                    ),
                    context=f"def {func['name']}(...)",
                ))
        return anomalies

    def _check_coupling(self, filepath, metrics) -> List[Anomaly]:
        limit = self.config.get_threshold("max_imports", 15)
        import_count = len(metrics.get("imports", []))
        if import_count > limit:
            return [Anomaly(
                file=filepath,
                line=1,
                rule_id="CPX004",
                category=self.category,
                severity="warning",
                message=(
                    f"Acoplamiento excesivo: {import_count} módulos importados "
                    f"(máximo: {limit}). El módulo depende de demasiadas dependencias externas."
                ),
                context="",
            )]
        return []
