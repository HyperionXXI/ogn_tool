# tools/export_rx_csv.py
import sqlite3, re, csv, datetime, argparse

re_db = re.compile(r'([+-]?\d+(?:\.\d+)?)dB\b')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="ogn_log.sqlite3")
    ap.add_argument("--igate", default="FK50887")
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--limit", type=int, default=200000)
    ap.add_argument("--out", default="rx_fk50887_db.csv")
    args = ap.parse_args()

    cut = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=args.hours)).isoformat()

    db = sqlite3.connect(args.db)
    q = """
    SELECT ts_utc, src, dst, qas, igate, lat, lon, raw
    FROM packets
    WHERE raw LIKE ?
      AND ts_utc >= ?
    ORDER BY ts_utc DESC
    LIMIT ?
    """
    rows = db.execute(q, (f"%,{args.igate}:%", cut, args.limit)).fetchall()

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ts_utc","src","dst","qas","igate","lat","lon","db","raw"])
        n_db = 0
        for ts,src,dst,qas,igate,lat,lon,raw in rows:
            m = re_db.search(raw or "")
            dbval = float(m.group(1)) if m else ""
            if m: n_db += 1
            w.writerow([ts,src,dst,qas,igate,lat,lon,dbval,raw])

    db.close()
    print(f"wrote {args.out} rows={len(rows)} rows_with_db={n_db} since={cut}")

if __name__ == "__main__":
    main()