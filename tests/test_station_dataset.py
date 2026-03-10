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
        limit_rows=10,
        station_id="FK50887",
    )

    assert isinstance(df, pd.DataFrame)
