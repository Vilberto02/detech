"""
Tests de las máscaras de línea (build_line_masks / get_span_context):
clasificación de rangos de columnas como código, comentario o string.
"""

from app.core.tokenizer import tokenize_source, build_line_masks, get_span_context


def _ctx(source, filename, line, start, end):
    masks = build_line_masks(tokenize_source(source, filename))
    return get_span_context(masks, line, start, end)


def test_span_en_comentario_python():
    src = 'x = 1  # password = "abc"\n'
    # "password" ocupa las columnas 9-17, dentro del comentario
    assert _ctx(src, "t.py", 1, 9, 17) == "comment"


def test_span_en_comentario_js():
    src = '// api_key = "xyz"\n'
    assert _ctx(src, "t.js", 1, 3, 10) == "comment"


def test_span_en_string():
    src = 'q = "SELECT * FROM users"\n'
    # "SELECT" ocupa las columnas 5-11, dentro del literal
    assert _ctx(src, "t.py", 1, 5, 11) == "string"


def test_span_en_codigo():
    src = 'password = "abc123"\n'
    assert _ctx(src, "t.py", 1, 0, 8) == "code"


def test_span_que_cruza_string_y_codigo_es_codigo():
    # El span abarca el literal Y el operador +: no está "dentro" del string
    src = 'q = "SELECT * FROM u WHERE id=" + uid\n'
    assert _ctx(src, "t.py", 1, 5, 34) == "code"


def test_linea_sin_mascaras():
    assert _ctx("x = 1\n", "t.py", 1, 0, 5) == "code"


def test_linea_interior_de_docstring_es_string():
    src = '"""doc\ncontenido TODO\n"""\nx = 1\n'
    assert _ctx(src, "t.py", 2, 10, 14) == "string"
