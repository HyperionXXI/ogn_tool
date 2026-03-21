from __future__ import annotations

from typing import Any, Callable


def run(model: Callable[..., Any], **kwargs: Any) -> Any:
    """Canonical RF model execution wrapper."""
    return model(**kwargs)


__all__ = ["run"]
