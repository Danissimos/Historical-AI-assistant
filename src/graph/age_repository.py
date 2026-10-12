from __future__ import annotations

from sqlalchemy import Engine

from src.graph.models import Graph
from src.graph.queries import (
    merge_vertex,
    merge_edge,
)


class AgeRepository:
    """
    Репозиторий для записи графа в Apache AGE.
    """

    def __init__(
        self,
        engine: Engine,
        graph_name: str = "knowledge_graph_ai_assistant",
    ):
        self.engine = engine
        self.graph_name = graph_name

    def save(self, graph: Graph) -> None:

        with self.engine.begin() as conn:

            self._prepare_age(conn)

            for vertex in graph.vertices:
                query, _ = merge_vertex(
                    vertex,
                    self.graph_name
                )

                query = query.replace("%", "%%")

                conn.exec_driver_sql(
                    query, ()
                )

            for edge in graph.edges:
                query, _ = merge_edge(
                    edge=edge,
                    graph_name=self.graph_name,
                )

                query = query.replace("%", "%%")

                conn.exec_driver_sql(
                    query, ()
                )


    @staticmethod
    def _prepare_age(conn):

        conn.exec_driver_sql(
            """
            LOAD 'age';

            SET search_path =
                ag_catalog,
                public;
            """
        )