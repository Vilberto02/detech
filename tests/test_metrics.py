"""
Tests unitarios para las métricas de app/core/metrics.py.
"""

from app.core.tokenizer import tokenize_source
from app.core.metrics import (
    count_lines_of_code,
    estimate_cyclomatic_complexity,
    get_function_metrics,
    has_mixed_indentation,
    max_nesting_depth,
)


def _funcs(source: str, filename: str = "t.py"):
    tokens = tokenize_source(source, filename)
    lines = source.splitlines()
    return {f["name"]: f for f in get_function_metrics(tokens, lines)}


# ---------------------------------------------------------------------------
# Fin de función (delimitación de bloque sin AST)
# ---------------------------------------------------------------------------

PY_CODIGO_POSTERIOR = '''def sola():
    return 1


a = 1
b = 2
c = 3
'''


def test_fin_de_funcion_no_incluye_codigo_posterior():
    funcs = _funcs(PY_CODIGO_POSTERIOR)
    assert funcs["sola"]["end_line"] == 2
    assert funcs["sola"]["length"] == 2


PY_ANIDADA = '''def outer():
    def inner():
        return 1
    return inner


x = 1
'''


def test_fin_de_funcion_anidada():
    funcs = _funcs(PY_ANIDADA)
    # inner termina en su propio dedent, no al final del archivo
    assert funcs["inner"]["end_line"] == 3
    assert funcs["inner"]["length"] == 2
    # outer abarca a inner y su propio return
    assert funcs["outer"]["end_line"] == 4
    assert funcs["outer"]["length"] == 4


PY_DOCSTRING_DEDENTADO = '''def con_docstring():
    """Resumen.

ejemplo dedentado dentro del docstring
    """
    return 1
'''


def test_fin_de_funcion_docstring_con_linea_dedentada():
    funcs = _funcs(PY_DOCSTRING_DEDENTADO)
    # La línea dedentada está dentro del string y no debe cortar el bloque
    assert funcs["con_docstring"]["end_line"] == 6
    assert funcs["con_docstring"]["length"] == 6


JS_LLAVES = '''function foo() {
  if (a) {
    b();
  }
}
var x = 1;
var y = 2;
'''


def test_fin_de_funcion_por_llaves_balanceadas():
    funcs = _funcs(JS_LLAVES, "t.js")
    assert funcs["foo"]["end_line"] == 5
    assert funcs["foo"]["length"] == 5


# ---------------------------------------------------------------------------
# Complejidad ciclomática (McCabe)
# ---------------------------------------------------------------------------

def test_complejidad_no_cuenta_else_try_finally_with():
    src = (
        "try:\n"
        "    if a:\n"
        "        pass\n"
        "    else:\n"
        "        pass\n"
        "finally:\n"
        "    pass\n"
        "with open('f') as f:\n"
        "    pass\n"
    )
    # Solo 'if' es punto de decisión: base 1 + 1
    assert estimate_cyclomatic_complexity(tokenize_source(src, "t.py")) == 2


def test_complejidad_cuenta_operadores_booleanos_python():
    src = "if a and b or c:\n    pass\n"
    # if + and + or: base 1 + 3
    assert estimate_cyclomatic_complexity(tokenize_source(src, "t.py")) == 4


def test_complejidad_cuenta_operadores_booleanos_js():
    src = "if (a && b || c) {\n  d();\n}\n"
    assert estimate_cyclomatic_complexity(tokenize_source(src, "t.js")) == 4


PY_DOS_FUNCIONES = '''def simple():
    return 1


def ramas(v):
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0
'''


def test_complejidad_por_funcion():
    funcs = _funcs(PY_DOS_FUNCIONES)
    assert funcs["simple"]["cyclomatic_complexity"] == 1
    assert funcs["ramas"]["cyclomatic_complexity"] == 3


# ---------------------------------------------------------------------------
# Profundidad de anidamiento (inferencia del ancho de indentación)
# ---------------------------------------------------------------------------

def test_nesting_con_indentacion_de_2_espacios():
    src = (
        "function f() {\n"
        "  if (a) {\n"
        "    if (b) {\n"
        "      c();\n"
        "    }\n"
        "  }\n"
        "}\n"
    )
    # 3 niveles con indentación de 2: con indent fijo de 4 salía 1
    assert max_nesting_depth(src.splitlines()) == 3


def test_nesting_con_indentacion_de_4_espacios():
    src = "if a:\n    if b:\n        x = 1\n"
    assert max_nesting_depth(src.splitlines()) == 2


def test_nesting_con_tabs():
    src = "if a:\n\tif b:\n\t\tx = 1\n"
    assert max_nesting_depth(src.splitlines()) == 2


# ---------------------------------------------------------------------------
# Conteo de líneas (comentarios multilenguaje vía tokens)
# ---------------------------------------------------------------------------

def _loc(source: str, filename: str):
    lines = source.splitlines()
    return count_lines_of_code(lines, tokenize_source(source, filename))


def test_loc_comentarios_python():
    src = "# comentario\nx = 1\n\n"
    loc = _loc(src, "t.py")
    assert loc == {"total": 3, "code": 1, "comment": 1, "blank": 1}


def test_loc_comentarios_js():
    src = (
        "// comentario\n"
        "var x = 1; // inline no cuenta como comentario\n"
        "\n"
        "/*\n"
        "bloque\n"
        "*/\n"
        "y = 2;\n"
    )
    loc = _loc(src, "t.js")
    # línea 1 (//), y líneas 4-6 (/* */) son comentario; la 2 es código
    assert loc == {"total": 7, "code": 2, "comment": 4, "blank": 1}


# ---------------------------------------------------------------------------
# Indentación mixta (solo indentación estructural de líneas de código)
# ---------------------------------------------------------------------------

def _mixed(source: str, filename: str = "t.py"):
    return has_mixed_indentation(source.splitlines(), tokenize_source(source, filename))


def test_indentacion_mixta_real():
    src = "def f():\n\tif a:\n        return 1\n"
    assert _mixed(src) is True


def test_indentacion_consistente_con_espacios():
    src = "def f():\n    if a:\n        return 1\n"
    assert _mixed(src) is False


def test_docstring_con_espacios_no_es_indentacion_mixta():
    # Archivo indentado con tabs; el interior del docstring usa espacios
    src = 'def f():\n\t"""Doc.\n    contenido con espacios\n\t"""\n\treturn 1\n'
    assert _mixed(src) is False


def test_continuacion_entre_parentesis_no_es_indentacion_mixta():
    # La línea 3 se alinea con espacios dentro del paréntesis abierto
    src = "def f():\n\tx = calcular(1,\n                 2)\n\treturn x\n"
    assert _mixed(src) is False
