from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, Optional


@dataclass
class NetworkNode:
    id: str
    type: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    altitude: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "type": self.type,
            "lat": self.lat,
            "lon": self.lon,
            "altitude": self.altitude,
        }
        if self.attributes:
            data.update(self.attributes)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "NetworkNode":
        base_keys = {"id", "type", "lat", "lon", "altitude"}
        attrs = {k: v for k, v in data.items() if k not in base_keys}
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
            lat=data.get("lat"),
            lon=data.get("lon"),
            altitude=data.get("altitude"),
            attributes=attrs or None,
        )


@dataclass
class NetworkEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0
    attributes: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        data = {
            "source": self.source,
            "target": self.target,
            "type": self.relation,
            "relation": self.relation,
            "weight": self.weight,
        }
        if self.attributes:
            data.update(self.attributes)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "NetworkEdge":
        base_keys = {"source", "target", "type", "relation", "weight"}
        attrs = {k: v for k, v in data.items() if k not in base_keys}
        relation = data.get("relation", data.get("type", ""))
        return cls(
            source=str(data.get("source", "")),
            target=str(data.get("target", "")),
            relation=str(relation),
            weight=float(data.get("weight", 1.0) or 1.0),
            attributes=attrs or None,
        )


@dataclass
class NetworkGraph:
    nodes: list[NetworkNode] = field(default_factory=list)
    edges: list[NetworkEdge] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "metrics": dict(self.metrics or {}),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> "NetworkGraph":
        data = data or {}
        return cls(
            nodes=[NetworkNode.from_dict(node) for node in data.get("nodes", [])],
            edges=[NetworkEdge.from_dict(edge) for edge in data.get("edges", [])],
            metrics=dict(data.get("metrics") or {}),
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: object) -> bool:
        return key in {"nodes", "edges", "metrics"}

    def __iter__(self) -> Iterator[str]:
        yield from ("nodes", "edges", "metrics")
