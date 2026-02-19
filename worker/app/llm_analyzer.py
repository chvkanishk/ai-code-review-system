"""
LLM Analyzer - Uses Ollama to analyze code
"""
import logging
import sys
import ollama

sys.path.append('/app')
from shared.config import settings

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Analyzes code using local LLM (Ollama)"""
    
    def __init__(self):
        self.model = "codellama"
        self.ollama_host = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        # Create Ollama client with custom host
        self.client = ollama.Client(host=self.ollama_host)
        logger.info(f"LLM Analyzer initialized with model: {self.model}")
        logger.info(f"Connecting to Ollama at: {self.ollama_host}")
    
    def analyze_pr(self, pr_number, pr_title, code_issues):
        """
        Analyze PR using LLM
        
        Args:
            pr_number: PR number
            pr_title: PR title
            code_issues: List of issues found by code analyzer
        
        Returns:
            Analysis result from LLM
        """
        try:
            # Build prompt for LLM
            prompt = self._build_prompt(pr_title, code_issues)
            
            logger.info(f"🤖 Asking AI to review PR #{pr_number}...")
            
            # Call Ollama using the client
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer. Provide brief, constructive feedback."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 200
                }
            )
            
            analysis = response['message']['content']
            
            logger.info(f"✅ AI analysis completed for PR #{pr_number}")
            
            return {
                "summary": analysis,
                "model": self.model,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            return {
                "summary": f"AI analysis unavailable: {str(e)}",
                "model": self.model,
                "success": False,
                "error": str(e)
            }
    
    def _build_prompt(self, pr_title, code_issues):
        """Build prompt for LLM analysis"""
        
        if not code_issues:
            return f"""
Review this Pull Request:

Title: {pr_title}

No code issues were detected by automated checks.

Please provide a brief summary (2-3 sentences) of what to verify manually.
"""
        
        issues_text = "\n".join([
            f"- {issue['severity'].upper()}: {issue['message']} (line {issue['line']})"
            for issue in code_issues[:5]
        ])
        
        prompt = f"""
Review this Pull Request:

Title: {pr_title}

Automated checks found these issues:
{issues_text}

Please provide:
1. Overall assessment (1 sentence)
2. Most critical issue to fix
3. One suggestion for improvement

Keep response under 100 words.
"""
        
        return prompt