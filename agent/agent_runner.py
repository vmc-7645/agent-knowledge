"""
agent/agent_runner.py  –  CLI chat with rich-colored pizzazz
"""

import os, sys, argparse, asyncio, textwrap
from typing import List

import requests
from dotenv import load_dotenv
import weave
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

# ---------------------------------------------------------------------
# ENV + CLI
# ---------------------------------------------------------------------
load_dotenv()
SERVER_URL   = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
WEAVE_PROJ   = os.getenv("WEAVE_PROJECT", "wandbhackathon")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.25"))

parser = argparse.ArgumentParser()
parser.add_argument("--persona", default="your helpful assistant")
args = parser.parse_args()
persona = args.persona

client  = OpenAI()
weave.init(WEAVE_PROJ)

console = Console()

# ---------------------------------------------------------------------
# Helper: thin wrapper around FastAPI
# ---------------------------------------------------------------------
def api(path: str, method="post", **kw):
    fn = getattr(requests, method)
    res = fn(f"{SERVER_URL}{path}", timeout=30, **kw)
    res.raise_for_status()
    return res.json()

# ---------------------------------------------------------------------
# KB helpers
# ---------------------------------------------------------------------
def get_or_create_question(text: str):
    hits = api("/search-question", json={"query": text, "k": 5})
    if hits and hits[0]["distance"] <= SIM_THRESHOLD:
        return hits[0]["id"], hits
    qid = api("/add-question", json={"content": text})["id"]
    return qid, []

def fetch_answers(qid: int, limit=3):
    return api(f"/answers/{qid}?limit={limit}", method="get")

def save_answer(qid: int, content: str):
    api("/add-answer", json={"question_id": qid, "content": content, "is_solution": False})

# ---------------------------------------------------------------------
# LLM wrapper
# ---------------------------------------------------------------------
@weave.op()
def ask_llm(question: str, context: List[str], persona: str) -> str:
    sys_prompt = f"You are {persona}. Keep answers concise (≤5 sentences)."
    msgs = [{"role": "system", "content": sys_prompt}]
    msgs += [{"role": "system", "content": f"Previous relevant answer: {snip}"} for snip in context]
    msgs.append({"role": "user", "content": question})

    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return resp.choices[0].message.content.strip()

# ---------------------------------------------------------------------
# CLI loop
# ---------------------------------------------------------------------
async def chat():
    console.print(textwrap.dedent(f"""
        [bold]Persona:[/bold] {persona}
        [bold]Model:[/bold] gpt-4o-mini
        ---
        Type 'exit' to quit.
    """).strip())

    while True:
        try:
            question = console.input("[bold]You > [/bold]")
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if question.lower() in {"exit", "quit"}:
            break

        # --- DB lookup ------------------------------------------------
        qid, hits = get_or_create_question(question)
        console.print(
            f"[#666666]Found {len(hits)} similar questions in knowledge-base.[/]"
        )

        # --- Harvest context -----------------------------------------
        ctx: List[str] = []
        for hit in hits:
            for ans in fetch_answers(hit['id']):
                ctx.append(ans['content'])
                if len(ctx) >= 3:
                    break
            if len(ctx) >= 3:
                break

        # --- Ask LLM --------------------------------------------------
        answer = ask_llm(question, ctx, persona)
        console.print(Markdown(f"**Agent >** <span style='color:#b0ffb0'>{answer}</span>"))

        # --- Save back to DB -----------------------------------------
        try:
            save_answer(qid, answer)
            console.print("[#666666]Adding answer to database.[/]")
        except Exception as exc:
            console.print(f"[red][warning][/red] failed to save answer → {exc}", style="red")

if __name__ == "__main__":
    asyncio.run(chat())
