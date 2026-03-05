import re
import sqlite3

DB = "ogn_log.sqlite3"
S = "FK50887"

RE_IGATE = re.compile(r",qA.{1,2},([^:,]+):")


def igate_from_raw(raw: str):
    m = RE_IGATE.search(raw or "")
    return m.group(1) if m else None


db = sqlite3.connect(DB)

print("count,last =", db.execute("select count(*), max(ts_utc) from packets").fetchone())

print("igate FK50887 rows =", db.execute("select count(*) from packets where igate=?", (S,)).fetchone()[0])
print(
    "heard-by FK50887 rows (raw contains ,qA?,FK50887:) =",
    db.execute("select count(*) from packets where raw like ?", (f"%,qA%,{S}:%",)).fetchone()[0],
)
print("src FK50887 rows =", db.execute("select count(*) from packets where src=?", (S,)).fetchone()[0])

rows = db.execute("select ts_utc,dst,raw from packets where src=? order by ts_utc desc limit 20", (S,)).fetchall()
print("\n--- last 20 src=FK50887 ---")
for ts, dst, raw in rows:
    print(ts, dst, raw[:140])

rows = db.execute(
    "select ts_utc,src,raw from packets where raw like ? and src<>? order by ts_utc desc limit 20",
    (f"%,qA%,{S}:%", S),
).fetchall()
print(f"\n--- last 20 heard-by {S} (fallback parse) ---")
for ts, src, raw in rows:
    print(ts, src, igate_from_raw(raw), raw[:140])

db.close()