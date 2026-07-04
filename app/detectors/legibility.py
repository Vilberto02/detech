"""
Detector de anomalías de Legibilidad y Mantenibilidad.
"""

import re
from typing import List

from .base import BaseDetector
from ..core.models import Anomaly
from ..core.tokenizer import Token, NAME_TOKEN, KEYWORD_TOKEN


class LegibilityDetector(BaseDetector):
    """Detecta anomalías relacionadas con la legibilidad y mantenibilidad del código."""

    category = "legibility"

    # Nombres cortos que son convencionales y no deben alertar
    ALLOWED_SHORT_NAMES = frozenset({
        "i", "j", "k", "n", "x", "y", "z", "e", "f", "g",
        "_", "id", "db", "df", "ok", "cb", "fn", "op",
    })

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []

        if self.is_enabled("long_function"):
            anomalies.extend(self._check_long_functions(filepath, metrics))

        if self.is_enabled("large_file"):
            anomalies.extend(self._check_large_file(filepath, lines, metrics))

        if self.is_enabled("long_line"):
            anomalies.extend(self._check_long_lines(filepath, lines))

        if self.is_enabled("inconsistent_indent"):
            anomalies.extend(self._check_indentation(filepath, lines, metrics))

        if self.is_enabled("short_variable_name"):
            anomalies.extend(self._check_short_names(filepath, tokens))

        if self.is_enabled("missing_docstring"):
            anomalies.extend(self._check_missing_docstrings(filepath, tokens, lines))

        return anomalies

    # Reglas individuales

    def _check_long_functions(self, filepath, metrics) -> List[Anomaly]:
        anomalies = []
        limit = self.config.get_threshold("max_function_lines", 50)
        for func in metrics.get("functions", []):
            if func["length"] > limit:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=func["start_line"],
                    rule_id="LEG001",
                    category=self.category,
                    severity="warning",
                    message=(
                        f"La función '{func['name']}' tiene {func['length']} líneas "
                        f"(máximo permitido: {limit})."
                    ),
                    context=f"def {func['name']}(...)",
                ))
        return anomalies

    def _check_large_file(self, filepath, lines, metrics) -> List[Anomaly]:
        limit = self.config.get_threshold("max_file_lines", 500)
        total = metrics.get("loc", {}).get("total", len(lines))
        if total > limit:
            return [Anomaly(
                file=filepath,
                line=1,
                rule_id="LEG002",
                category=self.category,
                severity="warning",
                message=f"El archivo tiene {total} líneas (máximo permitido: {limit}).",
                context="",
            )]
        return []

    def _check_long_lines(self, filepath, lines) -> List[Anomaly]:
        anomalies = []
        limit = self.config.get_threshold("max_line_length", 79)
        for i, line in enumerate(lines, start=1):
            if len(line) > limit:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=i,
                    rule_id="LEG003",
                    category=self.category,
                    severity="info",
                    message=(
                        f"Línea demasiado larga: {len(line)} caracteres "
                        f"(máximo recomendado: {limit})."
                    ),
                    context=line[:120] + ("..." if len(line) > 120 else ""),
                ))
        return anomalies

    def _check_indentation(self, filepath, lines, metrics) -> List[Anomaly]:
        if not metrics.get("mixed_indentation", False):
            return []
        return [Anomaly(
            file=filepath,
            line=1,
            rule_id="LEG004",
            category=self.category,
            severity="warning",
            message="Indentación inconsistente: se detectó mezcla de tabs y espacios.",
            context="",
        )]

    def _check_short_names(self, filepath, tokens) -> List[Anomaly]:
        """Detecta identificadores de 1-2 caracteres que no son convencionales."""
        anomalies = []
        seen_lines = set()

        for tok in tokens:
            if tok.type != NAME_TOKEN:
                continue
            name = tok.string
            # Ignorar: nombres permitidos, nombres de 3+ chars
            if (
                name in self.ALLOWED_SHORT_NAMES
                or len(name) > 2
            ):
                continue
            # Ignorar si ya se reportó esta línea
            if tok.line in seen_lines:
                continue
            seen_lines.add(tok.line)
            anomalies.append(Anomaly(
                file=filepath,
                line=tok.line,
                rule_id="LEG005",
                category=self.category,
                severity="info",
                message=f"Nombre de variable poco descriptivo: '{name}'.",
                context=tok.line_text.strip(),
            ))
        return anomalies

    def _check_missing_docstrings(self, filepath, tokens, lines) -> List[Anomaly]:
        """
        Detecta funciones sin docstring inmediatamente después del `def`.
        Una función tiene docstring si el primer token no-vacío tras los `:`
        es un STRING literal triple-quoted.
        """
        anomalies = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == KEYWORD_TOKEN and tok.string in ("def", "func", "function", "fn"):
                func_line = tok.line
                func_name = ""
                # Nombre de la función
                j = i + 1
                while j < len(tokens) and tokens[j].string != "(":
                    if tokens[j].type == NAME_TOKEN:
                        func_name = tokens[j].string
                    j += 1
                # Avanzar al cuerpo: buscar el primer STRING tras el ':'
                # Buscamos en los próximos 10 tokens no-whitespace
                found_colon = False
                has_docstring = False
                k = j
                steps = 0
                while k < len(tokens) and steps < 20:
                    t = tokens[k]
                    if t.string == ":":
                        found_colon = True
                    elif found_colon and t.type not in ("NEWLINE", "NL", "INDENT", "DEDENT", "COMMENT"):
                        if t.type == "STRING" and (t.string.startswith('"""') or t.string.startswith("'''")):
                            has_docstring = True
                        break
                    k += 1
                    steps += 1

                if not has_docstring:
                    anomalies.append(Anomaly(
                        file=filepath,
                        line=func_line,
                        rule_id="LEG006",
                        category=self.category,
                        severity="info",
                        message=f"La función '{func_name}' no tiene docstring.",
                        context=lines[func_line - 1].strip() if func_line <= len(lines) else "",
                    ))
            i += 1
        return anomalies
