from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class SpatialView(TypedDict):
    """Stable contract for spatial report projection.

    Field names are strict and always present.
    """

    stations: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    coverage: List[Dict[str, Any]]
    diagnostics: List[Dict[str, Any]]


__all__ = ["SpatialView"]

