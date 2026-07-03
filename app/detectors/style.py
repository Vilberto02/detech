"""
Detector de Anomalías de Estilo y Convenciones.
"""

import re
from typing import List, Set

from .base import BaseDetector
from ..core.models import Anomaly
from ..core.tokenizer import Token, NAME_TOKEN, PYTHON_KEYWORDS


# Patrones de convención de nombres
_SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
_CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]+$")
_PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]+$")
_UPPER_SNAKE = re.compile(r"^[A-Z_][A-Z0-9_]*$")  # Constantes


class StyleDetector(BaseDetector):
    """Detecta anomalías de estilo y convenciones de código."""

    category = "style"

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []

        if self.is_enabled("missing_module_docstring"):
            anomalies.extend(self._check_module_docstring(filepath, tokens))

        if self.is_enabled("naming_convention"):
            anomalies.extend(self._check_naming_convention(filepath, tokens))

        return anomalies


    def _check_module_docstring(self, filepath, tokens) -> List[Anomaly]:
        """
        Verifica que el archivo comience con un docstring de módulo.
        El primer token significativo debe ser un STRING triple-quoted.
        """
        for tok in tokens:
            if tok.type in ("ENCODING", "NEWLINE", "NL", "COMMENT"):
                continue
            if tok.type == "STRING" and (
                tok.string.startswith('"""') or tok.string.startswith("'''")
            ):
                return []  # Tiene docstring de módulo
            # Primer token significativo no es docstring
            return [Anomaly(
                file=filepath,
                line=1,
                rule_id="STY001",
                category=self.category,
                severity="info",
                message="El archivo no tiene docstring de módulo.",
                context="",
            )]
        return []

    def _check_naming_convention(self, filepath, tokens) -> List[Anomaly]:
        """
        Detecta inconsistencia en convenciones de nombres de funciones/variables.
        En Python la convención esperada es snake_case para funciones y variables.
        Alerta si se detecta camelCase en definiciones de función o variables locales.
        """
        anomalies = []
        seen = set()
        i = 0

        while i < len(tokens):
            tok = tokens[i]

            # Revisar nombres de funciones (def <nombre>)
            if tok.type == NAME_TOKEN and tok.string == "def":
                j = i + 1
                while j < len(tokens) and tokens[j].string in ("(", ):
                    j += 1
                if j < len(tokens) and tokens[j].type == NAME_TOKEN:
                    name = tokens[j].string
                    if self._is_camel_case_violation(name) and name not in seen:
                        seen.add(name)
                        anomalies.append(Anomaly(
                            file=filepath,
                            line=tokens[j].line,
                            rule_id="STY002",
                            category=self.category,
                            severity="info",
                            message=(
                                f"El nombre de función '{name}' usa camelCase. "
                                "En Python se prefiere snake_case (PEP 8)."
                            ),
                            context=tokens[j].line_text.strip(),
                        ))
            i += 1

        return anomalies

    @staticmethod
    def _is_camel_case_violation(name: str) -> bool:
        """Retorna True si el nombre usa camelCase (violación PEP 8 para funciones)."""
        if name in PYTHON_KEYWORDS:
            return False
        if name.startswith("_"):
            name = name.lstrip("_")
        # camelCase: comienza con minúscula pero contiene mayúsculas internas
        return bool(re.match(r"^[a-z]+[A-Z][a-zA-Z0-9]*$", name))
