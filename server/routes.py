from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db  # Assumes db.py exposes a get_db() dependency that yields a Session
from .embedding_utils import get_embedding

# -----------------------------------------------------------------------------
# FastAPI router
# -----------------------------------------------------------------------------

router = APIRouter(
    prefix="",
    tags=["semantic-qa"],
)

# -----------------------------------------------------------------------------
# Pydantic request / response models
# -----------------------------------------------------------------------------

class QuestionCreate(BaseModel):
    content: str = Field(..., description="Raw text of the question")


class QuestionOut(BaseModel):
    id: int


class QuestionSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    k: int = Field(5, gt=0, le=50, description="Number of nearest questions to return")


class QuestionSearchItem(BaseModel):
    id: int
    content: str
    distance: float


class AnswerCreate(BaseModel):
    question_id: int = Field(..., description="ID of the related question")
    content: str = Field(..., description="Answer text")
    is_solution: bool = Field(False, description="Mark as accepted solution")
    context_id: Optional[int] = Field(None, description="Optional context row ID")
    embedding: Optional[List[float]] = Field(None, description="Optional embedding")


class AnswerOut(BaseModel):
    id: int


# -----------------------------------------------------------------------------
# Helper – insert vector-safe parameter
# -----------------------------------------------------------------------------

def _vector_param(embedding: List[float]) -> List[float]:
    """Wrap an embedding list so pgvector/SQLAlchemy will cast it correctly."""
    # pgvector's SQLAlchemy integration automatically casts Python lists → vector
    return embedding


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@router.post("/add-question", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def add_question_endpoint(payload: QuestionCreate, db: Session = Depends(get_db)):
    """Embed *payload.content* and store it using the `add_question` DB function."""
    embedding = get_embedding(payload.content)

    # Call the SQL helper function. We rely on pgvector's auto-casting for the vector param.
    stmt = text("SELECT add_question(:content, :embedding) AS id")
    result = db.execute(stmt.bindparams(content=payload.content, embedding=_vector_param(embedding))).fetchone()

    if result is None:
        raise HTTPException(status_code=500, detail="Failed to insert question")

    db.commit()
    return QuestionOut(id=result.id)


class SearchQuestionIn(BaseModel):
    content: str
    k: int = 5
    embedding: List[float] | None = None

@router.post("/search-question")
def search_question_endpoint(req: SearchQuestionIn, db=Depends(get_db)):
    emb = req.embedding
    if emb is None:
        emb = get_embedding(req.content)
    rows = db.execute(
        text("SELECT * FROM search_questions(:embedding, :k)"),
        {"embedding": emb, "k": req.k},
    ).fetchall()
    return [{"id": r.id, "question_content": r.question_content, "distance": r.distance} for r in rows]

# server/routes.py  – inside add_answer_endpoint
@router.post("/add-answer", status_code=201)
def add_answer_endpoint(body: AnswerCreate, db=Depends(get_db)):
    emb = body.embedding or get_embedding(body.content)
    new_id = db.execute(
        text("SELECT add_answer(:ctx, :qid, :content, :emb, :sol)"),
        {
            "ctx": body.context_id,
            "qid": body.question_id,
            "content": body.content,
            "emb": emb,
            "sol": body.is_solution,
        },
    ).scalar_one()
    db.commit()
    return {"id": new_id}      # <-- just return a dict, not AnswerOut


import datetime
class AnswerOut(BaseModel):
    id: int
    answer_content: str
    is_solution: bool
    # created_at: datetime | None = None      # if you want the timestamp

@router.get("/answers/{question_id}", response_model=list[AnswerOut])
def answers_for_question(question_id: int, limit: int = 5, db=Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM answer_for_question(:qid, :lim)"),
        {"qid": question_id, "lim": limit},
    ).fetchall()
    return [
        AnswerOut(
            id=r.id,
            answer_content=r.answer_content,
            is_solution=r.is_solution,
            created_at=getattr(r, "created_at", None),
        )
        for r in rows
    ]