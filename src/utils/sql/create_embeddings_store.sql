CREATE TABLE embeddings_store
(
    id bigserial PRIMARY KEY,

    chunk_id bigint NOT NULL,

    embedding_model text NOT NULL,

    embedding vector(768) NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE (chunk_id, embedding_model)
);