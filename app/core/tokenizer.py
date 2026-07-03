"""
Tokenización léxica de código fuente Python.
Usa el módulo `tokenize` de la stdlib para descomponer el código en tokens
sin construir un árbol sintáctico formal.
"""

import io
import re
import tokenize as _tokenize
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    """Representa un token léxico del código fuente."""
    type: str          # Categoría: NAME, STRING, NUMBER, OP, COMMENT, NEWLINE, etc.
    string: str        # Valor textual del token
    line: int          # Número de línea (1-indexed)
    col: int           # Columna de inicio (0-indexed)
    line_text: str     # Texto completo de la línea donde aparece el token


# Tipos de token que representan nombres/identificadores
NAME_TOKEN = "NAME"
COMMENT_TOKEN = "COMMENT"
STRING_TOKEN = "STRING"
OP_TOKEN = "OP"
NEWLINE_TOKEN = "NEWLINE"
NL_TOKEN = "NL"
INDENT_TOKEN = "INDENT"
DEDENT_TOKEN = "DEDENT"
ENDMARKER_TOKEN = "ENDMARKER"
ENCODING_TOKEN = "ENCODING"

# Palabras clave de Python para complejidad ciclomática
CONTROL_FLOW_KEYWORDS = frozenset({
    "if", "elif", "else", "for", "while", "try", "except",
    "finally", "with", "case", "match", "and", "or",
})

# Palabras clave de Python (completo)
PYTHON_KEYWORDS = frozenset({
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield", "match", "case",
})


def tokenize_source(source: str) -> List[Token]:
    """
    Tokeniza el código fuente Python usando el módulo `tokenize` de la stdlib.

    Args:
        source: Contenido completo del archivo fuente como string.

    Returns:
        Lista de objetos Token.

    Note:
        Los tokens ERRORTOKEN (código con errores de encoding o caracteres raros)
        son ignorados silenciosamente para robustez.
    """
    tokens: List[Token] = []
    source_bytes = source.encode("utf-8", errors="replace")
    readline = io.BytesIO(source_bytes).readline

    try:
        for tok in _tokenize.tokenize(readline):
            tok_type_name = _tokenize.tok_name.get(tok.type, "UNKNOWN")

            # Ignorar tokens de infraestructura que no aportan al análisis
            if tok_type_name in (ENDMARKER_TOKEN, ENCODING_TOKEN):
                continue

            tokens.append(Token(
                type=tok_type_name,
                string=tok.string,
                line=tok.start[0],
                col=tok.start[1],
                line_text=tok.line.rstrip("\n"),
            ))
    except _tokenize.TokenError:
        # Archivo con errores de sintaxis parciales — retornar lo tokenizado hasta el error
        pass

    return tokens


def get_lines(source: str) -> List[str]:
    """Retorna las líneas del código fuente (sin salto de línea final)."""
    return source.splitlines()


def find_function_boundaries(tokens: List[Token]) -> List[dict]:
    """
    Detecta funciones y métodos en el código a partir de tokens NAME `def`.

    Returns:
        Lista de dicts con: name, start_line, param_count.
        El end_line se determina más adelante en MetricsCalculator.
    """
    functions = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == NAME_TOKEN and tok.string == "def":
            # El siguiente token NAME es el nombre de la función
            name = ""
            params_start = -1
            j = i + 1
            while j < len(tokens) and tokens[j].type in (NL_TOKEN, NEWLINE_TOKEN, INDENT_TOKEN):
                j += 1
            if j < len(tokens) and tokens[j].type == NAME_TOKEN:
                name = tokens[j].string
                j += 1
            # Buscar paréntesis de apertura para contar parámetros
            while j < len(tokens) and tokens[j].string != "(":
                j += 1
            params_start = j
            functions.append({
                "name": name,
                "start_line": tok.line,
                "params_token_idx": params_start,
            })
        i += 1
    return functions


def count_function_params(tokens: List[Token], open_paren_idx: int) -> int:
    """
    Cuenta los parámetros de una función dado el índice del token '('.

    Args:
        tokens: Lista completa de tokens.
        open_paren_idx: Índice del token '(' de apertura.

    Returns:
        Número de parámetros (0 para funciones sin parámetros, excluyendo `self`/`cls`).
    """
    depth = 0
    param_count = 0
    found_param = False
    i = open_paren_idx

    while i < len(tokens):
        tok = tokens[i]
        if tok.string == "(":
            depth += 1
        elif tok.string == ")":
            depth -= 1
            if depth == 0:
                if found_param:
                    param_count += 1
                break
        elif depth == 1 and tok.string == ",":
            param_count += 1
        elif depth == 1 and tok.type == NAME_TOKEN and not found_param:
            found_param = True
        i += 1

    # Excluir self/cls del conteo (primer parámetro de métodos)
    return param_count


# Patrón regex para detectar bloques de código Python dentro de comentarios
_COMMENTED_CODE_PATTERN = re.compile(
    r"^\s*#\s*(def |class |import |from |if |for |while |return |with |try:)",
    re.IGNORECASE,
)


def is_commented_code_line(line: str) -> bool:
    """Heurística: retorna True si la línea parece ser código comentado."""
    return bool(_COMMENTED_CODE_PATTERN.match(line))
