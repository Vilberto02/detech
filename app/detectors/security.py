"""
Detector de Anomalías de Seguridad.
"""

import re
from typing import List

from .base import BaseDetector
from ..core.models import Anomaly
from ..core.tokenizer import Token


# Patrones de credenciales hardcodeadas.
# secret_key va antes que secret para que el motor prefiera el match largo
# (cubre variantes como aws_secret_key = "...").
_CREDENTIAL_PATTERN = re.compile(
    r"""(?i)(password|passwd|secret_key|secret|api_key|apikey|token|auth_token|access_token|private_key)\s*=\s*['"][^'"]{3,}['"]"""
)

# Funciones peligrosas en Python, con su severidad.
# compile() no ejecuta código por sí mismo (solo genera el objeto código),
# pero su uso sobre entrada no confiable suele preceder a exec/eval.
_DANGEROUS_FUNCTIONS = {
    "eval": "critical",
    "exec": "critical",
    "execfile": "critical",
    "__import__": "critical",
    "compile": "warning",
}

# Patrones de concatenación directa en SQL
_SQL_CONCAT_PATTERNS = [
    re.compile(r"""(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*['"]\s*\+\s*\w"""),
    re.compile(r"""(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*%\s*\(?\w"""),
    re.compile(r"""(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*\.format\s*\("""),
    re.compile(r"""(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*f['"]"""),
]


class SecurityDetector(BaseDetector):
    """Detecta anomalías de seguridad básicas en el código fuente."""

    category = "security"

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []

        if self.is_enabled("hardcoded_credentials"):
            anomalies.extend(self._check_credentials(filepath, lines))

        if self.is_enabled("dangerous_functions"):
            anomalies.extend(self._check_dangerous_functions(filepath, tokens))

        if self.is_enabled("sql_concatenation"):
            anomalies.extend(self._check_sql_concatenation(filepath, lines))

        return anomalies


    def _check_credentials(self, filepath, lines) -> List[Anomaly]:
        """Detecta credenciales o claves hardcodeadas en el código."""
        anomalies = []
        for i, line in enumerate(lines, start=1):
            # Ignorar líneas que son solo comentarios
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            match = _CREDENTIAL_PATTERN.search(line)
            if match:
                # Ocultar el valor real en el contexto mostrado
                safe_context = re.sub(
                    r"""(['"][^'"]{3,}['"])""",
                    '"***"',
                    line.strip(),
                )
                anomalies.append(Anomaly(
                    file=filepath,
                    line=i,
                    rule_id="SEC001",
                    category=self.category,
                    severity="critical",
                    message=(
                        f"Posible credencial hardcodeada detectada: '{match.group(1)}'."
                        " Usa variables de entorno o un gestor de secretos."
                    ),
                    context=safe_context,
                ))
        return anomalies

    def _check_dangerous_functions(self, filepath, tokens) -> List[Anomaly]:
        """Detecta uso de funciones intrínsecamente peligrosas."""
        anomalies = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.string in _DANGEROUS_FUNCTIONS and tok.type == "NAME":
                # Verificar que el siguiente token sea '(' (llamada a función)
                if i + 1 < len(tokens) and tokens[i + 1].string == "(":
                    severity = _DANGEROUS_FUNCTIONS[tok.string]
                    if tok.string == "compile":
                        message = (
                            "Uso de 'compile()': genera objetos de código. "
                            "Verifica que la fuente no provenga de entrada no confiable."
                        )
                    else:
                        message = (
                            f"Uso de función peligrosa: '{tok.string}()'."
                            " Esta función puede ejecutar código arbitrario."
                        )
                    anomalies.append(Anomaly(
                        file=filepath,
                        line=tok.line,
                        rule_id="SEC002",
                        category=self.category,
                        severity=severity,
                        message=message,
                        context=tok.line_text.strip(),
                    ))
            i += 1
        return anomalies

    def _check_sql_concatenation(self, filepath, lines) -> List[Anomaly]:
        """Detecta posibles inyecciones SQL por concatenación directa."""
        anomalies = []
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _SQL_CONCAT_PATTERNS:
                if pattern.search(line):
                    anomalies.append(Anomaly(
                        file=filepath,
                        line=i,
                        rule_id="SEC003",
                        category=self.category,
                        severity="critical",
                        message=(
                            "Posible SQL Injection: consulta SQL construida por concatenación "
                            "o interpolación de strings. Usa consultas parametrizadas."
                        ),
                        context=stripped[:120],
                    ))
                    break  # Un reporte por línea es suficiente
        return anomalies
