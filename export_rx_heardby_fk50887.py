import sqlite3

DB = "ogn_log.sqlite3"
IGATE = "FK50887"
LIMIT = 5000

# Optionnel: ignorer les beacons de type Name="..."
EXCLUDE_NAME_BEACONS = False

sql = """
SELECT ts_utc, src, dst, qas, lat, lon, raw
FROM packets
WHERE raw LIKE '%,' || ? || ':%'
ORDER BY ts_utc DESC
LIMIT ?
"""

db = sqlite3.connect(DB)
rows = db.execute(sql, (IGATE, LIMIT)).fetchall()
db.close()

out = f"samples_rx_{IGATE}.txt"
kept = 0
with open(out, "w", encoding="utf-8") as f:
    for ts, src, dst, qas, lat, lon, raw in rows:
        if EXCLUDE_NAME_BEACONS and 'Name="' in raw:
            continue
        f.write(f"{ts} {src}>{dst} qas={qas} lat={lat} lon={lon} {raw}\n")
        kept += 1

print("wrote", out, kept, "rows")