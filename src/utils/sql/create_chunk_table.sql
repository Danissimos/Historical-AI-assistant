CREATE TABLE chunks
(
    id bigserial PRIMARY KEY,

    page_title text NOT NULL,
    page_url text NOT NULL,

    chunk_index integer NOT NULL,

    source text NOT NULL,

    chunk_text text NOT NULL,

    metadata jsonb NOT NULL,

    created_at timestamptz NOT NULL DEFAULT now()
);