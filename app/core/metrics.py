"""
Calculadora de métricas de código fuente.
Calcula indicadores cuantitativos a partir de tokens y líneas de código.
"""

from collections import Counter
from typing import List, Dict, Tuple
from .tokenizer import (
    Token,
    NAME_TOKEN,
    COMMENT_TOKEN,
    STRING_TOKEN,
    KEYWORD_TOKEN,
    OP_TOKEN,
    INDENT_TOKEN,
    DEDENT_TOKEN,
    NL_TOKEN,
    NEWLINE_TOKEN,
    DECISION_KEYWORDS,
    SHORT_CIRCUIT_OPERATORS,
    find_function_boundaries,
    find_function_end,
    count_function_params,
)


def count_lines_of_code(lines: List[str]) -> Dict[str, int]:
    """
    Calcula métricas básicas de líneas.

    Returns:
        Dict con claves: total, code, comment, blank
    """
    total = len(lines)
    blank = sum(1 for l in lines if l.strip() == "")
    comment = sum(1 for l in lines if l.strip().startswith("#"))
    code = total - blank - comment

    return {"total": total, "code": code, "comment": comment, "blank": blank}


def max_line_length(lines: List[str]) -> int:
    """Retorna la longitud de la línea más larga."""
    if not lines:
        return 0
    return max(len(l) for l in lines)


def lines_exceeding_limit(lines: List[str], limit: int) -> List[Tuple[int, int]]:
    """
    Retorna una lista de (número_de_línea, longitud) para líneas que superan el límite.

    Args:
        lines: Lista de líneas de código.
        limit: Longitud máxima permitida (PEP 8 = 79).

    Returns:
        Lista de tuplas (línea_1indexed, longitud).
    """
    return [
        (i + 1, len(line))
        for i, line in enumerate(lines)
        if len(line) > limit
    ]


def _count_decision_points(tokens: List[Token]) -> int:
    """Cuenta ramificaciones reales (McCabe) y operadores de cortocircuito."""
    count = 0
    for tok in tokens:
        if tok.type in (NAME_TOKEN, KEYWORD_TOKEN) and tok.string in DECISION_KEYWORDS:
            count += 1
        elif tok.type in (OP_TOKEN, KEYWORD_TOKEN) and tok.string in SHORT_CIRCUIT_OPERATORS:
            count += 1
    return count


def estimate_cyclomatic_complexity(tokens: List[Token]) -> int:
    """
    Estima la complejidad ciclomática según McCabe: 1 (flujo lineal base)
    + puntos de decisión + operadores booleanos de cortocircuito.
    """
    return 1 + _count_decision_points(tokens)


def _dominant_indent_unit(indents: List[int]) -> int:
    """
    Infiere el ancho de un nivel de indentación como la moda de los
    incrementos positivos entre líneas de código consecutivas.
    Si no hay incrementos (archivo plano), retorna 4 por convención.
    """
    diffs = [b - a for a, b in zip(indents, indents[1:]) if b > a]
    if not diffs:
        return 4
    return Counter(diffs).most_common(1)[0][0]


def max_nesting_depth(lines: List[str]) -> int:
    """
    Estima la profundidad máxima de anidamiento basada en la indentación.
    El ancho de un nivel se infiere del propio archivo (2 espacios, 4,
    tabs...), en lugar de asumir 4 espacios.

    Returns:
        Profundidad máxima de anidamiento encontrada.
    """
    indents = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indents.append(len(line) - len(stripped))

    if not indents:
        return 0
    unit = _dominant_indent_unit(indents)
    return max(indent // unit for indent in indents)


def has_mixed_indentation(lines: List[str]) -> bool:
    """
    Detecta si el archivo usa tanto tabs como espacios para indentar.

    Returns:
        True si se detecta mezcla de tabs y espacios.
    """
    has_tabs = any(line.startswith("\t") for line in lines if line.strip())
    has_spaces = any(
        line.startswith(" ") for line in lines if line.strip()
    )
    return has_tabs and has_spaces


def get_function_metrics(tokens: List[Token], lines: List[str]) -> List[Dict]:
    """
    Extrae métricas por función: nombre, línea de inicio, línea de fin,
    longitud y número de parámetros.

    Returns:
        Lista de dicts con info por función.
    """
    raw_funcs = find_function_boundaries(tokens)
    result = []

    for func in raw_funcs:
        start = func["start_line"]
        end = find_function_end(tokens, lines, start, func["params_token_idx"])

        param_idx = func.get("params_token_idx", -1)
        params = 0
        if param_idx >= 0:
            params = count_function_params(tokens, param_idx)

        func_tokens = [t for t in tokens if start <= t.line <= end]
        result.append({
            "name": func["name"],
            "start_line": start,
            "end_line": end,
            "length": end - start + 1,
            "param_count": params,
            "cyclomatic_complexity": 1 + _count_decision_points(func_tokens),
        })

    return result


def count_imports(tokens: List[Token]) -> List[Dict]:
    """
    Detecta declaraciones import y from...import en el código.
    """
    imports = []
    i = 0
    import_keywords = {"import", "from", "require", "include", "use"}
    while i < len(tokens):
        tok = tokens[i]
        if tok.type in (NAME_TOKEN, "KEYWORD") and tok.string in import_keywords:
            module_parts = []
            j = i + 1
            while j < len(tokens):
                t_j = tokens[j]
                if t_j.type in (NAME_TOKEN, STRING_TOKEN, "WHITESPACE"):
                    if t_j.type != "WHITESPACE":
                        # Strip quotes if string
                        mod = t_j.string.strip('"\'')
                        module_parts.append(mod)
                    j += 1
                elif t_j.string in (".", "/", "\\"):
                    j += 1
                else:
                    break
            if module_parts:
                imports.append({
                    "module": ".".join(module_parts),
                    "line": tok.line,
                    "kind": tok.string,
                })
            i = j - 1
        i += 1
    return imports
