from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from .db import Base

class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True, index=True)
    question_content = Column(Text, nullable=False)
    vector_embedding = Column(Vector(1536))
    created_at = Column(TIMESTAMP)

# Repeat for Context, Answer
