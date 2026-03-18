import sqlite3

db = sqlite3.connect("ogn_log.sqlite3")

sql = """
select count(*)
from packets
where raw like '%,FK50887:%'
and raw like '%dB%'
and ts_utc > datetime('now','-6 hours')
"""

print(db.execute(sql).fetchone())

db.close()