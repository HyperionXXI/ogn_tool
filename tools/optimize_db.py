import os
import sqlite3
import argparse


def main():
    ap = argparse.ArgumentParser(description="Optimize SQLite DB (ANALYZE / PRAGMA optimize / optional VACUUM).")
    ap.add_argument("--db", default=os.getenv("OGN_DB_PATH") or os.getenv("OGN_DB") or "ogn_log.sqlite3")
    ap.add_argument("--vacuum", action="store_true", help="Run VACUUM (may take time).")
    args = ap.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        raise SystemExit(f"DB not found: {db_path}")

    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("ANALYZE;")
        con.execute("PRAGMA optimize;")
        if args.vacuum:
            con.execute("VACUUM;")
        con.commit()
        print(f"Optimized DB: {db_path} (vacuum={args.vacuum})")
    finally:
        con.close()


if __name__ == "__main__":
    main()
