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


def test_constantes_no_son_credenciales():
    # Dogfooding: NAME_TOKEN = "NAME" no es una credencial; el valor es
    # una palabra corta puramente alfabética (sin dígitos ni símbolos)
    src = 'NAME_TOKEN = "NAME"\nCOMMENT_TOKEN = "COMMENT"\nSTRING_TOKEN = "STRING"\n'
    assert _by_rule(_detect(src), "SEC001") == []


def test_nombres_compuestos_son_credenciales():
    # Regresión del experimento con \b: el keyword suele ser SUFIJO de un
    # identificador compuesto (db_password, PaymentGatewayToken). Un límite
    # de palabra a la izquierda perdería estos 5 verdaderos positivos, que
    # son léxicamente idénticos a NAME_TOKEN: la diferencia está en el VALOR,
    # y de eso se encarga el filtro de plausibilidad.
    casos = [
        'db_password = "super_secreta_123"\n',
        'aws_secret_key = "AKIAIOSFODNN7EXAMPLE"\n',
        'master_passwd = "Tr0ub4dor&3"\n',
        'PaymentGatewayToken = "pk_live_9x8y7z"\n',
        'dbSecret = "s3cr3t_v4lu3"\n',
    ]
    for caso in casos:
        assert len(_by_rule(_detect(caso), "SEC001")) == 1, caso


def test_token_simple_con_digitos_es_credencial():
    found = _by_rule(_detect('token = "abc123"\n'), "SEC001")
    assert len(found) == 1


def test_valor_corto_con_digitos_si_es_credencial():
    found = _by_rule(_detect('token = "ab12cd"\n'), "SEC001")
    assert len(found) == 1


def test_valor_alfabetico_largo_si_es_credencial():
    found = _by_rule(_detect('password = "supersecretlarga"\n'), "SEC001")
    assert len(found) == 1


def test_filtro_no_suprime_password_corta_con_digito():
    # "hunter2" tiene 7 caracteres pero contiene un dígito: debe reportarse
    found = _by_rule(_detect('password = "hunter2"\n'), "SEC001")
    assert len(found) == 1


def test_filtro_no_suprime_api_key_con_guiones():
    found = _by_rule(_detect('API_KEY = "sk-proj-aB3xK9"\n'), "SEC001")
    assert len(found) == 1


def test_filtro_no_suprime_token_con_prefijo_ghp():
    found = _by_rule(_detect('token = "ghp_16C7e42F"\n'), "SEC001")
    assert len(found) == 1


# ---------------------------------------------------------------------------
# SEC001 — contexto léxico (máscaras de comentario/string)
# ---------------------------------------------------------------------------

def test_credencial_en_comentario_python_no_reporta():
    assert _by_rule(_detect('# password = "abc12345"\n'), "SEC001") == []


def test_credencial_en_comentario_js_no_reporta():
    # El filtro anterior solo reconocía '#'; los comentarios // pasaban
    assert _by_rule(_detect('// api_key = "xyz12345"\n', "t.js"), "SEC001") == []


def test_credencial_en_comentario_al_final_de_linea_no_reporta():
    assert _by_rule(_detect('x = 1  # password = "abc123"\n'), "SEC001") == []


def test_credencial_dentro_de_docstring_no_reporta():
    src = '"""Ejemplo de uso:\n    password = "abc123"\n"""\n'
    assert _by_rule(_detect(src), "SEC001") == []


def test_credencial_en_codigo_con_comentario_al_lado_si_reporta():
    found = _by_rule(_detect('password = "abc123"  # credencial real\n'), "SEC001")
    assert len(found) == 1


# ---------------------------------------------------------------------------
# SEC003 — contexto léxico
# ---------------------------------------------------------------------------

def test_sql_en_comentario_python_no_reporta():
    src = '# query = "SELECT * FROM users WHERE id=" + uid\n'
    assert _by_rule(_detect(src), "SEC003") == []


def test_sql_en_comentario_js_no_reporta():
    src = '// query = "SELECT * FROM users WHERE id=" + uid;\n'
    assert _by_rule(_detect(src, "t.js"), "SEC003") == []


def test_string_sql_inofensivo_no_reporta():
    assert _by_rule(_detect('q = "SELECT * FROM users"\n'), "SEC003") == []


def test_sql_con_formato_dentro_de_string_sigue_reportandose():
    # sprintf al estilo C: el %s vulnerable vive DENTRO del literal. Por eso
    # SEC003 solo descarta contexto comentario, nunca contexto string.
    src = 'sprintf(query, "SELECT * FROM t WHERE id = \'%s\'", buf);\n'
    found = _by_rule(_detect(src, "t.c"), "SEC003")
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
