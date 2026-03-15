import sqlite3

import pandas as pd

from ogn_tool.services import rf_analysis_service


def test_station_dataset_not_empty(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_epoch INTEGER,
            src TEXT,
            dst TEXT,
            igate TEXT,
            lat REAL,
            lon REAL,
            raw TEXT
        )
        """
    )
    con.commit()
    con.close()

    df = rf_analysis_service.load_rf_receptions(
        db_path=str(db_path),
        since_epoch=0,
        end_epoch=None,
        limit_rows=10,
        station_id="FK50887",
    )

    assert isinstance(df, pd.DataFrame)


def test_station_dataset_respects_end_epoch(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE packets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_epoch INTEGER,
            src TEXT,
            dst TEXT,
            igate TEXT,
            lat REAL,
            lon REAL,
            raw TEXT
        )
        """
    )
    con.executemany(
        "INSERT INTO packets (ts_epoch, src, dst, igate, lat, lon, raw) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (100, "a", "b", "FK50887", 47.0, 7.0, "p1"),
            (200, "a", "b", "FK50887", 47.0, 7.0, "p2"),
            (300, "a", "b", "FK50887", 47.0, 7.0, "p3"),
        ],
    )
    con.commit()
    con.close()

    df = rf_analysis_service.load_rf_receptions(
        db_path=str(db_path),
        since_epoch=150,
        end_epoch=250,
        limit_rows=10,
        station_id="FK50887",
    )

    assert df["ts_epoch"].tolist() == [200]
