from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Vertex:
    """
    Вершина графа.
    """

    label: str
    id: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.label, self.id))


@dataclass(slots=True)
class Edge:
    """
    Связь между двумя вершинами.
    """

    source_label: str
    source_id: str

    relationship: str

    target_label: str
    target_id: str

    properties: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: str(uuid4()))

    def __hash__(self) -> int:
        return hash((
            self.source_label,
            self.source_id,
            self.relationship,
            self.target_label,
            self.target_id,
        ))


@dataclass(slots=True)
class Graph:
    """
    Контейнер графа.
    """

    vertices: set[Vertex] = field(default_factory=set)
    edges: set[Edge] = field(default_factory=set)

    def add_vertex(
        self,
        label: str,
        id: str,
        **properties: Any,
    ) -> Vertex:

        vertex = Vertex(
            label=label,
            id=id,
            properties=properties,
        )

        self.vertices.add(vertex)

        return vertex

    def add_edge(
        self,
        source: Vertex,
        relationship: str,
        target: Vertex,
        **properties: Any,
    ) -> Edge:

        edge = Edge(
            source_label=source.label,
            source_id=source.id,

            relationship=relationship,

            target_label=target.label,
            target_id=target.id,

            properties=properties,
        )

        self.edges.add(edge)

        return edge

    def merge(self, other: "Graph") -> None:
        """
        Объединить два графа.
        """

        self.vertices |= other.vertices
        self.edges |= other.edges

    def clear(self) -> None:
        self.vertices.clear()
        self.edges.clear()

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def edge_count(self) -> int:
        return len(self.edges)