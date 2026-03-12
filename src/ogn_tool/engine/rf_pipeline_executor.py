from __future__ import annotations

import time
from typing import Any


def run_stage(stage: Any, dataset: Any) -> Any:
    return stage.run(dataset)


def execute_rf_pipeline(dataset: Any, pipeline: Any) -> Any:
    pipeline.metrics = {}
    for stage in pipeline.stages:
        stage_name = getattr(stage, "name", stage.__class__.__name__)
        requires = set(getattr(stage, "requires", []))
        available = dataset.available_fields()
        missing = sorted(requires - available)
        if missing:
            raise RuntimeError(f"Stage {stage_name} missing inputs {missing}")

        start = time.perf_counter()
        dataset = run_stage(stage, dataset)
        elapsed = time.perf_counter() - start
        items_processed = 0
        try:
            obs = getattr(dataset, "observations", None)
            items_processed = len(obs) if obs is not None else 0
        except TypeError:
            items_processed = 0
        pipeline.metrics[stage_name] = {
            "executed": True,
            "time": elapsed,
            "items": int(items_processed),
        }
    return dataset


__all__ = ["execute_rf_pipeline", "run_stage"]
