from fastapi import FastAPI
from sqlalchemy import text

from reconciliation.db import engine

app = FastAPI(title="Invoice Reconciliation Agent")


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}