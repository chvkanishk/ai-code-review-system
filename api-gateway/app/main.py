import time
from fastapi import FastAPI
from shared.database import init_db
from app.webhook_handler import router as webhook_router

app = FastAPI()


def wait_for_db():
    """Retry connecting to Postgres until it is ready."""
    for i in range(15):
        try:
            init_db()
            print("[api-gateway] Database is ready")
            return
        except Exception as e:
            print(f"[api-gateway] Database not ready yet, retrying... ({i+1}/15)")
            time.sleep(2)

    raise RuntimeError("Database never became ready")


@app.on_event("startup")
def startup_event():
    wait_for_db()
    print("[api-gateway] Startup complete")


# Register webhook routes
app.include_router(webhook_router)
