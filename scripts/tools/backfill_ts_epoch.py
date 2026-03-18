#!/usr/bin/env python3
"""Backfill ts_epoch in packets table in batches.

Usage:
  python tools/backfill_ts_epoch.py --db F:\Data\ogn\ogn_log.sqlite3 --batch 50000
"""

from __future__ import annotations

import argparse
import datetime as dt
import sqlite3
import time
from typing import Iterable, List, Tuple


def _ensure_column(con: sqlite3.Connection) -> None:
    cols = {row[1] for row in con.execute("PRAGMA table_info(packets)")}
    if "ts_epoch" not in cols:
        con.execute("ALTER TABLE packets ADD COLUMN ts_epoch INTEGER;")
        con.commit()


def _parse_epoch(ts_utc: str) -> int:
    if ts_utc.endswith("Z"):
        ts_utc = ts_utc.replace("Z", "+00:00")
    return int(dt.datetime.fromisoformat(ts_utc).timestamp())


def _fetch_batch(con: sqlite3.Connection, batch: int) -> List[Tuple[int, str]]:
    cur = con.execute(
        "SELECT id, ts_utc FROM packets WHERE ts_epoch IS NULL ORDER BY id LIMIT ?",
        (int(batch),),
    )
    return cur.fetchall()


def _update_batch(con: sqlite3.Connection, rows: Iterable[Tuple[int, str]]) -> int:
    updates = []
    for row_id, ts_utc in rows:
        try:
            updates.append((_parse_epoch(ts_utc), row_id))
        except Exception:
            # Skip rows with unparsable timestamps
            continue
    if not updates:
        return 0
    con.executemany("UPDATE packets SET ts_epoch=? WHERE id=?", updates)
    return len(updates)


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill packets.ts_epoch in batches.")
    ap.add_argument("--db", required=True, help="Path to SQLite DB")
    ap.add_argument("--batch", type=int, default=50000, help="Batch size (rows)")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between batches")
    args = ap.parse_args()

    con = sqlite3.connect(args.db, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        _ensure_column(con)

        total_missing = con.execute("SELECT COUNT(*) FROM packets WHERE ts_epoch IS NULL").fetchone()[0]
        print(f"Missing ts_epoch rows: {total_missing}")
        total_updated = 0
        start = time.time()

        while True:
            batch_rows = _fetch_batch(con, args.batch)
            if not batch_rows:
                break
            con.execute("BEGIN")
            updated = _update_batch(con, batch_rows)
            con.commit()
            total_updated += updated

            elapsed = time.time() - start
            rate = int(total_updated / elapsed) if elapsed > 0 else 0
            remaining = max(total_missing - total_updated, 0)
            eta = int(remaining / rate) if rate > 0 else 0
            print(f"Updated {total_updated}/{total_missing} (rate={rate}/s, eta={eta}s)")

            if args.sleep > 0:
                time.sleep(args.sleep)

        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_epoch ON packets(ts_epoch DESC);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_epoch_dst ON packets(ts_epoch DESC, dst);")
        con.commit()
        print("Backfill complete.")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
