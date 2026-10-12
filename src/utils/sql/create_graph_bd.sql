-- 1. Включаем расширение AGE
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- 2. Создаём граф, если ещё не создан
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM ag_catalog.ag_graph
        WHERE name = 'knowledge_graph_ai_assistant'
    ) THEN
        PERFORM create_graph('knowledge_graph_ai_assistant');
    END IF;
END $$;

-- 3. Создаём базовые label'ы
SELECT *
FROM cypher('knowledge_graph_ai_assistant', $$

    MERGE (d:Document {__init__: true})
    MERGE (s:Section {__init__: true})
    MERGE (c:Chunk {__init__: true})
    MERGE (e:Entity {__init__: true})
    MERGE (i:Image {__init__: true})
    MERGE (t:Table {__init__: true})

    MERGE (d)-[:HAS_SECTION]->(s)
    MERGE (s)-[:HAS_CHUNK]->(c)

    MERGE (c)-[:MENTIONS]->(e)
    MERGE (c)-[:HAS_IMAGE]->(i)
    MERGE (c)-[:HAS_TABLE]->(t)

$$) AS (v agtype);

-- 4. Удаляем технические вершины
SELECT *
FROM cypher('knowledge_graph_ai_assistant', $$

    MATCH (n)
    WHERE n.__init__ = true
    DETACH DELETE n

$$) AS (v agtype);
