import math
import os
import re
import sqlite3

import pandas as pd

DB = os.getenv("OGN_DB_PATH") or os.getenv("OGN_DB") or "ogn_log.sqlite3"

HOME_LAT = 47.33593787391701
HOME_LON = 7.272825467967339

re_db = re.compile(r'([+-]?\d+(?:\.\d+)?)dB')

def hav_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p = math.pi/180
    dlat = (lat2-lat1)*p
    dlon = (lon2-lon1)*p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(a))


def load_dataset(hours=24):

    db = sqlite3.connect(DB)

    q = """
    SELECT ts_utc, src, lat, lon, raw
    FROM packets
    WHERE raw LIKE '%,FK50887:%'
      AND lat IS NOT NULL
      AND lon IS NOT NULL
      AND ts_utc > datetime('now', ?)
    """

    rows = db.execute(q, (f"-{hours} hours",)).fetchall()

    data = []

    for ts, src, lat, lon, raw in rows:

        m = re_db.search(raw or "")
        db_val = float(m.group(1)) if m else None

        dist = hav_km(HOME_LAT, HOME_LON, lat, lon)

        data.append({
            "time": ts,
            "src": src,
            "lat": lat,
            "lon": lon,
            "distance_km": dist,
            "db": db_val
        })

    df = pd.DataFrame(data)

    return df
