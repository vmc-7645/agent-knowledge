-- 01_schema.sql
-- Postgres + pgvector schema for agent-knowledge project
---------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS vector;

-- -----------------------------------------------------
--  Context: environment / system metadata
-- -----------------------------------------------------
CREATE TABLE context (
    id SERIAL PRIMARY KEY,
    context_content TEXT NOT NULL,          -- keep name in sync with add_context()
    vector_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT now()
);

-- -----------------------------------------------------
--  Questions: the prompts/issues
-- -----------------------------------------------------
CREATE TABLE question (
    id SERIAL PRIMARY KEY,
    question_content TEXT NOT NULL,
    vector_embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT now()
);

-- -----------------------------------------------------
--  Answers: one or more per (question, context)
-- -----------------------------------------------------
CREATE TABLE answer (
    id SERIAL PRIMARY KEY,
    context_id  INT REFERENCES context(id)  ON DELETE CASCADE,
    question_id INT REFERENCES question(id) ON DELETE CASCADE,
    answer_content TEXT NOT NULL,
    vector_embedding VECTOR(1536),          -- included to match add_answer/search_answers
    is_solution BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now()
);

-- -----------------------------------------------------
--  Indexes for ANN similarity search (IVFFLAT, cosine)
--  Build these *after* loading a few hundred rows for best performance.
-- -----------------------------------------------------
CREATE INDEX question_embedding_ivfflat
    ON question USING ivfflat (vector_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX context_embedding_ivfflat
    ON context  USING ivfflat (vector_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX answer_embedding_ivfflat
    ON answer   USING ivfflat (vector_embedding vector_cosine_ops)
    WITH (lists = 100);
