from __future__ import annotations

from pathlib import Path


APPS_ROOT = Path(__file__).resolve().parents[1] / "apps"


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        yield path


def test_ui_layer_has_no_sql_or_repos():
    violations = []

    for path in _iter_py_files(APPS_ROOT):
        content = path.read_text(encoding="utf-8", errors="ignore")

        if "sqlite3" in content:
            violations.append((path, "imports sqlite3"))

        if "SELECT " in content or "FROM " in content:
            violations.append((path, "contains SQL query text"))

        if "ogn_tool.data" in content:
            violations.append((path, "imports ogn_tool.data.*"))

        if "ogn_tool.services" in content:
            continue

        if "ogn_tool." in content:
            # If any ogn_tool import exists, it must be services
            lines = [line.strip() for line in content.splitlines() if "ogn_tool." in line]
            for line in lines:
                if "ogn_tool.services" not in line:
                    violations.append((path, f"imports non-service: {line}"))

    assert not violations, "\n".join([f"{p}: {reason}" for p, reason in violations])
