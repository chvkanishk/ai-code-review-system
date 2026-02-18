import sys
import time

# Ensure Python can import /app/shared
sys.path.append("/app")

from shared.database import init_db, SessionLocal, PRAnalysis
from shared.redis_client import redis_client


POLL_INTERVAL_SECONDS = 1


def wait_for_db():
    """Retry connecting to Postgres until it is ready."""
    for i in range(15):
        try:
            # Try initializing DB (this will connect to Postgres)
            init_db()
            print("[worker] Database is ready")
            return
        except Exception as e:
            print(f"[worker] Database not ready yet, retrying... ({i+1}/15)")
            time.sleep(2)

    raise RuntimeError("Database never became ready after retries")


def process_job(job: dict):
    pr_number = job.get("pr_number")
    print(f"[worker] Processing job: PR #{pr_number}")

    db = SessionLocal()
    try:
        record = PRAnalysis(
            pr_number=pr_number,
            status="completed",
            message="Processed without AI (Phase 1)"
        )
        db.add(record)
        db.commit()
        print(f"[worker] Job completed for PR #{pr_number}")
    finally:
        db.close()


def main():
    print("[worker] Starting worker...")

    # Wait for Postgres to be ready BEFORE doing anything else
    wait_for_db()

    print("[worker] Ready for jobs")

    while True:
        job = redis_client.pop_job(block=True, timeout=5)
        if job is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue
        process_job(job)


if __name__ == "__main__":
    main()
