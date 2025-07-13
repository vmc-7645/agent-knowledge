"""agent/agent_runner.py – CLI chat with Weave + FastAPI store (rev-4)
--------------------------------------------------------------------
Features
  • Wider semantic search (k=10, threshold 0.35).
  • After every reply the user can type  [enter]  to continue or  y  to mark the answer as the accepted solution (calls /mark-solution).
  • Embeddings & context handled server-side (client sends nulls).
Routes used
  • POST  /search-question   {content, k}
  • POST  /add-question      {content}
  • GET   /answers/{qid}?limit=n
  • POST  /add-answer        {question_id, content, context_id|null, embedding|null, is_solution}
  • POST  /mark-solution     {answer_id}
"""

import os, argparse, asyncio, textwrap
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
SERVER_URL    = os.getenv("SERVER_URL", "http://127.0.0.1:8000")
WEAVE_PROJECT = os.getenv("WEAVE_PROJECT", "wandbhackathon")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "-0.6"))
SEARCH_K      = int(os.getenv("SEARCH_K", "10"))

parser = argparse.ArgumentParser()
parser.add_argument("--persona", default="your helpful assistant")
args     = parser.parse_args()
persona  = args.persona

client = OpenAI()
weave.init(WEAVE_PROJECT)
console = Console()

# ---------------------------------------------------------------------
# Helper: thin wrapper around FastAPI
# ---------------------------------------------------------------------

def api(path: str, method: str = "post", **kw):
    fn = getattr(requests, method.lower())
    res = fn(f"{SERVER_URL}{path}", timeout=30, **kw)
    res.raise_for_status()
    if res.headers.get("content-type", "").startswith("application/json"):
        return res.json()
    return res.text

# ---------------------------------------------------------------------
# KB helpers
# ---------------------------------------------------------------------

def get_or_create_question(text: str):
    hits = api("/search-question", json={"content": text, "k": SEARCH_K})
    if hits and hits[0]["distance"] <= SIM_THRESHOLD:
        print(f"nearest distance = {hits[0]['distance']:.3f}")
        return hits[0]["id"], hits
    qid = api("/add-question", json={"content": text})["id"]
    return qid, []

def fetch_answers(qid: int, limit: int = 3):
    return api(f"/answers/{qid}?limit={limit}", method="get")


def save_answer(qid: int, content: str) -> int:
    return api(
        "/add-answer",
        json={
            "question_id": qid,
            "context_id": None,
            "content": content,
            "embedding": None,
            "is_solution": False,
        },
    )["id"]


def mark_solution(ans_id: int):
    api("/mark-solution", json={"answer_id": ans_id})

# ---------------------------------------------------------------------
# LLM wrapper
# ---------------------------------------------------------------------

@weave.op()
def ask_llm(question: str, context: List[str], persona: str) -> str:
    system_prompt = f"You are {persona}. Keep answers concise (≤5 sentences)."
    msgs = [{"role": "system", "content": system_prompt}]
    msgs += [
        {"role": "system", "content": f"Previous relevant answer: {snip}"}
        for snip in context
    ]
    msgs.append({"role": "user", "content": question})

    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
    return resp.choices[0].message.content.strip()

# ---------------------------------------------------------------------
# CLI loop
# ---------------------------------------------------------------------

async def chat():
    console.print(
        textwrap.dedent(
            f"""
            [bold]Persona:[/bold] {persona}
            [bold]Model:[/bold] gpt-4o-mini
            ---
            Type 'exit' to quit.
        """
        ).strip()
    )

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
        console.print(f"[#666666]Found {len(hits)} similar questions in knowledge-base.[/]")

        # --- Harvest context -----------------------------------------
        ctx: List[str] = []
        for hit in hits:
            for ans in fetch_answers(hit["id"], limit=3):
                ctx.append(ans["answer_content"])
                if len(ctx) >= 3:
                    break
            if len(ctx) >= 3:
                break

        # --- Ask LLM --------------------------------------------------
        answer = ask_llm(question, ctx, persona)
        console.print(Markdown(f"**Agent >** {answer}"))

        # --- Save to DB ----------------------------------------------
        ans_id: int | None = None
        try:
            ans_id = save_answer(qid, answer)
            console.print("[#666666]Answer added to database.[/]")
        except Exception as exc:
            console.print(f"[red]Failed to save answer → {exc}[/red]")

        # --- Optional mark-solution ----------------------------------
        if ans_id is not None:
            flag = console.input("[#666666]Mark as solution? (y/N) > [/] ").strip().lower()
            if flag == "y":
                try:
                    mark_solution(ans_id)
                    console.print("[#666666]Marked as solution.[/]")
                except Exception as exc:
                    console.print(f"[red]Failed to mark solution → {exc}[/red]")

if __name__ == "__main__":
    asyncio.run(chat())
