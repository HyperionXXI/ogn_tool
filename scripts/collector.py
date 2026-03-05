#!/usr/bin/env python3
"""OGN/APRS-IS collector -> SQLite.

Key points (based on issues observed):
- APRS-IS q-construct token is typically 3 chars (qAS/qAC/qAR/qAO/...).
  Some tools sometimes emit 4 chars (rare). We accept both.
- The 'igate' (a.k.a. "heard-by") is the callsign right after the qA? token
  in the path, e.g.  "...,qAS,FK50887:" -> igate=FK50887.

Env vars:
  OGN_HOST   default glidern5.glidernet.org
  OGN_PORT   default 14580
  OGN_DB     default ogn_log.sqlite3
  OGN_FILTER default ''
  OGN_DEBUG  default '0'

This collector stores raw packets and parsed fields useful for analysis.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import socket
import sqlite3
from typing import Any, Dict, Iterable, Optional, Tuple


HOST = os.getenv("OGN_HOST", "glidern5.glidernet.org")
PORT = int(os.getenv("OGN_PORT", "14580"))
DB_PATH = os.getenv("OGN_DB", "ogn_log.sqlite3")
FILTER = os.getenv("OGN_FILTER", "")
DEBUG = os.getenv("OGN_DEBUG", "0") not in ("0", "", "false", "False")

# Collector identity for APRS-IS login.
CALLSIGN = os.getenv("OGN_USER", "NOCALL")
PASSCODE = os.getenv("OGN_PASS", "-1")

SOCKET_TIMEOUT_S = 60
COMMIT_EVERY = int(os.getenv("OGN_COMMIT_EVERY", "250"))

# APRS uncompressed position (DDMM.mmN/DDDMM.mmE)
_POS_RE = re.compile(
    r"(?P<latdeg>\d{2})(?P<latmin>\d{2}\.\d{2})(?P<lathem>[NS]).{0,3}"
    r"(?P<londeg>\d{3})(?P<lonmin>\d{2}\.\d{2})(?P<lonhem>[EW])"
)

# q-construct token: usually 3 chars (qAS/qAC/qAR/...), occasionally seen as 4.
_QA_RE = re.compile(r"^qA.{1,2}$")


def _dm_to_deg(deg: str, minutes: str, hem: str) -> float:
    d = int(deg)
    m = float(minutes)
    v = d + m / 60.0
    if hem in ("S", "W"):
        v = -v
    return v


def parse_position(body: str) -> Tuple[Optional[float], Optional[float]]:
    if not body:
        return None, None
    m = _POS_RE.search(body)
    if not m:
        return None, None

    lat = _dm_to_deg(m.group("latdeg"), m.group("latmin"), m.group("lathem"))
    lon = _dm_to_deg(m.group("londeg"), m.group("lonmin"), m.group("lonhem"))

    if abs(lat) < 1e-9 and abs(lon) < 1e-9:
        return None, None

    return lat, lon


def parse_path(path: str) -> Tuple[Optional[str], Optional[str]]:
    if not path:
        return None, None

    parts = [p.strip() for p in path.split(",") if p.strip()]
    qas = None
    igate = None

    for i, p in enumerate(parts):
        if _QA_RE.match(p):
            qas = p
            igate = parts[i + 1] if i + 1 < len(parts) else None
            break

    return qas, igate


def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip("\r\n")
    if not line or line.startswith("#"):
        return None

    if ":" not in line or ">" not in line:
        return None

    head, body = line.split(":", 1)
    if ">" not in head:
        return None

    src, rest = head.split(">", 1)
    src = src.strip()

    if "," in rest:
        dst, path = rest.split(",", 1)
    else:
        dst, path = rest, ""

    dst = dst.strip()
    path = path.strip()

    qas, igate = parse_path(path)
    lat, lon = parse_position(body)

    return {
        "src": src,
        "dst": dst,
        "igate": igate,
        "qas": qas,
        "lat": lat,
        "lon": lon,
        "raw": line,
    }


def db_connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=30)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("PRAGMA temp_store=MEMORY;")
    con.execute("PRAGMA foreign_keys=ON;")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS packets (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc   TEXT    NOT NULL,
            src     TEXT,
            dst     TEXT,
            igate   TEXT,
            qas     TEXT,
            lat     REAL,
            lon     REAL,
            raw     TEXT    NOT NULL
        )
        """
    )

    con.execute("CREATE INDEX IF NOT EXISTS idx_packets_ts    ON packets(ts_utc);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_packets_src   ON packets(src);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_packets_dst   ON packets(dst);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_packets_igate ON packets(igate);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_packets_qas   ON packets(qas);")

    return con


def insert_many(con: sqlite3.Connection, rows: Iterable[Dict[str, Any]]) -> None:
    con.executemany(
        """
        INSERT INTO packets (ts_utc, src, dst, igate, qas, lat, lon, raw)
        VALUES (:ts_utc, :src, :dst, :igate, :qas, :lat, :lon, :raw)
        """,
        rows,
    )


def _login_line() -> str:
    base = f"user {CALLSIGN} pass {PASSCODE} vers ogn_tool 1.1"
    if FILTER:
        base += f" filter {FILTER}"
    return base + "\r\n"


def collect_forever() -> None:
    con = db_connect(DB_PATH)
    pending: list[Dict[str, Any]] = []

    inserted_total = 0
    received_total = 0
    rejected_total = 0

    while True:
        sock: Optional[socket.socket] = None
        f = None
        try:
            print(f"Connecting to {HOST}:{PORT} ...")
            sock = socket.create_connection((HOST, PORT), timeout=SOCKET_TIMEOUT_S)
            sock.settimeout(SOCKET_TIMEOUT_S)

            sock.sendall(_login_line().encode("ascii", "ignore"))
            f = sock.makefile("r", encoding="utf-8", newline="\n", errors="replace")

            print("Logging into SQLite... (Ctrl+C to stop)")
            if DEBUG:
                print(f"[debug] DB={os.path.abspath(DB_PATH)}")
                print(f"[debug] FILTER={FILTER!r} COMMIT_EVERY={COMMIT_EVERY}")

            while True:
                line = f.readline()
                if not line:
                    raise ConnectionError("socket closed")

                received_total += 1
                pkt = parse_line(line)
                if not pkt:
                    rejected_total += 1
                    continue

                pkt["ts_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
                pending.append(pkt)

                if DEBUG and received_total % 250 == 0:
                    print(f"[debug] raw: {pkt['raw']}")

                if len(pending) >= COMMIT_EVERY:
                    insert_many(con, pending)
                    con.commit()
                    inserted_total += len(pending)
                    pending.clear()

                    if DEBUG:
                        print(
                            f"[debug] inserted_total={inserted_total} received_total={received_total} rejected_total={rejected_total}"
                        )

        except KeyboardInterrupt:
            print("\nStopping collector (Ctrl+C).")
            break
        except Exception as e:
            try:
                if pending:
                    insert_many(con, pending)
                    con.commit()
                    inserted_total += len(pending)
                    pending.clear()
            except Exception:
                pass

            print(f"[collector] ERROR: {e!r} -> reconnect in 3s")
            try:
                import time

                time.sleep(3)
            except Exception:
                pass
        finally:
            try:
                if f:
                    f.close()
            except Exception:
                pass
            try:
                if sock:
                    sock.close()
            except Exception:
                pass

    try:
        con.close()
    except Exception:
        pass


if __name__ == "__main__":
    collect_forever()