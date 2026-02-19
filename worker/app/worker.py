"""
Worker - Polls queue and processes jobs with AI
"""
import logging
import sys
import time
from datetime import datetime
import json

sys.path.append('/app')

from shared import redis_client, settings, SessionLocal, PRAnalysis
from app.code_analyzer import CodeAnalyzer
from app.llm_analyzer import LLMAnalyzer

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Worker:
    """Worker that processes code review jobs with AI"""
    
    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.llm_analyzer = LLMAnalyzer()
        self.running = True
        logger.info("🤖 Worker initialized (Phase 2 - with AI + Caching)")
    
    def process_job(self, job_data):
        """
        Process a single job with AI analysis and caching
        
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
            
            # CHECK CACHE FIRST!
            cache_key = f"pr_analysis:{pr_number}"
            cached_result = redis_client.cache_get(cache_key)
            
            if cached_result:
                logger.info(f"   ⚡ CACHE HIT! Using cached analysis")
                cached_data = json.loads(cached_result)
                
                pr_analysis.status = "completed"
                pr_analysis.message = f"[CACHED] {cached_data['message']}"
                db.commit()
                
                duration = time.time() - start_time
                logger.info(f"   ⚡ Retrieved from cache")
                logger.info(f"✅ Completed in {duration:.2f}s (CACHED!)")
                logger.info("=" * 60)
                
                db.close()
                return True
            
            # CACHE MISS - Do real analysis
            logger.info(f"   🔍 Running code analysis...")
            
            # Sample code to analyze
            sample_code = f"""
def process_user_login(username):
    password = "hardcoded123"  # TODO: Move to environment variable
    console.log("Processing login for: " + username)
    if len(username) > 0:
        return True
    return False
"""
            
            # Run code analyzer
            code_issues = self.code_analyzer.analyze_code(sample_code)
            logger.info(f"   📋 Found {len(code_issues)} code issues")
            
            # Run LLM analyzer
            logger.info(f"   🤖 Getting AI insights...")
            llm_result = self.llm_analyzer.analyze_pr(
                pr_number=pr_number,
                pr_title=pr_title,
                code_issues=code_issues
            )
            
            # Build result message
            result_message = f"""
Phase 2 Analysis Complete:
- Code Issues Found: {len(code_issues)}
- AI Analysis: {llm_result['summary'][:200]}...

Details:
{', '.join([f"{i['type']} (line {i['line']})" for i in code_issues[:3]])}
"""
            
            # Update database with results
            pr_analysis.status = "completed"
            pr_analysis.message = result_message
            db.commit()
            
            # CACHE THE RESULT!
            cache_data = {
                "message": result_message,
                "issues": len(code_issues),
                "ai_summary": llm_result['summary']
            }
            redis_client.cache_set(cache_key, json.dumps(cache_data), ttl=86400)  # 24 hours
            logger.info(f"   💾 Cached result for future requests")
            
            duration = time.time() - start_time
            logger.info(f"   📊 Issues: {len(code_issues)}")
            logger.info(f"   💬 AI: {llm_result['summary'][:80]}...")
            logger.info(f"✅ Completed in {duration:.2f}s")
            logger.info("=" * 60)
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
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
        logger.info("🚀 Worker started (Phase 2 - AI Enabled with Caching)!")
        logger.info(f"   📡 Polling queue: {settings.REDIS_QUEUE_NAME}")
        logger.info(f"   ⏱️  Poll interval: 5 seconds")
        logger.info(f"   🔗 Redis: {settings.REDIS_HOST}")
        logger.info(f"   🗄️  Database: {settings.POSTGRES_HOST}")
        logger.info(f"   🤖 AI Model: codellama")
        logger.info(f"   ⚡ Caching: Enabled (24h TTL)")
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