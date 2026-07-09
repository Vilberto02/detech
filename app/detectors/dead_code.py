"""
Detector de Código Muerto o Redundante.
"""

import re
from typing import List, Set

from .base import BaseDetector
from ..core.models import Anomaly
from ..core.tokenizer import Token, NAME_TOKEN, COMMENT_TOKEN, STRING_TOKEN, is_commented_code_line


# Anotaciones técnicas pendientes
_ANNOTATION_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG|NOQA)\b", re.IGNORECASE)


class DeadCodeDetector(BaseDetector):
    """Detecta código muerto, redundante o anotaciones pendientes."""

    category = "dead_code"

    def detect(self, filepath, lines, tokens, metrics) -> List[Anomaly]:
        anomalies = []

        if self.is_enabled("pending_annotations"):
            anomalies.extend(self._check_annotations(filepath, lines))

        if self.is_enabled("commented_code"):
            anomalies.extend(self._check_commented_code(filepath, lines))

        if self.is_enabled("unused_import"):
            anomalies.extend(self._check_unused_imports(filepath, tokens, metrics))

        return anomalies

    # ------------------------------------------------------------------

    def _check_annotations(self, filepath, lines) -> List[Anomaly]:
        """Detecta comentarios con TODO, FIXME, HACK, XXX."""
        anomalies = []
        for i, line in enumerate(lines, start=1):
            match = _ANNOTATION_PATTERN.search(line)
            if match:
                anomalies.append(Anomaly(
                    file=filepath,
                    line=i,
                    rule_id="DCO001",
                    category=self.category,
                    severity="info",
                    message=f"Anotación pendiente encontrada: '{match.group()}'.",
                    context=line.strip(),
                ))
        return anomalies

    def _check_commented_code(self, filepath, lines) -> List[Anomaly]:
        """
        Detecta bloques consecutivos de líneas que parecen código comentado.
        Requiere al menos `min_commented_code_block` líneas consecutivas.
        """
        anomalies = []
        min_block = self.config.get_threshold("min_commented_code_block", 3)
        block_start = None
        block_count = 0

        for i, line in enumerate(lines, start=1):
            if is_commented_code_line(line):
                if block_start is None:
                    block_start = i
                block_count += 1
            else:
                if block_count >= min_block:
                    anomalies.append(Anomaly(
                        file=filepath,
                        line=block_start,
                        rule_id="DCO002",
                        category=self.category,
                        severity="warning",
                        message=(
                            f"Bloque de código comentado detectado "
                            f"({block_count} líneas desde la línea {block_start}). "
                            "Considera eliminarlo si ya no es necesario."
                        ),
                        context=lines[block_start - 1].strip(),
                    ))
                block_start = None
                block_count = 0

        # Verificar bloque al final del archivo
        if block_count >= min_block and block_start is not None:
            anomalies.append(Anomaly(
                file=filepath,
                line=block_start,
                rule_id="DCO002",
                category=self.category,
                severity="warning",
                message=(
                    f"Bloque de código comentado detectado "
                    f"({block_count} líneas desde la línea {block_start})."
                ),
                context=lines[block_start - 1].strip(),
            ))

        return anomalies

    def _check_unused_imports(self, filepath, tokens, metrics) -> List[Anomaly]:
        """
        Detecta imports que no son referenciados en el resto del archivo.

        Estrategia léxica:
        1. Recopilar todos los nombres importados.
        2. Buscar si el nombre aparece en algún token NAME fuera de las líneas de import.
        """
        anomalies = []
        imports = metrics.get("imports", [])
        if not imports:
            return []

        import_lines: Set[int] = {imp["line"] for imp in imports}

        # Recolectar todos los NAME tokens fuera de las líneas de import
        used_names: Set[str] = {
            tok.string
            for tok in tokens
            if tok.type == NAME_TOKEN and tok.line not in import_lines
        }

        for imp in imports:
            module = imp.get("module", "")
            if not module:
                continue
            names = imp.get("names") or []
            if names:
                # "from X import a, b" → lo referenciable son los nombres
                if any(name in used_names for name in names):
                    continue
                context = f"{imp['kind']} {module} import {', '.join(names)}"
            else:
                # "import os.path" → lo referenciable es la raíz "os"
                root_name = module.split(".")[0]
                if not root_name or root_name in used_names:
                    continue
                context = f"{imp['kind']} {module}"

            anomalies.append(Anomaly(
                file=filepath,
                line=imp["line"],
                rule_id="DCO003",
                category=self.category,
                severity="warning",
                message=f"Import posiblemente no utilizado: '{module}'.",
                context=context,
            ))

        return anomalies
