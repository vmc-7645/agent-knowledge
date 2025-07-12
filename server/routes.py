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


@router.post("/search-question", response_model=List[QuestionSearchItem])
async def search_question_endpoint(payload: QuestionSearchRequest, db: Session = Depends(get_db)):
    """Return the *k* most similar questions to *payload.query*."""
    embedding = get_embedding(payload.query)

    stmt = text("SELECT * FROM search_questions(:embedding, :k)")
    rows = db.execute(
        stmt.bindparams(embedding=_vector_param(embedding), k=payload.k)
    ).fetchall()

    results = [
        QuestionSearchItem(id=row.id, content=row.question_content, distance=row.distance)
        for row in rows
    ]
    return results


@router.post("/add-answer", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
async def add_answer_endpoint(payload: AnswerCreate, db: Session = Depends(get_db)):
    """Embed *payload.content* and store it using the `add_answer` DB function."""
    embedding = get_embedding(payload.content)

    stmt = text("""
        SELECT add_answer(
            :context_id,
            :question_id,
            :content,
            :embedding,
            :is_solution
        ) AS id
    """)

    result = db.execute(
        stmt.bindparams(
            context_id=payload.context_id,
            question_id=payload.question_id,
            content=payload.content,
            embedding=_vector_param(embedding),
            is_solution=payload.is_solution,
        )
    ).fetchone()

    if result is None:
        raise HTTPException(status_code=500, detail="Failed to insert answer")

    db.commit()
    return AnswerOut(id=result.id)
