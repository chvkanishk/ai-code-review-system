from fastapi import APIRouter, HTTPException
from shared.redis_client import redis_client
import json

router = APIRouter()

@router.post("/github")
def github_webhook(payload: dict):
    pr_number = payload.get("pr_number")
    if not pr_number:
        raise HTTPException(status_code=400, detail="Missing pr_number")

    job = {"pr_number": pr_number}

    # Use your existing queue system
    redis_client.push_job(job)

    return {"status": "queued", "pr_number": pr_number}
