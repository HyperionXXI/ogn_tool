import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def _load_collector():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "collector.py"
    spec = importlib.util.spec_from_file_location("ogn_tool_collector", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestDbSchema(unittest.TestCase):
    def test_db_schema_version_table(self):
        collector = _load_collector()
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.sqlite3"
            con = collector.db_connect(str(db_path))
            try:
                tables = {
                    row[0]
                    for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                }
                self.assertIn("packets", tables)
                self.assertIn("meta", tables)

                row = con.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], str(collector.SCHEMA_VERSION))
            finally:
                con.close()
