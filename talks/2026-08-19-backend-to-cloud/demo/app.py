"""Tiny production-shaped API used in the live demo."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="JKUAT Cloud Workshop API",
    description="Local-to-AWS demo service for From Backend Code to the Cloud.",
    version="1.0.0",
)


class Echo(BaseModel):
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "workshop-api", "stage": "local-or-cloud"}


@app.get("/")
def root():
    return {
        "talk": "From Backend Code to the Cloud",
        "host": "AWS Student Builder Group at JKUAT",
        "hint": "Hit /health, then POST /echo, then deploy the same image to AWS.",
    }


@app.post("/echo")
def echo(body: Echo):
    return {"ok": True, "echo": body.message, "ready_for_aws": True}
