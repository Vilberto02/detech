"""
Detector de Anomalías de Seguridad.
"""

import re
from typing import List

from .base import BaseDetector
from ..core.models import Anomaly
from ..core.tokenizer import Token, build_line_masks, get_span_context


# Patrones de credenciales hardcodeadas.
# secret_key va antes que secret para que el motor prefiera el match largo
# (cubre variantes como aws_secret_key = "...").
_CREDENTIAL_PATTERN = re.compile(
    r"""(?i)(password|passwd|secret_key|secret|api_key|apikey|token|auth_token|access_token|private_key)\s*=\s*['"]([^'"]{2,})['"]"""
)


def _is_plausible_credential(value: str) -> bool:
    """
    Filtro de plausibilidad: una palabra corta puramente alfabética
    (ej. "NAME" en NAME_TOKEN = "NAME") no es un secreto; las credenciales
    reales suelen ser largas o contener dígitos/símbolos.
    """
    return len(value) >= 8 or not value.isalpha()

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
    # f-string que contiene el keyword SQL y una interpolación: f"UPDATE ... {x}"
    re.compile(r"""(?i)\bf['"][^'"]*\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b.*\{"""),
]


class SecurityDetector(BaseDetector):
    """Detecta anomalías de seguridad básicas en el código fuente."""

    category = "security"

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []
        masks = build_line_masks(tokens)

        if self.is_enabled("hardcoded_credentials"):
            anomalies.extend(self._check_credentials(filepath, lines, masks))

        if self.is_enabled("dangerous_functions"):
            anomalies.extend(self._check_dangerous_functions(filepath, tokens))

        if self.is_enabled("sql_concatenation"):
            anomalies.extend(self._check_sql_concatenation(filepath, lines, masks))

        return anomalies


    def _check_credentials(self, filepath, lines, masks) -> List[Anomaly]:
        """Detecta credenciales o claves hardcodeadas en el código."""
        anomalies = []
        for i, line in enumerate(lines, start=1):
            match = _CREDENTIAL_PATTERN.search(line)
            if not match or not _is_plausible_credential(match.group(2)):
                continue
            # Una asignación viva cruza código y string (nombre = "valor");
            # si el match cae completo dentro de un comentario o de un
            # string (docstring, texto de ejemplo), no es una credencial.
            if get_span_context(masks, i, match.start(), match.end()) != "code":
                continue
            # Ocultar el valor real en el contexto mostrado
            safe_context = re.sub(
                r"""(['"][^'"]{2,}['"])""",
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

    def _check_sql_concatenation(self, filepath, lines, masks) -> List[Anomaly]:
        """Detecta posibles inyecciones SQL por concatenación directa."""
        anomalies = []
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            for pattern in _SQL_CONCAT_PATTERNS:
                match = pattern.search(line)
                if match is None:
                    continue
                # Solo se descarta contexto comentario. Una inyección real
                # puede vivir íntegra dentro del literal (sprintf con %s,
                # f-strings interpoladas), así que el string no exonera.
                if get_span_context(masks, i, match.start(), match.end()) == "comment":
                    continue
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
