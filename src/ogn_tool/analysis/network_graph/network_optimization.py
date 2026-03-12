from __future__ import annotations

from typing import Any


def estimate_station_gain(lat: float, lon: float, graph: dict) -> float:
    blind = ((graph.get("metrics") or {}).get("blind_zones") or {}).get("grid_cells") or []
    if not blind:
        return 0.0
    gain = 0.0
    for grid_id in blind:
        try:
            grid_lat_s, grid_lon_s = str(grid_id).split(":", 1)
            grid_lat = float(grid_lat_s)
            grid_lon = float(grid_lon_s)
        except Exception:
            continue
        gain += 1.0 / (1.0 + abs(grid_lat - float(lat)) + abs(grid_lon - float(lon)))
    return float(gain)


def optimize_station_locations(graph: dict) -> list[dict[str, Any]]:
    suggestions = []
    blind = ((graph.get("metrics") or {}).get("blind_zones") or {}).get("grid_cells") or []
    for grid_id in blind:
        try:
            grid_lat_s, grid_lon_s = str(grid_id).split(":", 1)
            lat = float(grid_lat_s)
            lon = float(grid_lon_s)
        except Exception:
            continue
        suggestions.append({
            "lat": lat,
            "lon": lon,
            "estimated_gain": estimate_station_gain(lat, lon, graph),
        })
    suggestions.sort(key=lambda item: item["estimated_gain"], reverse=True)
    return suggestions


def suggest_station_locations(graph: dict, k: int = 5) -> list[dict[str, Any]]:
    return optimize_station_locations(graph)[: max(0, int(k))]


__all__ = ["optimize_station_locations", "estimate_station_gain", "suggest_station_locations"]
