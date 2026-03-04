# tools/rx_stats.py
import sqlite3, re, datetime

DB = "ogn_log.sqlite3"
IGATE = "FK50887"

re_db = re.compile(r'([+-]?\d+(?:\.\d+)?)dB\b')

def since(hours: int) -> str:
    t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    return t.isoformat()

def main():
    db = sqlite3.connect(DB)
    cut6 = since(6)
    cut24 = since(24)

    def count(where: str, params=()):
        return db.execute(f"SELECT COUNT(*) FROM packets WHERE {where}", params).fetchone()[0]

    rx6   = count("raw LIKE ? AND ts_utc >= ?", (f"%,{IGATE}:%", cut6))
    rx24  = count("raw LIKE ? AND ts_utc >= ?", (f"%,{IGATE}:%", cut24))
    rx6db = count("raw LIKE ? AND raw LIKE ? AND ts_utc >= ?", (f"%,{IGATE}:%", "%dB%", cut6))

    with_latlon_6 = count("raw LIKE ? AND ts_utc >= ? AND lat IS NOT NULL AND lon IS NOT NULL",
                          (f"%,{IGATE}:%", cut6))

    print(f"DB={DB}")
    print(f"RX heard-by {IGATE} last 6h  : {rx6}")
    print(f"RX heard-by {IGATE} last 24h : {rx24}")
    print(f"RX (contains dB) last 6h     : {rx6db}")
    print(f"RX (has lat/lon) last 6h     : {with_latlon_6}")

    # quick dB distribution sample (last 6h)
    rows = db.execute(
        "SELECT raw FROM packets WHERE raw LIKE ? AND raw LIKE ? AND ts_utc >= ? LIMIT 20000",
        (f"%,{IGATE}:%", "%dB%", cut6)
    ).fetchall()

    vals = []
    for (raw,) in rows:
        m = re_db.search(raw or "")
        if m:
            vals.append(float(m.group(1)))

    if vals:
        vals.sort()
        def pct(p):
            i = int(round((p/100)*(len(vals)-1)))
            return vals[i]
        print(f"dB sample parsed={len(vals)} (from <=20000 rows)")
        print(f"dB min={vals[0]:.1f}  p10={pct(10):.1f}  p50={pct(50):.1f}  p90={pct(90):.1f}  max={vals[-1]:.1f}")
    else:
        print("No dB values parsed in sample.")

    db.close()

if __name__ == "__main__":
    main()