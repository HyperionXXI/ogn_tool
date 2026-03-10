from __future__ import annotations

from typing import Any, Dict


def build_rf_models_view(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a UI-friendly representation of RF model results.

    Input:
        results["rf_models"]

    Output:
        {
          "models": [
            {
              "name": "signal_distance",
              "implemented": True,
              "summary": {...},
              "chart_data": ...
            },
            ...
          ]
        }
    """

    rf_models = results.get("rf_models") if isinstance(results, dict) else None
    if not isinstance(rf_models, dict):
        return {"models": []}

    models = []
    for name, payload in rf_models.items():
        if not isinstance(payload, dict):
            models.append(
                {
                    "name": name,
                    "implemented": False,
                    "summary": {"reason": "invalid_payload"},
                    "chart_data": None,
                }
            )
            continue

        models.append(
            {
                "name": name,
                "implemented": bool(payload.get("implemented", False)),
                "summary": payload.get("summary") or {},
                "chart_data": payload.get("data"),
                "binned_data": payload.get("binned_data"),
            }
        )

    return {"models": models}
