from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional


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

    def validate(self) -> None:
        if not isinstance(self.nodes, list):
            raise RuntimeError("NetworkGraph invalid: nodes must be a list")
        if not isinstance(self.edges, list):
            raise RuntimeError("NetworkGraph invalid: edges must be a list")
        if not isinstance(self.metrics, dict):
            raise RuntimeError("NetworkGraph invalid: metrics must be a dictionary")

        node_ids: set[str] = set()
        for node in self.nodes:
            if not isinstance(node, NetworkNode):
                raise RuntimeError("NetworkGraph invalid: nodes must contain NetworkNode instances")
            if not node.id:
                raise RuntimeError("NetworkGraph invalid: node id must be non-empty")
            if not node.type:
                raise RuntimeError("NetworkGraph invalid: node type must be non-empty")
            node_ids.add(node.id)

        for edge in self.edges:
            if not isinstance(edge, NetworkEdge):
                raise RuntimeError("NetworkGraph invalid: edges must contain NetworkEdge instances")
            if not edge.source or not edge.target:
                raise RuntimeError("NetworkGraph invalid: edge source and target must be non-empty")
            if not edge.relation:
                raise RuntimeError("NetworkGraph invalid: edge relation must be non-empty")
            if node_ids and (edge.source not in node_ids or edge.target not in node_ids):
                raise RuntimeError("NetworkGraph invalid: edge references unknown node ids")

    def get(self, key: str, default: Any = None) -> Any:
        return self.to_dict().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __contains__(self, key: object) -> bool:
        return key in {"nodes", "edges", "metrics"}

    def __iter__(self) -> Iterator[str]:
        yield from ("nodes", "edges", "metrics")
