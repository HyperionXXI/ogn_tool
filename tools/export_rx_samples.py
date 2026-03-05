import sqlite3

DB = "ogn_log.sqlite3"
LIMIT = 200

sql = """
SELECT ts_utc, raw
FROM packets
WHERE raw LIKE '%dB%'
ORDER BY ts_utc DESC
LIMIT ?
"""

db = sqlite3.connect(DB)
rows = db.execute(sql, (LIMIT,)).fetchall()
db.close()

with open("samples_rx.txt", "w", encoding="utf-8") as f:
    for ts, raw in rows:
        f.write(f"{ts} {raw}\n")

print("wrote samples_rx.txt", len(rows), "rows")
