from fastapi import APIRouter, Depends
from sqlalchemy import text
from .db import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/add-question")
def add_question(payload: dict, db=Depends(get_db)):
    sql = text("SELECT add_question(:content, :embedding)")
    result = db.execute(sql, payload).scalar_one()
    db.commit()
    return {"id": result}

@router.post("/search-question")
def search_question(payload: dict, db=Depends(get_db)):
    sql = text("SELECT search_question(:embedding)")
    result = db.execute(sql, payload).scalar_one()
    db.commit()
    return {"id": result}

@router.post("/add-context")
def add_context(payload: dict, db=Depends(get_db)):
    sql = text("SELECT add_context(:content, :embedding)")
    result = db.execute(sql, payload).scalar_one()
    db.commit()
    return {"id": result}

@router.post("/search-context")
def search_context(payload: dict, db=Depends(get_db)):
    sql = text("SELECT search_context(:embedding)")
    result = db.execute(sql, payload).scalar_one()
    db.commit()
    return {"id": result}
