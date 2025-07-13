-- 02_functions.sql  ------------------------------------------------------
-- All helpers accept FLOAT8[] embeddings and cast to pgvector VECTOR(1536)
-------------------------------------------------------------------------

-- ========== INSERT HELPERS ============================================

CREATE OR REPLACE FUNCTION add_question(
    _content   TEXT,
    _embedding FLOAT8[]
) RETURNS INT AS $$
INSERT INTO question (question_content, vector_embedding)
VALUES (_content, _embedding::vector)
RETURNING id;
$$ LANGUAGE SQL STRICT;

CREATE OR REPLACE FUNCTION add_context(
    _content   TEXT,
    _embedding FLOAT8[]
) RETURNS INT AS $$
INSERT INTO context (context_content, vector_embedding)
VALUES (_content, _embedding::vector)
RETURNING id;
$$ LANGUAGE SQL STRICT;

CREATE OR REPLACE FUNCTION add_answer(
    _context_id  INT,
    _question_id INT,
    _content     TEXT,
    _embedding   FLOAT8[],
    _is_solution BOOLEAN DEFAULT FALSE
) RETURNS INT AS $$
INSERT INTO answer (context_id, question_id, answer_content,
                    vector_embedding, is_solution)
VALUES (_context_id, _question_id, _content, _embedding::vector, _is_solution)
RETURNING id;
$$ LANGUAGE SQL STRICT;

-- ========== SEMANTIC SEARCH ===========================================

CREATE OR REPLACE FUNCTION search_questions(
    _embedding FLOAT8[],
    _k INT DEFAULT 5
) RETURNS TABLE(id INT, question_content TEXT, distance FLOAT) AS $$
SELECT id,
       question_content,
       vector_embedding <#> _embedding::vector AS distance
FROM   question
ORDER  BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;

CREATE OR REPLACE FUNCTION search_context(
    _embedding FLOAT8[],
    _k INT DEFAULT 5
) RETURNS TABLE(id INT, context_content TEXT, distance FLOAT) AS $$
SELECT id,
       context_content,
       vector_embedding <#> _embedding::vector AS distance
FROM   context
ORDER  BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;

CREATE OR REPLACE FUNCTION search_answers(
    _embedding FLOAT8[],
    _k INT DEFAULT 5
) RETURNS TABLE(id INT, answer_content TEXT, distance FLOAT) AS $$
SELECT id,
       answer_content,
       vector_embedding <#> _embedding::vector AS distance
FROM   answer
ORDER  BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;

-- ========== RELATIONAL FETCHERS =======================================

CREATE OR REPLACE FUNCTION answer_for_question(
    _question_id INT,
    _limit INT DEFAULT 5
) RETURNS TABLE(id INT, answer_content TEXT,
                is_solution BOOLEAN, created_at TIMESTAMP) AS $$
SELECT id, answer_content, is_solution, created_at
FROM   answer
WHERE  question_id = _question_id
ORDER  BY is_solution DESC, created_at DESC
LIMIT  _limit;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION context_for_answer(
    _answer_id INT
) RETURNS TABLE(context_id INT, context_content TEXT) AS $$
SELECT c.id, c.context_content
FROM   answer a
JOIN   context c ON c.id = a.context_id
WHERE  a.id = _answer_id
LIMIT  1;
$$ LANGUAGE SQL STABLE;

-- ========== WORKFLOW UTILITIES ========================================

CREATE OR REPLACE FUNCTION mark_solution(
    _answer_id INT
) RETURNS VOID AS $$
WITH q AS (SELECT question_id FROM answer WHERE id = _answer_id)
UPDATE answer
SET    is_solution = (id = _answer_id)
WHERE  question_id = (SELECT question_id FROM q);
$$ LANGUAGE SQL VOLATILE;

CREATE OR REPLACE FUNCTION unsolved_questions(
    _limit INT DEFAULT 10
) RETURNS TABLE(id INT, question_content TEXT, created_at TIMESTAMP) AS $$
SELECT q.id, q.question_content, q.created_at
FROM   question q
WHERE  NOT EXISTS (
    SELECT 1 FROM answer a
    WHERE  a.question_id = q.id AND a.is_solution
)
ORDER  BY q.created_at DESC
LIMIT  _limit;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION similar_context_questions(
    _context_id INT,
    _k INT DEFAULT 5
) RETURNS TABLE(id INT, question_content TEXT, distance FLOAT) AS $$
SELECT q.id,
       q.question_content,
       q.vector_embedding <#> c.vector_embedding AS distance
FROM   context c,
       question q
WHERE  c.id = _context_id
ORDER  BY distance
LIMIT  _k;
$$ LANGUAGE SQL STABLE PARALLEL SAFE;
