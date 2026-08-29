"""Tiny production-shaped API used in the live demo."""

import os

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="JKUAT Cloud Workshop API",
    description="Local-to-AWS demo service for From Backend Code to the Cloud.",
    version="1.0.0",
)


class Echo(BaseModel):
    message: str


def _log(message: str) -> None:
    print(message, flush=True)


@app.get("/health")
def health():
    stage = os.getenv("APP_STAGE", "local")
    _log(f"GET /health stage={stage}")
    return {
        "status": "ok",
        "service": "workshop-api",
        "stage": stage,
        "secret_loaded": bool(os.getenv("WORKSHOP_SECRET")),
        "database": "configured" if os.getenv("DATABASE_URL") else "not-attached",
    }


@app.get("/")
def root():
    _log("GET /")
    return {
        "talk": "From Backend Code to the Cloud",
        "host": "AWS Student Builder Group at JKUAT",
        "hint": "Hit /health, then POST /echo, then deploy the same image to AWS.",
        "stage": os.getenv("APP_STAGE", "local"),
    }


@app.post("/echo")
def echo(body: Echo):
    _log(f"POST /echo message_length={len(body.message)}")
    return {"ok": True, "echo": body.message, "ready_for_aws": True}
