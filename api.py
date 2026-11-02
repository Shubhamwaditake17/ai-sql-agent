"""FastAPI backend. Run: uvicorn api:api --reload"""
from fastapi import FastAPI
from pydantic import BaseModel
from agent import ask

api = FastAPI(title="AI SQL Agent")


class Query(BaseModel):
    question: str
    session_id: str = "default"


@api.post("/ask")
def ask_endpoint(q: Query):
    return ask(q.question, q.session_id)
