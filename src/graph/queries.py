from __future__ import annotations

import json

from src.graph.models import Vertex, Edge


def merge_vertex(
    vertex: Vertex,
    graph_name: str,
) -> tuple[str, dict]:

    props = to_cypher_map(vertex.properties)

    query = f"""
    SELECT *
    FROM cypher(
        '{graph_name}',
        $$
            MERGE (n:{vertex.label} {{id: {cypher_value(vertex.id)}}})
            SET n += {props}
            RETURN n
        $$
    ) AS (n agtype);
    """

    return query, None


def merge_edge(
    edge: Edge,
    graph_name: str,
) -> tuple[str, None]:

    props = to_cypher_map(edge.properties)

    query = f"""
    SELECT *
    FROM cypher(
        '{graph_name}',
        $$
            MATCH (s:{edge.source_label} {{id: {cypher_value(edge.source_id)}}})
            MATCH (t:{edge.target_label} {{id: {cypher_value(edge.target_id)}}})

            MERGE (s)-[r:{edge.relationship}]->(t)

            SET r += {props}

            RETURN r
        $$
    ) AS (r agtype);
    """

    return query, None

def cypher_value(value):
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        value = (
            value
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "")
        )
        return f"'{value}'"

    if isinstance(value, list):
        return "[" + ", ".join(cypher_value(v) for v in value) + "]"

    if isinstance(value, dict):
        return "{" + ", ".join(
            f"{k}: {cypher_value(v)}"
            for k, v in value.items()
        ) + "}"

    return cypher_value(str(value))


def to_cypher_map(properties):
    if not properties:
        return "{}"

    return (
        "{"
        + ", ".join(
            f"{k}: {cypher_value(v)}"
            for k, v in properties.items()
        )
        + "}"
    )