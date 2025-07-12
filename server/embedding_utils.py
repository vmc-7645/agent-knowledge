import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Default model
EMBEDDING_MODEL = "text-embedding-3-small"

def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Get the embedding vector for a single string of text.

    Args:
        text (str): Input text
        model (str): Embedding model name

    Returns:
        List[float]: Embedding vector
    """
    text = text.replace("\n", " ")  # OpenAI recommends removing newlines
    response = client.embeddings.create(
        input=[text],
        model=model,
    )
    return response.data[0].embedding
