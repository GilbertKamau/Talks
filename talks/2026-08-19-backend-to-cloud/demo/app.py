"""Tiny production-shaped API used in the live demo."""

import os
import re

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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


def _hide_secrets(text: str) -> str:
    return re.sub(r":[^:@/]+@", ":***@", text)[:220]


def check_database() -> dict:
    url = os.getenv("DATABASE_URL")
    if not url:
        return {"status": "not-attached"}
    try:
        import psycopg

        with psycopg.connect(url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1, current_database()")
                ping, name = cur.fetchone()
        return {"status": "connected", "ping": ping, "database_name": name, "engine": "PostgreSQL"}
    except Exception as exc:
        return {"status": "error", "detail": _hide_secrets(str(exc))}


@app.get("/health")
def health():
    db = check_database()
    stage = os.getenv("APP_STAGE", "local")
    _log(f"GET /health stage={stage} database={db['status']}")
    return {
        "status": "ok",
        "service": "workshop-api",
        "stage": stage,
        "secret_loaded": bool(os.getenv("WORKSHOP_SECRET") or os.getenv("DATABASE_URL")),
        "database": db["status"],
    }


@app.get("/db")
def db_check():
    result = check_database()
    _log(f"GET /db status={result['status']}")
    if result["status"] == "connected":
        return result
    code = 503 if result["status"] == "not-attached" else 502
    return JSONResponse(status_code=code, content=result)


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
