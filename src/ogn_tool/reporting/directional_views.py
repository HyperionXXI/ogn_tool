from __future__ import annotations

from typing import Any

ARC_WIDTH_BINS = 3


def _balance_label(balance: float | None) -> str:
    if balance is None:
        return 'unknown'
    if balance < 0.5:
        return 'strongly directional'
    if balance < 0.8:
        return 'anisotropic'
    if balance <= 1.2:
        return 'broad'
    return 'highly uneven'


def _confidence_label(packet_count: int) -> str:
    if packet_count < 100:
        return 'low'
    if packet_count < 500:
        return 'medium'
    return 'high'


def _arc_share_label(share: float | None) -> str:
    if share is None:
        return 'unknown'
    if share >= 0.35:
        return 'very concentrated'
    if share >= 0.22:
        return 'clear dominant sector'
    return 'distributed'


def _coverage_label(balance: float | None) -> str:
    if balance is None:
        return 'unknown'
    if balance < 0.5:
        return 'narrow'
    if balance < 0.8:
        return 'anisotropic'
    return 'broad'


def _format_deg(value: float) -> int:
    return int(round(value)) % 360


def _sector_label(start_deg: float, end_deg: float) -> str:
    return f"{_format_deg(start_deg)}°-{_format_deg(end_deg) or 360}°"


def _build_sector(edges: list[float], hist: list[int], idx: int, packet_count: int) -> dict[str, Any]:
    count = int(hist[idx])
    start_deg = float(edges[idx])
    end_deg = float(edges[idx + 1])
    share = (count / packet_count) if packet_count else 0.0
    return {
        'start_deg': start_deg,
        'end_deg': end_deg,
        'count': count,
        'share': round(share, 4),
        'label': _sector_label(start_deg, end_deg),
    }


def compute_top_sectors(edges: list[float], hist: list[int], packet_count: int, top_k: int = 3) -> list[dict[str, Any]]:
    ranked = sorted(range(len(hist)), key=lambda idx: hist[idx], reverse=True)
    return [_build_sector(edges, hist, idx, packet_count) for idx in ranked[:top_k]]


def compute_dominant_arc(
    edges: list[float],
    hist: list[int],
    packet_count: int,
    width_bins: int = ARC_WIDTH_BINS,
) -> dict[str, Any] | None:
    n = len(hist)
    if not hist or not edges or len(edges) != n + 1 or n < width_bins:
        return None

    best_sum = -1
    best_idx = 0
    for idx in range(n):
        window_sum = sum(hist[(idx + offset) % n] for offset in range(width_bins))
        if window_sum > best_sum:
            best_sum = int(window_sum)
            best_idx = idx

    start_deg = float(edges[best_idx])
    end_idx = (best_idx + width_bins) % n
    end_deg = float(edges[end_idx])
    share = (best_sum / packet_count) if packet_count else 0.0
    return {
        'start_deg': start_deg,
        'end_deg': end_deg,
        'count': best_sum,
        'share': round(share, 4),
        'start_bin': best_idx,
        'width_bins': width_bins,
        'label': _sector_label(start_deg, end_deg),
    }


def _summary_sentence(dominant_arc: dict[str, Any] | None, balance: float | None) -> str:
    if not dominant_arc:
        return 'Directional coverage summary is unavailable.'

    if balance is None:
        return f"Directional coverage is centered on {dominant_arc['label']}."

    if balance < 0.5:
        descriptor = 'strongly directional coverage'
    elif balance < 0.8:
        descriptor = 'anisotropic coverage'
    else:
        descriptor = 'broad coverage'

    start_deg = _format_deg(dominant_arc['start_deg'])
    end_deg = _format_deg(dominant_arc['end_deg']) or 360
    if start_deg == 90 and end_deg == 120:
        direction = 'east / east-southeast'
    else:
        direction = dominant_arc['label']

    return (
        f"{descriptor.capitalize()} with a clear reinforcement toward {direction} "
        f"({dominant_arc['share'] * 100:.1f}% of usable packets)."
    )


def build_directional_summary(
    histogram: dict[str, Any],
    directional_balance: float | int | None,
    *,
    run_id: str | None = None,
    station_angular_entropy: Any = None,
    shadow_risk_scores: Any = None,
) -> dict[str, Any]:
    edges = histogram.get('edges') or []
    hist = histogram.get('hist') or []
    packet_count = int(sum(hist)) if hist else 0

    top_bin = None
    top_sectors: list[dict[str, Any]] = []
    dominant_arc = None
    dominant_arc_share = None

    if hist and edges and len(edges) == len(hist) + 1:
        top_sectors = compute_top_sectors(edges, hist, packet_count)
        if top_sectors:
            top_bin = top_sectors[0]
        dominant_arc = compute_dominant_arc(edges, hist, packet_count)
        if dominant_arc:
            dominant_arc_share = dominant_arc['share']

    balance_value = float(directional_balance) if isinstance(directional_balance, (int, float)) else None
    confidence = _confidence_label(packet_count)

    return {
        'run_id': run_id,
        'packet_count': packet_count,
        'directional_balance': directional_balance,
        'coverage': _coverage_label(balance_value),
        'top_bin': top_bin,
        'dominant_arc': dominant_arc,
        'dominant_arc_share': dominant_arc_share,
        'top_sectors': top_sectors,
        'station_angular_entropy': station_angular_entropy,
        'shadow_risk_scores': shadow_risk_scores,
        'interpretation': {
            'anisotropy': _balance_label(balance_value),
            'dominant_sector_strength': _arc_share_label(dominant_arc_share),
            'hard_shadow_detected': bool(shadow_risk_scores) if isinstance(shadow_risk_scores, dict) else False,
            'confidence': confidence,
            'summary_sentence': _summary_sentence(dominant_arc, balance_value),
            'notes': [
                'Station angular entropy is unavailable.' if not station_angular_entropy else 'Station angular entropy is available.',
                'Shadow risk scores are unavailable.' if not shadow_risk_scores else 'Shadow risk scores are available.',
            ],
        },
    }


def format_directional_summary(summary: dict[str, Any]) -> str:
    top_bin = summary.get('top_bin') or {}
    dominant_arc = summary.get('dominant_arc') or {}
    top_sectors = summary.get('top_sectors') or []
    interp = summary.get('interpretation') or {}

    lines = [
        'Directional summary',
        '-------------------',
        '',
        f"Packets analysed: {summary['packet_count']}",
        '',
        (
            f"Directional balance: {summary.get('directional_balance'):.2f}"
            if isinstance(summary.get('directional_balance'), (int, float))
            else 'Directional balance: unavailable'
        ),
        f"Coverage: {summary.get('coverage')}",
        '',
    ]

    if dominant_arc:
        lines.append(f"Dominant arc: {dominant_arc['label']}")
        lines.append(f"Share: {dominant_arc['share'] * 100:.1f} %")
    else:
        lines.append('Dominant arc: unavailable')
        lines.append('Share: unavailable')
    lines.append('')

    if top_sectors:
        lines.append('Top sectors:')
        for sector in top_sectors:
            lines.append(f"{sector['label']:>10} : {sector['count']}")
        lines.append('')

    if top_bin:
        lines.append(
            f"Top bin (debug): {top_bin['label']} ({top_bin['count']} packets, {top_bin['share'] * 100:.1f}%)"
        )
        lines.append('')

    lines.extend(
        [
            'Interpretation:',
            str(interp.get('summary_sentence')),
            '',
            f"Hard shadow detected: {'yes' if interp.get('hard_shadow_detected') else 'no'}",
            f"Confidence: {interp.get('confidence')}",
        ]
    )
    for note in interp.get('notes', []):
        lines.append(f"- {note}")

    return '\n'.join(lines)
