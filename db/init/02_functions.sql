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

-- -------------------------------------------------
-- Answers for a question (limit 5, solution first)
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION answer_for_question(
    _question_id INT,
    _limit INT DEFAULT 5
) RETURNS TABLE(
    id INT,
    answer_content TEXT,
    is_solution BOOLEAN,
    created_at TIMESTAMP
) AS $$
SELECT id,
       answer_content,
       is_solution,
       created_at
FROM   answer
WHERE  question_id = _question_id
ORDER  BY is_solution DESC, created_at DESC
LIMIT  _limit;
$$ LANGUAGE SQL STABLE;

-- -------------------------------------------------
-- Context row for a specific answer
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION context_for_answer(
    _answer_id INT
) RETURNS TABLE(
    context_id INT,
    context_content TEXT
) AS $$
SELECT c.id,
       c.context_content
FROM   answer  a
JOIN   context c ON c.id = a.context_id
WHERE  a.id = _answer_id
LIMIT  1;
$$ LANGUAGE SQL STABLE;

-- -------------------------------------------------
-- Mark an answer as the accepted solution
--   • Sets chosen answer to true
--   • Clears is_solution on siblings
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION mark_solution(
    _answer_id INT
) RETURNS VOID AS $$
WITH chosen AS (
    SELECT question_id
    FROM   answer
    WHERE  id = _answer_id
)
UPDATE answer
SET    is_solution = CASE WHEN id = _answer_id THEN TRUE ELSE FALSE END
WHERE  question_id = (SELECT question_id FROM chosen);
$$ LANGUAGE SQL VOLATILE;

-- -------------------------------------------------
-- Questions with no accepted solution
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION unsolved_questions(
    _limit INT DEFAULT 10
) RETURNS TABLE(
    id INT,
    question_content TEXT,
    created_at TIMESTAMP
) AS $$
SELECT q.id,
       q.question_content,
       q.created_at
FROM   question q
LEFT   JOIN answer a ON a.question_id = q.id AND a.is_solution
WHERE  a.id IS NULL
ORDER  BY q.created_at DESC
LIMIT  _limit;
$$ LANGUAGE SQL STABLE;

-- -------------------------------------------------
-- Questions whose embeddings are closest to a
-- given context row
-- -------------------------------------------------
CREATE OR REPLACE FUNCTION similar_context_questions(
    _context_id INT,
    _k INT DEFAULT 5
) RETURNS TABLE(
    id INT,
    question_content TEXT,
    distance FLOAT
) AS $$
SELECT q.id,
       q.question_content,
       q.vector_embedding <#> c.vector_embedding AS distance
FROM   context c,
       question q
WHERE  c.id = _context_id
ORDER  BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;
