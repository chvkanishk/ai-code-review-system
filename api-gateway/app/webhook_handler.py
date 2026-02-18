from fastapi import APIRouter
from shared.redis_client import redis_client
from .models import WebhookPayload

def handle_webhook(payload: WebhookPayload):
    job = {"pr_number": payload.pr_number}
    redis_client.push_job(job)
    return {"message": "Queued", "pr_number": payload.pr_number}
