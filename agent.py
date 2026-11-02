"""LangGraph agent:
schema -> generate SQL -> validate -> execute -> explain
Errors loop back to 'generate' (self-correction), max MAX_RETRIES times.
"""
import os
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from db import get_schema, run_query, DIALECT
from validator import validate

MAX_RETRIES = 2
llm = ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL", "gemini-3.8-flash"), temperature=0)


class State(TypedDict, total=False):
    question: str
    history: list      # past (question, sql) pairs -> follow-up support
    schema: str
    sql: str
    error: str
    columns: list
    rows: list
    answer: str
    attempts: int


def to_text(msg) -> str:
    """LLM reply -> plain string (newer Gemini returns a list of blocks)."""
    c = msg.content
    if isinstance(c, str):
        return c
    return "".join(b if isinstance(b, str) else b.get("text", "") for b in c)


def strip_fences(text: str) -> str:
    return text.replace("```sql", "").replace("```", "").strip()


# ---- nodes ----------------------------------------------------------------
def load_schema(s: State):
    return {"schema": get_schema(), "attempts": 0, "error": "", "sql": ""}


def generate(s: State):
    prompt = (
        f"You write {DIALECT} SQL. Return ONLY one SELECT query, no explanation.\n\n"
        f"Schema:\n{s['schema']}\n\n"
        f"Previous questions (for follow-ups):\n{s.get('history', [])[-3:]}\n\n"
        f"Question: {s['question']}\n"
    )
    if s.get("error"):  # self-correction
        prompt += f"\nYour last query failed.\nSQL: {s['sql']}\nError: {s['error']}\nFix it.\n"
    return {"sql": strip_fences(to_text(llm.invoke(prompt)))}


def check(s: State):
    ok, result = validate(s["sql"])
    if ok:
        return {"sql": result, "error": ""}
    return {"error": result, "attempts": s["attempts"] + 1}


def execute(s: State):
    try:
        cols, rows = run_query(s["sql"])
        return {"columns": cols, "rows": rows, "error": ""}
    except Exception as e:
        return {"error": str(e), "attempts": s["attempts"] + 1}


def explain(s: State):
    prompt = (
        f"Question: {s['question']}\nSQL: {s['sql']}\n"
        f"Columns: {s['columns']}\nRows (first 20): {s['rows'][:20]}\n"
        "Answer the question in 1-3 plain sentences."
    )
    history = s.get("history", []) + [(s["question"], s["sql"])]
    return {"answer": to_text(llm.invoke(prompt)), "history": history}


def give_up(s: State):
    return {"answer": f"Sorry, I couldn't answer that. Last error: {s['error']}",
            "columns": [], "rows": []}


# ---- routing --------------------------------------------------------------
def route(next_node: str):
    def _route(s: State):
        if not s.get("error"):
            return next_node
        return "give_up" if s["attempts"] > MAX_RETRIES else "generate"
    return _route


# ---- graph ----------------------------------------------------------------
g = StateGraph(State)
for name, fn in [("load_schema", load_schema), ("generate", generate), ("check", check),
                 ("execute", execute), ("explain", explain), ("give_up", give_up)]:
    g.add_node(name, fn)

g.set_entry_point("load_schema")
g.add_edge("load_schema", "generate")
g.add_edge("generate", "check")
g.add_conditional_edges("check", route("execute"), ["execute", "generate", "give_up"])
g.add_conditional_edges("execute", route("explain"), ["explain", "generate", "give_up"])
g.add_edge("explain", END)
g.add_edge("give_up", END)

app = g.compile(checkpointer=MemorySaver())  # memory per session_id


def ask(question: str, session_id: str = "default") -> dict:
    cfg = {"configurable": {"thread_id": session_id}}
    out = app.invoke({"question": question}, cfg)
    return {"answer": out["answer"], "sql": out.get("sql", ""),
            "columns": out.get("columns", []), "rows": out.get("rows", [])}


if __name__ == "__main__":  # quick CLI test
    while True:
        q = input("\nAsk: ")
        print(ask(q))
