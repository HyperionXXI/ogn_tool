"""
query.py — small diagnostics for ogn_log.sqlite3

Usage:
  python query.py
"""

import re
import sqlite3

DB = "ogn_log.sqlite3"
STATION = "FK50887"

HEARD_RE = re.compile(rf",qA..,{re.escape(STATION)}(?=,|:|$)")


def main():
    c = sqlite3.connect(DB)
    try:
        total = c.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
        with_pos = c.execute("SELECT COUNT(*) FROM packets WHERE lat IS NOT NULL AND lon IS NOT NULL").fetchone()[0]
        print("Total packets:", total)
        print("With positions:", with_pos)

        print("\nTop iGates:")
        for ig, n in c.execute(
            "SELECT COALESCE(NULLIF(igate,''),'(none)') ig, COUNT(*) FROM packets GROUP BY ig ORDER BY COUNT(*) DESC LIMIT 20"
        ):
            print(f"  {ig!s:20} {n}")

        # Heard-by FK50887 (ANY qA??)
        rows = c.execute("SELECT COUNT(*) FROM packets WHERE raw LIKE ?", (f"%{STATION}%",)).fetchone()[0]
        heard = 0
        for (raw,) in c.execute("SELECT raw FROM packets WHERE raw LIKE ? AND raw NOT LIKE ?", (f"%{STATION}%", f"{STATION}>%")):
            if HEARD_RE.search(raw):
                heard += 1

        print(f"\nRows containing {STATION} (anywhere) :", rows)
        print(f"Rows tagged heard-by {STATION} (qA??,{STATION}) :", heard)

    finally:
        c.close()


if __name__ == "__main__":
    main()