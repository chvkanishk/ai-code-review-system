from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
import time

from shared.database import Base, engine
from app.webhook_handler import router as webhook_router

app = FastAPI(title="AI Code Review System API Gateway")


def wait_for_postgres(max_retries=20, delay=1):
    """Retry DB connection until Postgres is ready."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                return True
        except OperationalError:
            print(f"[api-gateway] Waiting for Postgres... attempt {attempt + 1}/{max_retries}")
            time.sleep(delay)
    raise Exception("Postgres did not become ready in time")


@app.on_event("startup")
def on_startup():
    print("[api-gateway] Startup: checking database readiness...")
    wait_for_postgres()
    print("[api-gateway] Postgres is ready. Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("[api-gateway] Database initialized.")


# Routers
app.include_router(webhook_router, prefix="/webhooks", tags=["webhooks"])


@app.get("/")
def root():
    return {"status": "API Gateway running"}
