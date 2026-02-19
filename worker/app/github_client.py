"""
GitHub Client - Fetches PR code and posts comments
"""
import logging
import sys
from github import Github
import requests

sys.path.append('/app')
from shared.config import settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self):
        if not settings.GITHUB_TOKEN:
            logger.warning("⚠️  No GitHub token provided - GitHub features disabled")
            self.client = None
        else:
            self.client = Github(settings.GITHUB_TOKEN)
            logger.info("✅ GitHub client initialized")
    
    def get_pr_files(self, repo_owner, repo_name, pr_number):
        """
        Fetch files changed in a PR
        
        Args:
            repo_owner: Repository owner (e.g., 'facebook')
            repo_name: Repository name (e.g., 'react')
            pr_number: PR number
        
        Returns:
            List of files with their content
        """
        if not self.client:
            logger.error("GitHub client not initialized")
            return []
        
        try:
            repo = self.client.get_repo(f"{repo_owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                # Only analyze code files (skip images, binaries, etc.)
                if self._is_code_file(file.filename):
                    # Get file content
                    try:
                        content = self._fetch_file_content(file.raw_url)
                        files.append({
                            "filename": file.filename,
                            "content": content,
                            "additions": file.additions,
                            "deletions": file.deletions,
                            "changes": file.changes
                        })
                        logger.info(f"   📄 Fetched: {file.filename}")
                    except Exception as e:
                        logger.warning(f"Could not fetch {file.filename}: {e}")
            
            return files
        
        except Exception as e:
            logger.error(f"Failed to fetch PR files: {e}")
            return []
    
    def post_review_comment(self, repo_owner, repo_name, pr_number, comment_body):
        """
        Post a review comment on a PR
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            pr_number: PR number
            comment_body: Comment text
        
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            repo = self.client.get_repo(f"{repo_owner}/{repo_name}")
            pr = repo.get_pull(pr_number)
            
            # Post comment
            pr.create_issue_comment(comment_body)
            
            logger.info(f"✅ Posted review comment to PR #{pr_number}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            return False
    
    def _is_code_file(self, filename):
        """Check if file is a code file we should analyze"""
        code_extensions = [
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.cs', '.scala',
            '.html', '.css', '.scss', '.sql', '.sh', '.yaml', '.yml', '.json'
        ]
        return any(filename.endswith(ext) for ext in code_extensions)
    
    def _fetch_file_content(self, url):
        """Fetch file content from raw URL"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Limit content size (max 100KB per file)
        content = response.text[:100000]
        return content