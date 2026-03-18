from __future__ import annotations

import pandas as pd


def compute_shadow_proxy(grid: pd.DataFrame, packets_threshold: int = 3) -> pd.DataFrame:
    if grid is None or grid.empty:
        return grid

    grid = grid.copy()
    grid["coverage"] = grid["packets"] > packets_threshold
    grid["shadow"] = ~grid["coverage"]
    return grid
