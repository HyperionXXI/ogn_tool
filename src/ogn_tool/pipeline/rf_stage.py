from __future__ import annotations

from typing import Any, Dict


class RFAnalysisStage:
    """Base class for RF analysis pipeline stages."""

    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
