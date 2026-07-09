"""
Tests de integración para los detectores de DETECH.
Usa el fixture 'ejemplo_anomalias.py' que contiene anomalías conocidas.
"""

# pyrefly: ignore [missing-import]
import pytest
from pathlib import Path

from app.core.rule_engine import RuleEngine
from app.config.config_manager import ConfigManager
from app.core.models import Report

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ejemplo_anomalias.py"


@pytest.fixture
def engine():
    config = ConfigManager()
    return RuleEngine(config)


@pytest.fixture
def file_result(engine):
    return engine.analyze_file(FIXTURE_PATH)


class TestFileResult:
    def test_has_anomalies(self, file_result):
        """El fixture contiene anomalías conocidas, debe detectar al menos una."""
        assert file_result.total_anomalies > 0

    def test_has_critical(self, file_result):
        """Debe detectar anomalías críticas (credenciales, eval, SQL)."""
        assert file_result.critical_count > 0

    def test_filepath_preserved(self, file_result):
        assert str(FIXTURE_PATH) in file_result.filepath


class TestSecurityDetector:
    def test_detects_hardcoded_credentials(self, file_result):
        sec_anomalies = [a for a in file_result.anomalies if a.rule_id == "SEC001"]
        assert len(sec_anomalies) >= 1, "Debe detectar credencial hardcodeada"

    def test_detects_eval(self, file_result):
        eval_anomalies = [a for a in file_result.anomalies if a.rule_id == "SEC002"]
        assert len(eval_anomalies) >= 1, "Debe detectar uso de eval()"

    def test_detects_sql_injection(self, file_result):
        sql_anomalies = [a for a in file_result.anomalies if a.rule_id == "SEC003"]
        assert len(sql_anomalies) >= 1, "Debe detectar concatenacion SQL"


class TestComplexityDetector:
    def test_detects_too_many_params(self, file_result):
        param_anomalies = [a for a in file_result.anomalies if a.rule_id == "CPX003"]
        assert len(param_anomalies) >= 1, "Debe detectar funcion con demasiados parametros"

    def test_cpx001_reporta_por_funcion(self):
        from app.detectors.complexity import ComplexityDetector
        det = ComplexityDetector(ConfigManager())
        metrics = {
            "cyclomatic_complexity": 25,
            "functions": [
                {"name": "compleja", "start_line": 10, "end_line": 40,
                 "length": 31, "param_count": 2, "cyclomatic_complexity": 15},
                {"name": "simple", "start_line": 50, "end_line": 55,
                 "length": 6, "param_count": 0, "cyclomatic_complexity": 2},
            ],
        }
        found = [a for a in det.detect("t.py", [], [], metrics) if a.rule_id == "CPX001"]
        assert len(found) == 1, "Solo la funcion compleja debe reportarse"
        assert found[0].line == 10
        assert "compleja" in found[0].message

    def test_cpx001_archivo_sin_funciones_usa_metrica_global(self):
        from app.detectors.complexity import ComplexityDetector
        det = ComplexityDetector(ConfigManager())
        metrics = {"cyclomatic_complexity": 25, "functions": []}
        found = [a for a in det.detect("t.py", [], [], metrics) if a.rule_id == "CPX001"]
        assert len(found) == 1
        assert found[0].line == 1


class TestDeadCodeDetector:
    def test_detects_annotations(self, file_result):
        todo_anomalies = [a for a in file_result.anomalies if a.rule_id == "DCO001"]
        assert len(todo_anomalies) >= 2, "Debe detectar TODO y FIXME"

    def test_detects_commented_code(self, file_result):
        commented = [a for a in file_result.anomalies if a.rule_id == "DCO002"]
        assert len(commented) >= 1, "Debe detectar bloque de codigo comentado"

    def _dco003(self, source):
        from app.detectors.dead_code import DeadCodeDetector
        from app.core.tokenizer import tokenize_source
        from app.core.metrics import count_imports
        det = DeadCodeDetector(ConfigManager())
        tokens = tokenize_source(source, "t.py")
        metrics = {"imports": count_imports(tokens)}
        found = det.detect("t.py", source.splitlines(), tokens, metrics)
        return [a for a in found if a.rule_id == "DCO003"]

    def test_from_import_usado_no_reporta_dco003(self):
        src = 'from pathlib import Path\n\np = Path(".")\n'
        assert self._dco003(src) == []

    def test_from_import_no_usado_reporta_dco003(self):
        src = "from pathlib import Path\n\nx = 1\n"
        assert len(self._dco003(src)) == 1

    def _dco(self, source, rule_id, filename="t.py"):
        from app.detectors.dead_code import DeadCodeDetector
        from app.core.tokenizer import tokenize_source
        det = DeadCodeDetector(ConfigManager())
        tokens = tokenize_source(source, filename)
        found = det.detect(filename, source.splitlines(), tokens, {})
        return [a for a in found if a.rule_id == rule_id]

    def test_dco001_todo_en_comentario_python(self):
        assert len(self._dco("# TODO: arreglar esto\n", "DCO001")) == 1

    def test_dco001_fixme_en_comentario_js(self):
        assert len(self._dco("// FIXME: revisar\n", "DCO001", "t.js")) == 1

    def test_dco001_todo_en_string_no_reporta(self):
        # 'TODO' como dato (no como anotación pendiente) no debe contar
        assert self._dco('msg = "TODO list"\n', "DCO001") == []

    def test_dco001_todo_en_docstring_no_reporta(self):
        src = '"""\nTODO: documentar la API\n"""\nx = 1\n'
        assert self._dco(src, "DCO001") == []

    def test_dco002_codigo_comentado_real_reporta(self):
        src = "# import os\n# import sys\n# import json\nx = 1\n"
        assert len(self._dco(src, "DCO002")) == 1

    def test_dco002_docstring_con_ejemplos_no_reporta(self):
        # Un docstring que muestra código de ejemplo no es código comentado
        src = '"""\n# import os\n# import sys\n# import json\n"""\nx = 1\n'
        assert self._dco(src, "DCO002") == []


class TestLegibilityDetector:
    def test_detects_long_lines(self, file_result):
        long_line = [a for a in file_result.anomalies if a.rule_id == "LEG003"]
        assert len(long_line) >= 1, "Debe detectar lineas largas"

    def test_detects_long_function(self, file_result):
        long_func = [a for a in file_result.anomalies if a.rule_id == "LEG001"]
        assert len(long_func) >= 1, "Debe detectar funcion muy larga"


class TestReport:
    def test_report_aggregation(self, engine):
        report = Report()
        result = engine.analyze_file(FIXTURE_PATH)
        report.files.append(result)
        assert report.total_anomalies == result.total_anomalies
        assert report.critical_count == result.critical_count
