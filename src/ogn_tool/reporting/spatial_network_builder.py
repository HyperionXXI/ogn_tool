from __future__ import annotations

from dataclasses import dataclass
from math import ceil, cos, floor, radians
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class _Obs:
    lat: float
    lon: float
    timestamp_epoch: int
    seen_by_count: int


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _normalize_observations(observations: Iterable[Mapping[str, Any]]) -> list[_Obs]:
    rows: list[_Obs] = []
    for row in observations:
        if not isinstance(row, Mapping):
            continue
        lat = _to_float(row.get('lat'))
        lon = _to_float(row.get('lon'))
        ts = _to_int(row.get('timestamp_epoch'))
        seen_by = row.get('seen_by')
        seen_by_count = len(seen_by) if isinstance(seen_by, list) else 0

        if lat is None or lon is None or ts is None:
            continue

        rows.append(_Obs(lat=lat, lon=lon, timestamp_epoch=ts, seen_by_count=seen_by_count))
    return rows


def _empty_result(cell_size_km: float, analysis_radius_km: float) -> dict[str, Any]:
    return {
        'grid_meta': {
            'min_lat': None,
            'max_lat': None,
            'min_lon': None,
            'max_lon': None,
            'cell_size_km': float(cell_size_km),
            'analysis_radius_km': float(analysis_radius_km),
            'blind_actionable_neighbor_radius_cells': 2,
            'blind_problematic_activity_radius_cells': 4,
            'blind_problematic_exclusion_radius_cells': 1,
            'blind_density_threshold_source': 'p10_active_density',
            'blind_semantics_version': 'a3',
            'rows': 0,
            'cols': 0,
            'time_window_start_epoch': None,
            'time_window_end_epoch': None,
        },
        'coverage_density': [],
        'unique_coverage': [],
        'shared_coverage': [],
        'blind_zones': [],
        'analysis_mask': [],
        'blind_zones_masked': [],
        'blind_actionable': [],
        'blind_problematic': [],
        'shared_overlap_ratio_active': 0.0,
    }


def _expand_analysis_mask(
    active_cells: set[tuple[int, int]],
    row_count: int,
    col_count: int,
    cell_size_km: float,
    analysis_radius_km: float,
) -> set[tuple[int, int]]:
    if not active_cells:
        return set()

    radius_cells = max(1, int(ceil(analysis_radius_km / cell_size_km)))
    mask: set[tuple[int, int]] = set()

    for r_idx, c_idx in active_cells:
        for dr in range(-radius_cells, radius_cells + 1):
            for dc in range(-radius_cells, radius_cells + 1):
                rr = r_idx + dr
                cc = c_idx + dc
                if 0 <= rr < row_count and 0 <= cc < col_count:
                    mask.add((rr, cc))

    return mask


def _compute_blind_actionable_cells(
    analysis_mask_cells: set[tuple[int, int]],
    density_by_cell: Mapping[tuple[int, int], float],
    row_count: int,
    col_count: int,
    d_min: float = 0.08,
    neighbor_radius_cells: int = 2,
) -> set[tuple[int, int]]:
    actionable: set[tuple[int, int]] = set()

    for r_idx, c_idx in analysis_mask_cells:
        density = density_by_cell.get((r_idx, c_idx), 0.0)
        if density >= d_min:
            continue

        has_active_neighbor = False
        for dr in range(-neighbor_radius_cells, neighbor_radius_cells + 1):
            for dc in range(-neighbor_radius_cells, neighbor_radius_cells + 1):
                if dr == 0 and dc == 0:
                    continue
                rr = r_idx + dr
                cc = c_idx + dc
                if rr < 0 or cc < 0 or rr >= row_count or cc >= col_count:
                    continue
                if density_by_cell.get((rr, cc), 0.0) >= d_min:
                    has_active_neighbor = True
                    break
            if has_active_neighbor:
                break

        if not has_active_neighbor:
            actionable.add((r_idx, c_idx))

    return actionable


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    q_clamped = min(max(q, 0.0), 100.0)
    pos = (len(ordered) - 1) * (q_clamped / 100.0)
    lo = int(floor(pos))
    hi = int(ceil(pos))
    if lo == hi:
        return ordered[lo]
    weight = pos - lo
    return ordered[lo] * (1.0 - weight) + ordered[hi] * weight


def _compute_blind_problematic_cells(
    analysis_mask_cells: set[tuple[int, int]],
    density_by_cell: Mapping[tuple[int, int], float],
    d_min: float,
    activity_radius_cells: int = 4,
    exclusion_radius_cells: int = 1,
) -> set[tuple[int, int]]:
    active_cells = [idx for idx, value in density_by_cell.items() if value >= d_min]
    if not active_cells:
        return set()

    problematic: set[tuple[int, int]] = set()
    for r_idx, c_idx in analysis_mask_cells:
        if density_by_cell.get((r_idx, c_idx), 0.0) >= d_min:
            continue

        nearest_dist: int | None = None
        for rr, cc in active_cells:
            dist = max(abs(rr - r_idx), abs(cc - c_idx))
            if nearest_dist is None or dist < nearest_dist:
                nearest_dist = dist
                if nearest_dist == 0:
                    break

        if nearest_dist is None:
            continue
        if nearest_dist <= exclusion_radius_cells:
            continue
        if nearest_dist <= activity_radius_cells:
            problematic.add((r_idx, c_idx))

    return problematic


def build_spatial_network_features(
    observations: Iterable[Mapping[str, Any]],
    cell_size_km: float = 2.5,
    analysis_radius_km: float = 7.5,
) -> dict[str, Any]:
    """Build additive spatial network features from canonical aircraft observations only."""
    if cell_size_km <= 0:
        raise RuntimeError('cell_size_km must be positive')
    if analysis_radius_km <= 0:
        raise RuntimeError('analysis_radius_km must be positive')

    rows = _normalize_observations(observations)
    if not rows:
        return _empty_result(cell_size_km, analysis_radius_km)

    min_lat = min(row.lat for row in rows)
    max_lat = max(row.lat for row in rows)
    min_lon = min(row.lon for row in rows)
    max_lon = max(row.lon for row in rows)

    center_lat = (min_lat + max_lat) / 2.0
    lat_step = cell_size_km / 110.574
    lon_scale = max(cos(radians(center_lat)), 0.1)
    lon_step = cell_size_km / (111.320 * lon_scale)

    row_count = int(floor((max_lat - min_lat) / lat_step)) + 1
    col_count = int(floor((max_lon - min_lon) / lon_step)) + 1

    counts: dict[tuple[int, int], list[int]] = {}

    for obs in rows:
        r_idx = int(floor((obs.lat - min_lat) / lat_step))
        c_idx = int(floor((obs.lon - min_lon) / lon_step))

        r_idx = min(max(r_idx, 0), row_count - 1)
        c_idx = min(max(c_idx, 0), col_count - 1)

        bucket = counts.setdefault((r_idx, c_idx), [0, 0, 0])
        bucket[0] += 1
        if obs.seen_by_count <= 1:
            bucket[1] += 1
        else:
            bucket[2] += 1

    max_total = max((bucket[0] for bucket in counts.values()), default=0)
    if max_total <= 0:
        return _empty_result(cell_size_km, analysis_radius_km)

    active_cells = {idx for idx, bucket in counts.items() if bucket[0] > 0}
    analysis_mask_cells = _expand_analysis_mask(
        active_cells=active_cells,
        row_count=row_count,
        col_count=col_count,
        cell_size_km=cell_size_km,
        analysis_radius_km=analysis_radius_km,
    )

    density_by_cell: dict[tuple[int, int], float] = {
        idx: bucket[0] / max_total for idx, bucket in counts.items()
    }
    active_density_values = [value for value in density_by_cell.values() if value > 0.0]
    d_min = _percentile(active_density_values, 10.0) if active_density_values else 0.08
    if d_min <= 0.0:
        d_min = 0.08

    blind_actionable_cells = _compute_blind_actionable_cells(
        analysis_mask_cells=analysis_mask_cells,
        density_by_cell=density_by_cell,
        row_count=row_count,
        col_count=col_count,
        d_min=d_min,
        neighbor_radius_cells=2,
    )
    blind_problematic_cells = _compute_blind_problematic_cells(
        analysis_mask_cells=analysis_mask_cells,
        density_by_cell=density_by_cell,
        d_min=d_min,
        activity_radius_cells=4,
        exclusion_radius_cells=1,
    )

    coverage_density: list[dict[str, Any]] = []
    unique_coverage: list[dict[str, Any]] = []
    shared_coverage: list[dict[str, Any]] = []
    blind_zones: list[dict[str, Any]] = []
    analysis_mask: list[dict[str, Any]] = []
    blind_zones_masked: list[dict[str, Any]] = []
    blind_actionable: list[dict[str, Any]] = []
    blind_problematic: list[dict[str, Any]] = []

    for r_idx in range(row_count):
        for c_idx in range(col_count):
            total, unique, shared = counts.get((r_idx, c_idx), [0, 0, 0])

            density = total / max_total
            unique_norm = unique / max_total
            shared_norm = shared / max_total
            blind = 1.0 - density

            cell_center_lat = min_lat + (r_idx + 0.5) * lat_step
            cell_center_lon = min_lon + (c_idx + 0.5) * lon_step

            cell_density = {'lat': cell_center_lat, 'lon': cell_center_lon, 'value': density}
            cell_unique = {'lat': cell_center_lat, 'lon': cell_center_lon, 'value': unique_norm}
            cell_shared = {'lat': cell_center_lat, 'lon': cell_center_lon, 'value': shared_norm}
            cell_blind = {'lat': cell_center_lat, 'lon': cell_center_lon, 'value': blind}

            coverage_density.append(cell_density)
            unique_coverage.append(cell_unique)
            shared_coverage.append(cell_shared)
            blind_zones.append(cell_blind)

            if (r_idx, c_idx) in analysis_mask_cells:
                analysis_mask.append({'lat': cell_center_lat, 'lon': cell_center_lon, 'value': 1.0})
                blind_zones_masked.append(cell_blind)

            if (r_idx, c_idx) in blind_actionable_cells:
                blind_actionable.append(cell_blind)
            if (r_idx, c_idx) in blind_problematic_cells:
                blind_problematic.append(cell_blind)

    time_window_start_epoch = min(row.timestamp_epoch for row in rows)
    time_window_end_epoch = max(row.timestamp_epoch for row in rows)
    shared_active_cell_count = sum(1 for _, _, shared in counts.values() if shared > 0)
    active_cell_count = len(active_cells)
    shared_overlap_ratio_active = (
        shared_active_cell_count / active_cell_count if active_cell_count > 0 else 0.0
    )

    return {
        'grid_meta': {
            'min_lat': min_lat,
            'max_lat': max_lat,
            'min_lon': min_lon,
            'max_lon': max_lon,
            'cell_size_km': float(cell_size_km),
            'analysis_radius_km': float(analysis_radius_km),
            'blind_actionable_neighbor_radius_cells': 2,
            'blind_problematic_activity_radius_cells': 4,
            'blind_problematic_exclusion_radius_cells': 1,
            'blind_density_threshold': float(d_min),
            'blind_density_threshold_source': 'p10_active_density',
            'blind_semantics_version': 'a3',
            'rows': row_count,
            'cols': col_count,
            'time_window_start_epoch': time_window_start_epoch,
            'time_window_end_epoch': time_window_end_epoch,
        },
        'coverage_density': coverage_density,
        'unique_coverage': unique_coverage,
        'shared_coverage': shared_coverage,
        'blind_zones': blind_zones,
        'analysis_mask': analysis_mask,
        'blind_zones_masked': blind_zones_masked,
        'blind_actionable': blind_actionable,
        'blind_problematic': blind_problematic,
        'shared_overlap_ratio_active': shared_overlap_ratio_active,
    }


__all__ = ['build_spatial_network_features']
