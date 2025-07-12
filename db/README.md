# Database Function Reference

This project stores all Q&A knowledge in PostgreSQL 15 + pgvector.  Below is a quick reference to every stored function shipped in /db/init/*.sql and how to use them from psql, SQLAlchemy, or any client.

## Core Insert Helpers

| Function | Signature | Purpose / Behavior |
| --- | --- | --- |
| add_question | (content text, embedding vector) → int | Inserts a new row into question, returns the generated id. |
| add_context | (content text, embedding vector) → int | Inserts into context, returns id. |
| add_answer | (context_id int, question_id int, content text, embedding vector, is_solution boolean DEFAULT false) → int | Inserts an answer linked to a question & context, returns id. |

Example (psql):

```sql
SELECT add_question('Why is the sky blue?', '[0.1,0.2,...]'::vector);
```

## Semantic Search Helpers  ▶ cosine distance <#>

| Function | Signature | Returns | Notes |
| --- | --- | --- | --- |
| search_questions | (embedding vector, k int DEFAULT 5) | TABLE(id, question_content, distance) | Finds closest questions to the given embedding. |
| search_context | (embedding vector, k int DEFAULT 5) | TABLE(id, context_content, distance) | Same but for context. |
| search_answers | (embedding vector, k int DEFAULT 5) | TABLE(id, answer_content, distance) | Vector search over answers. |

Example (psql):

```sql
SELECT * FROM search_questions('[...]'::vector, 3);
```

## Moderation / Workflow Helpers

| Function | Signature | Returns | Action |
| --- | --- | --- | --- |
| mark_solution | (answer_id int) | void | Sets is_solution=true on the chosen answer and clears the flag on its siblings. |
| unsolved_questions | (limit int DEFAULT 10) | TABLE(id, question_content, created_at) | Lists newest questions that have no accepted solution. |
| similar_context_questions | (context_id int, k int DEFAULT 5) | TABLE(id, question_content, distance) | Given a context row, returns the k nearest questions by vector similarity. |

## Quick Testing Cheatsheet

```bash
# Open interactive shell in the container
$ docker exec -it pgvector-db psql -U postgres -d agentdb

-- Verify extensions & tables
db=> \dx
 db=> \dt

-- Smoke‑test vector search
SELECT add_question('hello', random()::float8[][:1536]);
SELECT * FROM search_questions(random()::float8[][:1536], 2);
```

### Notes

All embedding columns are VECTOR(1536); adjust dimension in SQL if you change the model size.

ANN indexes (ivfflat) are created for each embedding column; they perform best once the table holds a few hundred rows.

Functions marked STABLE are safe for parallel execution and can appear inside queries; mark_solution is VOLATILE because it mutates data.

Happy querying! :rocket:

