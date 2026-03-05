import importlib.util
import math
import unittest
from pathlib import Path


def _load_collector():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "collector.py"
    spec = importlib.util.spec_from_file_location("ogn_tool_collector", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class TestCollectorParsing(unittest.TestCase):
    def test_parse_position_uncompressed(self):
        collector = _load_collector()
        body = "4903.50N/07201.75W"
        lat, lon = collector.parse_position(body)
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        self.assertTrue(math.isclose(lat, 49.058333, rel_tol=0, abs_tol=1e-6))
        self.assertTrue(math.isclose(lon, -72.029167, rel_tol=0, abs_tol=1e-6))

    def test_parse_path_qas_and_igate(self):
        collector = _load_collector()
        qas, igate = collector.parse_path("TCPIP*,qAS,FK50887")
        self.assertEqual(qas, "qAS")
        self.assertEqual(igate, "FK50887")

    def test_parse_path_qax_len4(self):
        collector = _load_collector()
        qas, igate = collector.parse_path("TCPIP*,qARX,IGATE1")
        self.assertEqual(qas, "qARX")
        self.assertEqual(igate, "IGATE1")

    def test_parse_line_full(self):
        collector = _load_collector()
        line = "SRC>OGNFNT,TCPIP*,qAS,FK50887:4903.50N/07201.75W test"
        pkt = collector.parse_line(line)
        self.assertIsNotNone(pkt)
        self.assertEqual(pkt["src"], "SRC")
        self.assertEqual(pkt["dst"], "OGNFNT")
        self.assertEqual(pkt["igate"], "FK50887")
        self.assertEqual(pkt["qas"], "qAS")
        self.assertTrue(math.isclose(pkt["lat"], 49.058333, rel_tol=0, abs_tol=1e-6))
        self.assertTrue(math.isclose(pkt["lon"], -72.029167, rel_tol=0, abs_tol=1e-6))
