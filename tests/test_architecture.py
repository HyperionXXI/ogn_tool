from __future__ import annotations

from pathlib import Path


APPS_ROOT = Path(__file__).resolve().parents[1] / "apps"


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        yield path


def test_ui_layer_has_no_sql_or_services():
    violations = []

    for path in _iter_py_files(APPS_ROOT):
        if path.name == "debug.py":
            continue
        if path.name == "network_intelligence.py":
            continue
        if path.name == "station_intelligence.py":
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")

        if "sqlite3" in content:
            violations.append((path, "imports sqlite3"))

        if "SELECT " in content or "FROM " in content:
            violations.append((path, "contains SQL query text"))

        if "ogn_tool.services" in content:
            violations.append((path, "imports ogn_tool.services.*"))

        if "ui.viewmodels" in content:
            violations.append((path, "imports ui.viewmodels.*"))

        if "ogn_tool.api" in content:
            violations.append((path, "imports ogn_tool.api.*"))

    assert not violations, "\n".join([f"{p}: {reason}" for p, reason in violations])
