from pydantic import BaseModel

class WebhookPayload(BaseModel):
    pr_number: int
