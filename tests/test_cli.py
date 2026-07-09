"""
Tests del CLI (app/cli.py).
"""

import json
import sys

from app.cli import main


def test_export_json_genera_archivo_valido(tmp_path, monkeypatch):
    target = tmp_path / "codigo.py"
    target.write_text('password = "supersecreta123"\n', encoding="utf-8")
    out = tmp_path / "reporte.json"

    monkeypatch.setattr(sys, "argv", ["detech", str(target), "--export-json", str(out)])
    main()

    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert any(a["rule_id"] == "SEC001" for a in data[0]["anomalies"])
