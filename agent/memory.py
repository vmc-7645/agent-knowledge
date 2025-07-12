def search_similar_questions(text: str) -> list:
    embedding = get_embedding(text)
    # httpx.post("http://localhost:8000/search-question", json={"embedding": embedding.tolist()})
    pass
