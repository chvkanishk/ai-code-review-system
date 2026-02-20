"""
Slack Notifier - Sends notifications to Slack
"""
import logging
import sys
import requests
import json

sys.path.append('/app')
from shared.config import settings

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Send notifications to Slack"""
    
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        if not self.webhook_url:
            logger.warning("⚠️  No Slack webhook URL provided - Slack notifications disabled")
        else:
            logger.info("✅ Slack notifier initialized")
    
    def send_review_notification(self, pr_number, pr_title, repo_owner, repo_name, 
                                 issues_count, ai_summary, processing_time):
        """
        Send PR review notification to Slack
        
        Args:
            pr_number: PR number
            pr_title: PR title
            repo_owner: Repository owner
            repo_name: Repository name
            issues_count: Number of issues found
            ai_summary: AI analysis summary
            processing_time: Time taken to process
        
        Returns:
            True if successful
        """
        if not self.webhook_url:
            return False
        
        try:
            # Determine color based on issues
            if issues_count == 0:
                color = "#36a64f"  # Green
                status_emoji = "✅"
            elif issues_count <= 3:
                color = "#FFA500"  # Orange
                status_emoji = "⚠️"
            else:
                color = "#FF0000"  # Red
                status_emoji = "🔴"
            
            # Build GitHub PR URL
            pr_url = f"https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}" if repo_owner and repo_name else ""
            
            # Create Slack message with blocks (rich formatting)
            payload = {
                "text": f"🤖 Code Review Complete for PR #{pr_number}",
                "attachments": [
                    {
                        "color": color,
                        "blocks": [
                            {
                                "type": "header",
                                "text": {
                                    "type": "plain_text",
                                    "text": f"{status_emoji} Code Review Complete",
                                    "emoji": True
                                }
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*PR:*\n#{pr_number} - {pr_title}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Repository:*\n{repo_owner}/{repo_name}" if repo_owner else "*Repository:*\nDemo PR"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "fields": [
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Issues Found:*\n{issues_count}"
                                    },
                                    {
                                        "type": "mrkdwn",
                                        "text": f"*Processing Time:*\n{processing_time:.2f}s"
                                    }
                                ]
                            },
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"*AI Analysis:*\n{ai_summary[:200]}..."
                                }
                            }
                        ]
                    }
                ]
            }
            
            # Add button to view PR if URL available
            if pr_url:
                payload["attachments"][0]["blocks"].append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View PR on GitHub",
                                "emoji": True
                            },
                            "url": pr_url,
                            "style": "primary"
                        }
                    ]
                })
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Slack notification sent for PR #{pr_number}")
                return True
            else:
                logger.error(f"Slack notification failed: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def send_error_notification(self, pr_number, error_message):
        """Send error notification to Slack"""
        if not self.webhook_url:
            return False
        
        try:
            payload = {
                "text": f"❌ Code Review Failed for PR #{pr_number}",
                "attachments": [
                    {
                        "color": "#FF0000",
                        "text": f"*Error:* {error_message}"
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False