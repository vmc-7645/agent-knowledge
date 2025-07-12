

# Setup

```bash
# 1. Create a virtual environment
py -3 -m venv .venv

# 2. Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# If you use CMD
.venv\Scripts\activate.bat

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install weave (and others)
pip install -r requirements.txt

# 5. Start the database
docker-compose up -d
docker ps
```

# Running

```bash
# 1. Run the server
uvicorn server.main:app --reload

# 2. Run the agent
python agent/agent_runner.py

# 3. (optional) Run multiple agents
python agent/agent_runner.py --persona "terrence tau"
python agent/agent_runner.py --persona "sam altman"
python agent/agent_runner.py --persona "kim kardashian"
python agent/agent_runner.py --persona "brad pitt"
```

# Workflow

Agent (agent/):
- Queries context/questions from pgvector (via memory.py)
- Adds new data to DB when it discovers or generates new knowledge
- Embeds with embedding_utils.py using OpenAI or local model
- Interacts through Weave API to get/expose function calls

Server (server/):
- Offers REST endpoints for:
- `/add-question` - add a new question to the DB
- `/search-question` - search for a question in the DB
- `/add-context` - add a new context to the DB
- `/search-context` - search for a context in the DB
- Handles pgvector queries, embedding storage, result scoring

Communication:
- Use httpx inside the agent to talk to your FastAPI backend
- Or share a Python module (agent/shared_db.py) to call directly

# Database

db schema used in hackathon

Main tables

```sql
-- Enable pgvector (if not already)
CREATE EXTENSION IF NOT EXISTS vector;

-- Context: system/environment description (with vector)
CREATE TABLE context (
  id SERIAL PRIMARY KEY,
  description_content TEXT NOT NULL,
  vector_embedding VECTOR(1536),  -- adjust to match your embedding dimension
  created_at TIMESTAMP DEFAULT now()
);

-- Questions: main prompt or issue
CREATE TABLE question (
  id SERIAL PRIMARY KEY,
  question_content TEXT NOT NULL,
  vector_embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT now()
);

-- Answers: one or more per (question, context)
CREATE TABLE answer (
  id SERIAL PRIMARY KEY,
  context_id INTEGER REFERENCES context(id) ON DELETE CASCADE,
  question_id INTEGER REFERENCES question(id) ON DELETE CASCADE,
  answer_content TEXT NOT NULL,
  is_solution BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT now()
);
```

Indexes:
```sql
-- Fast similarity search on embeddings (e.g., ANN)
CREATE INDEX ON question USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON context  USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);
```

Example queries:

```sql
-- Find similar questions
SELECT id, question_content
FROM question
ORDER BY vector_embedding <#> '[0.01, 0.02, ..., 0.03]'  -- replace with real embedding
LIMIT 5;

-- Find similar answers
SELECT id, answer_content
FROM answer
ORDER BY vector_embedding <#> '[0.01, 0.02, ..., 0.03]'  -- replace with real embedding
LIMIT 5;

-- Find similar context
SELECT id, description_content
FROM context
ORDER BY vector_embedding <#> '[0.01, 0.02, ..., 0.03]'  -- replace with real embedding
LIMIT 5;
```
