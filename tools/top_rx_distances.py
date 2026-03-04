# tools/top_rx_distances.py
import sqlite3, math, re, datetime, argparse

re_db = re.compile(r'([+-]?\d+(?:\.\d+)?)dB\b')

def hav_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.pi/180.0
    dlat = (lat2-lat1)*p
    dlon = (lon2-lon1)*p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="ogn_log.sqlite3")
    ap.add_argument("--igate", default="FK50887")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--home-lat", type=float, default=47.33593787391701)
    ap.add_argument("--home-lon", type=float, default=7.272825467967339)
    args = ap.parse_args()

    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=args.hours)).isoformat()
    db = sqlite3.connect(args.db)

    rows = db.execute("""
        SELECT src, lat, lon, ts_utc, raw
        FROM packets
        WHERE raw LIKE ?
          AND ts_utc >= ?
          AND lat IS NOT NULL AND lon IS NOT NULL
        """, (f"%,{args.igate}:%", cut)).fetchall()

    best = {}  # src -> (dist, ts, db, lat, lon)
    for src, lat, lon, ts, raw in rows:
        lat = float(lat); lon = float(lon)
        dist = hav_km(args.home_lat, args.home_lon, lat, lon)
        m = re_db.search(raw or "")
        dbval = float(m.group(1)) if m else None
        cur = best.get(src)
        if cur is None or dist > cur[0]:
            best[src] = (dist, ts, dbval, lat, lon, (raw or "")[:120])

    top = sorted(best.items(), key=lambda kv: kv[1][0], reverse=True)[:args.top]
    print(f"heard-by {args.igate} since {cut}  unique_src={len(best)}  rows={len(rows)}")
    for src,(d,ts,dbval,lat,lon,raw120) in top:
        dbs = f"{dbval:.1f}dB" if dbval is not None else "n/a"
        print(f"{d:7.2f} km  {dbs:8s}  {src:10s}  {ts}  ({lat:.5f},{lon:.5f})  {raw120}")

    db.close()

if __name__ == "__main__":
    main()