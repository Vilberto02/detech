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


def count_lines_of_code(lines: List[str], tokens: List[Token]) -> Dict[str, int]:
    """
    Calcula métricas básicas de líneas. Una línea cuenta como comentario
    si todos sus tokens son COMMENT (según el lexer del lenguaje: #, //,
    /* */, etc.); una línea con código y comentario al final es código.

    Returns:
        Dict con claves: total, code, comment, blank
    """
    total = len(lines)
    blank = sum(1 for l in lines if l.strip() == "")

    comment_lines = set()
    other_lines = set()
    for tok in tokens:
        if tok.type == NEWLINE_TOKEN:
            continue
        if tok.type == COMMENT_TOKEN:
            comment_lines.add(tok.line)
        else:
            other_lines.add(tok.line)
    comment = len(comment_lines - other_lines)

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


def has_mixed_indentation(lines: List[str], tokens: List[Token]) -> bool:
    """
    Detecta si el archivo mezcla tabs y espacios en la indentación
    estructural de líneas de código. Se excluyen las líneas interiores
    de strings multilínea, las continuaciones dentro de paréntesis o
    corchetes (alineadas con espacios por convención) y los comentarios,
    cuyo sangrado no define bloques.

    Returns:
        True si ambos estilos aparecen en líneas de código indentadas.
    """
    # Líneas que continúan un token multilínea (docstrings, strings largos)
    string_continuations = {t.line for t in tokens if t.is_continuation}

    # Líneas que comienzan con un paréntesis/corchete aún abierto
    # (no se rastrean llaves: en JS/Go/Rust delimitan bloques normales)
    bracket_continuations = set()
    depth = 0
    last_line = 0
    for tok in tokens:
        if tok.line != last_line:
            if depth > 0:
                bracket_continuations.add(tok.line)
            last_line = tok.line
        if tok.type == OP_TOKEN:
            if tok.string in ("(", "["):
                depth += 1
            elif tok.string in (")", "]"):
                depth = max(0, depth - 1)

    code_lines = {
        tok.line
        for tok in tokens
        if tok.type not in (COMMENT_TOKEN, NEWLINE_TOKEN) and not tok.is_continuation
    }

    has_tabs = has_spaces = False
    for ln in code_lines - string_continuations - bracket_continuations:
        line = lines[ln - 1] if ln <= len(lines) else ""
        if line.startswith("\t"):
            has_tabs = True
        elif line.startswith(" "):
            has_spaces = True
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


def _collect_dotted_name(tokens: List[Token], j: int) -> Tuple[List[str], int]:
    """
    Avanza sobre un nombre punteado ('os.path', 'a/b') y retorna
    (partes, índice del primer token que no pertenece al nombre).
    """
    parts = []
    while j < len(tokens):
        t = tokens[j]
        # El separador va primero: Pygments puede tipar el '.' como NAME
        if t.string in (".", "/", "\\"):
            j += 1
        elif t.type in (NAME_TOKEN, STRING_TOKEN):
            parts.append(t.string.strip('"\''))
            j += 1
        else:
            break
    return parts, j


def count_imports(tokens: List[Token]) -> List[Dict]:
    """
    Detecta declaraciones de import en el código.

    - "import a, b" produce una entrada por módulo.
    - "from X import a, b" produce UNA sola entrada para X, con los
      nombres importados en la clave "names" (los que el código referencia).
    """
    imports = []
    import_keywords = {"import", "from", "require", "include", "use"}
    n = len(tokens)
    i = 0
    while i < n:
        tok = tokens[i]
        if not (tok.type in (NAME_TOKEN, "KEYWORD") and tok.string in import_keywords):
            i += 1
            continue

        kind = tok.string
        line = tok.line

        if kind == "from":
            module_parts, j = _collect_dotted_name(tokens, i + 1)
            names = []
            if j < n and tokens[j].string == "import":
                j += 1
                while j < n:
                    name_parts, j = _collect_dotted_name(tokens, j)
                    if name_parts:
                        names.append(name_parts[-1])
                    if j < n and tokens[j].string == ",":
                        j += 1
                    else:
                        break
            if module_parts:
                imports.append({
                    "module": ".".join(module_parts),
                    "line": line,
                    "kind": kind,
                    "names": names,
                })
        else:
            j = i + 1
            while j < n:
                module_parts, j = _collect_dotted_name(tokens, j)
                if module_parts:
                    imports.append({
                        "module": ".".join(module_parts),
                        "line": line,
                        "kind": kind,
                    })
                if j < n and tokens[j].string == ",":
                    j += 1
                else:
                    break

        # Continuar después de lo consumido (sin retroceder al 'import'
        # interno de un from-import, que era lo que duplicaba entradas)
        i = max(j, i + 1)
    return imports
