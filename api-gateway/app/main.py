"""
API Gateway - Receives webhooks and queues jobs
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append('/app')

from shared import settings, redis_client, init_db, db_health_check

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting API Gateway...")
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("👋 API Gateway shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Code Review API",
    description="Webhook receiver for GitHub PRs",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint - shows API info"""
    return {
        "service": "AI Code Review API Gateway",
        "version": "0.1.0",
        "status": "running",
        "phase": "1 - Foundation",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check - verifies Redis and DB are working"""
    redis_healthy = redis_client.health_check()
    db_healthy = db_health_check()
    queue_length = redis_client.get_queue_length()
    
    healthy = redis_healthy and db_healthy
    
    return {
        "status": "healthy" if healthy else "unhealthy",
        "redis": redis_healthy,
        "database": db_healthy,
        "queue_length": queue_length,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook")
async def github_webhook(request: Request):
    """
    Receive GitHub webhook and queue it for processing
    """
    try:
        # Get the JSON payload
        payload = await request.json()
        
        logger.info("📨 Webhook received")
        
        # Extract PR info (simplified for Phase 1)
        pr_number = payload.get("number", 0)
        pr_title = payload.get("pull_request", {}).get("title", "Unknown")
        action = payload.get("action", "unknown")
        
        # Create a job
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "pr_number": pr_number,
            "pr_title": pr_title,
            "action": action,
            "queued_at": datetime.utcnow().isoformat()
        }
        
        # Push to Redis queue
        success = redis_client.push_job(job_data)
        
        if success:
            logger.info(f"✅ Queued: PR #{pr_number} (job: {job_id})")
            return JSONResponse(
                content={
                    "message": "PR queued for analysis",
                    "pr_number": pr_number,
                    "job_id": job_id
                },
                status_code=202  # Accepted
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to queue job")
    
    except Exception as e:
        logger.error(f"❌ Webhook failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/status")
async def queue_status():
    """Get current queue status"""
    try:
        queue_length = redis_client.get_queue_length()
        return {
            "queue_length": queue_length,
            "status": "processing" if queue_length > 0 else "idle",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)