-- 02_functions.sql
-- All helper functions aligned with 01_schema.sql
-- Uses pgvector cosine distance (<#>) for semantic search
-- ---------------------------------------------------------

-- -------------------------------------------------
-- Insert a question and return its id
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION add_question(
    _content TEXT,
    _embedding VECTOR(1536)
) RETURNS INT AS $$
INSERT INTO question (question_content, vector_embedding)
VALUES (_content, _embedding)
RETURNING id;
$$ LANGUAGE SQL STRICT;

-- -------------------------------------------------
-- Semantic search for questions (top-k by cosine distance)
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION search_questions(
    _embedding VECTOR(1536),
    _k INT DEFAULT 5
) RETURNS TABLE(
    id INT,
    question_content TEXT,
    distance FLOAT
) AS $$
SELECT id,
       question_content,
       vector_embedding <#> _embedding AS distance
FROM   question
ORDER BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;

-- -------------------------------------------------
-- Insert a context row and return its id
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION add_context(
    _content TEXT,
    _embedding VECTOR(1536)
) RETURNS INT AS $$
INSERT INTO context (context_content, vector_embedding)
VALUES (_content, _embedding)
RETURNING id;
$$ LANGUAGE SQL STRICT;

-- -------------------------------------------------
-- Semantic search for contexts
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION search_context(
    _embedding VECTOR(1536),
    _k INT DEFAULT 5
) RETURNS TABLE(
    id INT,
    context_content TEXT,
    distance FLOAT
) AS $$
SELECT id,
       context_content,
       vector_embedding <#> _embedding AS distance
FROM   context
ORDER BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;

-- -------------------------------------------------
-- Insert an answer and return its id
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION add_answer(
    _context_id INT,
    _question_id INT,
    _content TEXT,
    _embedding VECTOR(1536),
    _is_solution BOOLEAN DEFAULT false
) RETURNS INT AS $$
INSERT INTO answer (context_id, question_id, answer_content, vector_embedding, is_solution)
VALUES (_context_id, _question_id, _content, _embedding, _is_solution)
RETURNING id;
$$ LANGUAGE SQL STRICT;

-- -------------------------------------------------
-- Semantic search for answers
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION search_answers(
    _embedding VECTOR(1536),
    _k INT DEFAULT 5
) RETURNS TABLE(
    id INT,
    answer_content TEXT,
    distance FLOAT
) AS $$
SELECT id,
       answer_content,
       vector_embedding <#> _embedding AS distance
FROM   answer
ORDER BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;
