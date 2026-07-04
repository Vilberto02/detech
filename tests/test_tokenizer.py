"""
Tests para el Tokenizer de DETECH.
"""

# pyrefly: ignore [missing-import]
import pytest
from pathlib import Path

from app.core.tokenizer import tokenize_source, get_lines, NAME_TOKEN, COMMENT_TOKEN, KEYWORD_TOKEN


SIMPLE_CODE = '''
def hola_mundo(nombre):
    """Saluda al usuario."""
    print(f"Hola, {nombre}!")

x = 42
# Este es un comentario
'''


def test_tokenize_returns_tokens():
    tokens = tokenize_source(SIMPLE_CODE)
    assert len(tokens) > 0


def test_tokenize_finds_def():
    tokens = tokenize_source(SIMPLE_CODE, filepath="test.py")
    names = [t.string for t in tokens if t.type == NAME_TOKEN]
    keywords = [t.string for t in tokens if t.type == KEYWORD_TOKEN]
    assert "def" in keywords
    assert "hola_mundo" in names


def test_tokenize_finds_comments():
    tokens = tokenize_source(SIMPLE_CODE, filepath="test.py")
    comments = [t for t in tokens if t.type == COMMENT_TOKEN]
    assert len(comments) >= 1
    assert any("comentario" in c.string for c in comments)


def test_get_lines():
    lines = get_lines(SIMPLE_CODE)
    assert isinstance(lines, list)
    assert any("def" in l for l in lines)


def test_tokenize_empty_string():
    tokens = tokenize_source("")
    assert isinstance(tokens, list)


def test_tokenize_syntax_error_resilient():
    """El tokenizador debe manejar archivos con errores sin lanzar excepción."""
    broken = "def sin_cerrar(\n    x = 1"
    tokens = tokenize_source(broken)
    assert isinstance(tokens, list)
