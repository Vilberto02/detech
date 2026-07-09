"""
Tests unitarios del SecurityDetector (SEC001, SEC002, SEC003).
"""

from app.config.config_manager import ConfigManager
from app.core.tokenizer import tokenize_source
from app.detectors.security import SecurityDetector


def _detect(source: str, filename: str = "t.py"):
    det = SecurityDetector(ConfigManager())
    return det.detect(filename, source.splitlines(), tokenize_source(source, filename), {})


def _by_rule(anomalies, rule_id):
    return [a for a in anomalies if a.rule_id == rule_id]


# ---------------------------------------------------------------------------
# SEC002 — funciones peligrosas
# ---------------------------------------------------------------------------

def test_input_no_es_funcion_peligrosa():
    # En Python 3 input() devuelve str; marcarlo era un falso positivo
    found = _by_rule(_detect('nombre = input("Nombre: ")\n'), "SEC002")
    assert found == []


def test_eval_sigue_siendo_critical():
    found = _by_rule(_detect("x = eval(datos)\n"), "SEC002")
    assert len(found) == 1
    assert found[0].severity == "critical"


def test_compile_baja_a_warning():
    # compile() no ejecuta código por sí mismo: sospechoso, no crítico
    found = _by_rule(_detect("c = compile(src, '<s>', 'exec')\n"), "SEC002")
    assert len(found) == 1
    assert found[0].severity == "warning"


# ---------------------------------------------------------------------------
# SEC001 — credenciales hardcodeadas
# ---------------------------------------------------------------------------

def test_detecta_secret_key_con_prefijo():
    found = _by_rule(_detect('aws_secret_key = "AKIAIOSFODNN7EXAMPLE"\n'), "SEC001")
    assert len(found) == 1
    assert found[0].severity == "critical"


def test_detecta_password_simple():
    found = _by_rule(_detect('db_password = "super_secreta_123"\n'), "SEC001")
    assert len(found) == 1


# ---------------------------------------------------------------------------
# SEC003 — inyección SQL
# ---------------------------------------------------------------------------

def test_detecta_sql_en_fstring_interpolada():
    src = "query = f\"UPDATE users SET role = 'admin' WHERE id = '{uid}'\"\n"
    found = _by_rule(_detect(src), "SEC003")
    assert len(found) == 1


def test_fstring_sql_sin_interpolacion_no_reporta():
    # Sin llaves no hay interpolación y por tanto no hay inyección
    src = 'query = f"SELECT version"\n'
    assert _by_rule(_detect(src), "SEC003") == []


def test_detecta_sql_por_concatenacion():
    src = "query = \"SELECT * FROM usuarios WHERE nombre = '\" + nombre + \"'\"\n"
    found = _by_rule(_detect(src), "SEC003")
    assert len(found) == 1
