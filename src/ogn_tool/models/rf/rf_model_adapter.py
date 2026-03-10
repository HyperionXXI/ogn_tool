from __future__ import annotations

from typing import Any, Callable, Dict


def run_rf_model(model_fn: Callable[..., Any], **kwargs: Any) -> Dict[str, Any]:
    """
    Execute an RF model function and normalize its output structure.

    Standard output:
    {
        "implemented": bool,
        "summary": dict | None,
        "data": any,
        "binned_data": any | None
    }
    """

    if model_fn is None:
        return {
            "implemented": False,
            "summary": {"reason": "no model"},
            "data": None,
            "binned_data": None,
        }

    result = model_fn(**kwargs)

    if result is None:
        return {
            "implemented": False,
            "summary": {"reason": "no data"},
            "data": None,
            "binned_data": None,
        }

    if isinstance(result, list):
        return {
            "implemented": True,
            "summary": {},
            "data": result,
            "binned_data": None,
        }

    if isinstance(result, dict):
        if not result:
            return {
                "implemented": False,
                "summary": {"reason": "no data"},
                "data": None,
                "binned_data": None,
            }
        return {
            "implemented": bool(result.get("implemented", True)),
            "summary": result.get("summary"),
            "data": result.get("data"),
            "binned_data": result.get("binned_data"),
        }

    return {
        "implemented": True,
        "summary": {},
        "data": result,
        "binned_data": None,
    }
