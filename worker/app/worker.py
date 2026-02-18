"""
Worker - Polls queue and processes jobs
"""
import logging
import sys
import time
from datetime import datetime

sys.path.append('/app')

from shared import redis_client, settings, SessionLocal, PRAnalysis

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Worker:
    """Worker that processes code review jobs"""
    
    def __init__(self):
        self.running = True
        logger.info("🤖 Worker initialized")
    
    def process_job(self, job_data):
        """
        Process a single job
        
        Args:
            job_data: Job information from queue
        
        Returns:
            True if successful
        """
        start_time = time.time()
        job_id = job_data.get("job_id")
        pr_number = job_data.get("pr_number")
        pr_title = job_data.get("pr_title", "Unknown")
        
        logger.info("=" * 60)
        logger.info(f"⚙️  Processing: PR #{pr_number}")
        logger.info(f"   📝 Title: {pr_title}")
        logger.info(f"   🆔 Job ID: {job_id}")
        
        try:
            # Create database record
            db = SessionLocal()
            
            pr_analysis = PRAnalysis(
                pr_number=pr_number,
                pr_title=pr_title,
                status="processing"
            )
            db.add(pr_analysis)
            db.commit()
            db.refresh(pr_analysis)
            
            # Phase 1: Just simulate work (no actual analysis yet)
            logger.info(f"   🔍 Analyzing... (Phase 1 - simulation)")
            time.sleep(2)  # Simulate processing time
            
            # Update database with result
            pr_analysis.status = "completed"
            pr_analysis.message = (
                f"Phase 1: Job processed successfully. "
                f"Completed at {datetime.utcnow().isoformat()}"
            )
            db.commit()
            
            duration = time.time() - start_time
            logger.info(f"✅ Completed in {duration:.2f}s")
            logger.info("=" * 60)
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Job failed: {e}")
            logger.info("=" * 60)
            
            # Try to update database with error
            try:
                pr_analysis.status = "failed"
                pr_analysis.message = f"Error: {str(e)}"
                db.commit()
                db.close()
            except:
                pass
            
            return False
    
    def run(self):
        """Main worker loop - runs forever"""
        logger.info("🚀 Worker started!")
        logger.info(f"   📡 Polling queue: {settings.REDIS_QUEUE_NAME}")
        logger.info(f"   ⏱️  Poll interval: 5 seconds")
        logger.info(f"   🔗 Redis: {settings.REDIS_HOST}")
        logger.info(f"   🗄️  Database: {settings.POSTGRES_HOST}")
        logger.info("")
        logger.info("⏳ Waiting for jobs...")
        
        while self.running:
            try:
                # Poll for jobs (blocks for up to 5 seconds)
                job_data = redis_client.pop_job(timeout=5)
                
                if job_data:
                    # Process the job
                    self.process_job(job_data)
                else:
                    # No job available - this is normal
                    pass
            
            except KeyboardInterrupt:
                logger.info("")
                logger.info("👋 Worker shutting down...")
                self.running = False
            except Exception as e:
                logger.error(f"⚠️  Worker error: {e}")
                time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    worker = Worker()
    worker.run()