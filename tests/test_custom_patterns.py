"""
Tests de los patrones personalizados del RuleEngine y su clave `scope`
(code | comment | all, con default code).
"""

from app.config.config_manager import ConfigManager
from app.core.rule_engine import RuleEngine

_SOURCE = (
    'print("hola")\n'
    '# print("comentado")\n'
    'x = "print(dentro de string)"\n'
)


def _yaml(scope_line=""):
    return (
        "custom_patterns:\n"
        "  - id: CUS001\n"
        "    name: prohibido-print\n"
        "    pattern: 'print\\('\n"
        "    severity: warning\n"
        "    message: uso de print\n"
        + scope_line
    )


def _analyze(tmp_path, yaml_text):
    (tmp_path / "detech.yaml").write_text(yaml_text, encoding="utf-8")
    target = tmp_path / "ejemplo.py"
    target.write_text(_SOURCE, encoding="utf-8")
    result = RuleEngine(ConfigManager(tmp_path)).analyze_file(target)
    return [a.line for a in result.anomalies if a.rule_id == "CUS001"]


def test_scope_por_defecto_es_code(tmp_path):
    # Sin clave scope: solo el print vivo de la línea 1; ni el comentario
    # ni el literal de string deben matchear
    assert _analyze(tmp_path, _yaml()) == [1]


def test_scope_comment_solo_comentarios(tmp_path):
    assert _analyze(tmp_path, _yaml("    scope: comment\n")) == [2]


def test_scope_all_no_filtra(tmp_path):
    assert _analyze(tmp_path, _yaml("    scope: all\n")) == [1, 2, 3]


def test_scope_invalido_cae_a_code(tmp_path):
    assert _analyze(tmp_path, _yaml("    scope: bogus\n")) == [1]
