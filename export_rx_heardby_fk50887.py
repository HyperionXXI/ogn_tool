import sqlite3

DB = "ogn_log.sqlite3"
IGATE = "FK50887"
LIMIT = 5000

sql = """
SELECT ts_utc, src, dst, raw
FROM packets
WHERE raw LIKE '%,qA%,%'
  AND raw LIKE '%,' || ? || ':%'
ORDER BY ts_utc DESC
LIMIT ?
"""

db = sqlite3.connect(DB)
rows = db.execute(sql, (IGATE, LIMIT)).fetchall()
db.close()

out = "samples_rx_fk50887.txt"
with open(out, "w", encoding="utf-8") as f:
    for ts, src, dst, raw in rows:
        f.write(f"{ts} {src}>{dst} {raw}\n")

print("wrote", out, len(rows), "rows")
