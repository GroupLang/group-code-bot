import re
from typing import Optional, Tuple
from loguru import logger
from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from utils.telegram_utils import send_message

GITHUB_ISSUE_PATTERN = r'(?:https?://)?github\.com/([^/]+)/([^/]+)/issues/(\d+)'

def parse_github_issue(text: str) -> Optional[Tuple[str, str, str]]:
    """Extract owner, repo and issue number from GitHub issue URL.
    
    Returns:
        Tuple of (owner, repo, issue_number) or None if no match
    """
    match = re.search(GITHUB_ISSUE_PATTERN, text)
    return match.groups() if match else None

async def handle_github_issue(chat_id: int, owner: str, repo: str, issue_num: str) -> None:
    """Process a GitHub issue link and create corresponding instance.
    
    Args:
        chat_id: Telegram chat ID
        owner: GitHub repository owner
        repo: Repository name 
        issue_num: Issue number
    """
    repo_url = f"https://github.com/{owner}/{repo}"
    issue_number = int(issue_num)
    issue_url = f"{repo_url}/issues/{issue_number}"
    
    async with AgentMarketClient() as client:
        try:
            # Add repository
            repo_data = {
                "repo_url": issue_url,
                "default_reward": 0.04,
            }
            await client.add_repository(repo_data)

            # Get issue details and instance
            issues = await client.get_repository_issues(repo_url=issue_url)
            issue = next((i for i in issues if i['issue_number'] == issue_number), None)

            if not issue or not issue.get('instance_id'):
                send_message(chat_id, f"❌ Instance for issue #{issue_number} not found.")
                return

            # Store instance tracking
            instance_id = issue['instance_id']
            tracker = RequestTracker()
            await tracker.add_request(instance_id, chat_id)

            send_message(
                chat_id,
                f"✅ Created instance `{instance_id}` from GitHub issue #{issue_number}:\n"
                f"*{issue['title']}*\n\n"
            )
            
        except Exception as e:
            logger.error(f"Error handling GitHub issue: {e}")
            send_message(
                chat_id,
                f"❌ Failed to process GitHub issue: {str(e)}. Please try again later."
            )
