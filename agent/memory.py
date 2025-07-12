import httpx, os

API = os.getenv("MEMORY_API", "http://localhost:8000")

async def remember_question(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/add-question",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]

async def search_similar_questions(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/search-question",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]

async def remember_context(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/add-context",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]

async def search_similar_contexts(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/search-context",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]

async def remember_answer(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/add-answer",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]

async def search_similar_answers(text, embedding):
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/search-answer",
                         json={"content": text, "embedding": embedding})
    return r.json()["id"]
