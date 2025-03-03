import os
import re
import time
import asyncio
from typing import Dict, Any, Optional
import requests
from loguru import logger

from utils.message_storage import (
    Config,
    get_chat_history,
    store_message,
    add_chat_id_if_reply,
    clear_chat_history
)
from services.bot.messages import (
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    INVALID_REWARD_FORMAT,
    REWARD_SUCCESS,
    SUCCESS_MESSAGES
)

from services.client import AgentMarketClient
from services.request_tracker import RequestTracker
from services.bot.provider import send_message_to_provider, parse_provider_mention
from utils.telegram_utils import send_message, escape_markdown
from utils.message_storage import get_from_reaction_to_message

BOT_MENTION_PATTERN = r'@group_code_bot\s+(.*)'
GITHUB_ISSUE_PATTERN = r'(?:https?://)?github\.com/([^/]+)/([^/]+)/issues/(\d+)'


async def handle_update(update: Dict[str, Any]) -> None:
    """Handle incoming updates from Telegram.
    
    Args:
        update: Update object from Telegram
    """
    try:
        if 'message' in update:
            await handle_message(update['message'])
        elif 'message_reaction' in update and update['message_reaction'].get('new_reaction'):
            reaction_message = get_from_reaction_to_message(update['message_reaction'])
            store_message(reaction_message['chat']['id'], reaction_message)
            
    except Exception as e:
        import traceback
        error_details = f"Error handling update: {e}\n"
        error_details += f"Traceback: {traceback.format_exc()}\n"
        
        # Get additional details if it's an HTTP error
        if hasattr(e, 'response') and e.response is not None:
            response = e.response
            # Check if response is an object or dict and extract status code
            if isinstance(response, dict) and 'status_code' in response:
                error_details += f"Status Code: {response['status_code']}\n"
            elif hasattr(response, 'status_code'):
                error_details += f"Status Code: {response.status_code}\n"
            
            # Check for text content
            if isinstance(response, dict) and 'text' in response:
                error_details += f"Response Content: {response['text']}\n"
            elif hasattr(response, 'text'):
                error_details += f"Response Content: {response.text}\n"
        
        logger.error(error_details)

async def handle_code_request(message: Dict[str, Any]) -> None:
    """Handle code request commands"""
    chat_id = message['chat']['id']
    command_text = message['text'].lower().split('@group_code_bot', 1)[1].strip()
    
    chat_history = await get_chat_history(chat_id)
    
    conversation = "\nPrevious conversation:\n"
    for msg in chat_history:
        username = msg.get('username', 'unknown')
        text = msg.get('text', '')
        conversation += f"{username}: {text}\n"
    
    command_text = f"{command_text}\n{conversation}"
    
    if not command_text:
        send_message(
            chat_id,
            "❌ Please provide a code request description after the command.",
        )
        return

    instance_data = {
        "background": command_text,
        "max_credit_per_instance": 0.04,
        "instance_timeout": 30,
        "gen_reward_timeout": 6000,
        "percentage_reward": 1,
    }
    
    async with AgentMarketClient() as client:
        response = await client.create_instance(instance_data)
    instance_id = response['id']
            
    tracker = RequestTracker()
    await tracker.add_request(instance_id, chat_id)
        
    try:
        # First try with simple formatting
        send_message(
            chat_id,
            f"✅ Instance created!\n\n"
            f"🔍 Instance ID: {instance_id}\n"
        )
    except Exception as e:
        logger.error(f"Failed to send instance creation message: {e}")
        # Fallback to even simpler message if needed
        send_message(
            chat_id,
            f"✅ Instance created with ID: {instance_id}"
        )

async def handle_github_issue_link(message: Dict[str, Any]) -> None:
    """Handle GitHub issue link detection using authorized endpoints."""
    chat_id = message['chat']['id']
    match = re.search(GITHUB_ISSUE_PATTERN, message['text'])
    if not match:
        return
        
    owner, repo, issue_num = match.groups()
    repo_url = f"https://github.com/{owner}/{repo}"
    issue_number = int(issue_num)
    
    async with AgentMarketClient() as client:
        try:
            # Include 'issue_url' in repo_data instead of 'issue_number'
            issue_url = f"{repo_url}/issues/{issue_number}"
            repo_data = {
                "repo_url": issue_url,
                "default_reward": 0.04,
            }
            try:
                try:
                    issues = await client.get_repository_issues(repo_url=issue_url)
                    return
                except Exception as e:
                    repo_url = repo_url.replace(owner, 'agentMarketBot') 
                    issue_url = f"{repo_url}/issues/{issue_number}"
                    issues = await client.get_repository_issues(repo_url=issue_url)
                    return
            except Exception as e:
                pass
            try:
                await client.add_repository(repo_data)
            except Exception as e:
                logger.error(f"Error adding repository: {e}")
                send_message(
                    chat_id,
                    f"❌ Failed to process GitHub issue {e}. Please try again later.",
                )
                return 

            time.sleep(61)

            try:
                repo_url = f"https://github.com/{owner}/{repo}"
                issue_url = f"{repo_url}/issues/{issue_number}"
                issues = await client.get_repository_issues(repo_url=issue_url)
            except Exception as e:
                repo_url = repo_url.replace(owner, 'agentMarketBot') 
                issue_url = f"{repo_url}/issues/{issue_number}"
                issues = await client.get_repository_issues(repo_url=issue_url)
            issue = next((issue for issue in issues if issue['issue_number'] == issue_number), None)

            if not issue or not issue.get('instance_id'):
                send_message(
                    chat_id,
                    f"❌ Instance for issue #{issue_number} not found.",
                )
                return

            instance_id = issue['instance_id']
            
            tracker = RequestTracker()
            await tracker.add_request(instance_id, chat_id)

            try:
                issue_body = issue.get('body', 'No description provided.')
                check_mark = "✅"
                # Try first with MarkdownV2 formatting
                message_text = (
                    f"{check_mark} Created instance `{instance_id}` from GitHub issue {issue_number}\n\n"
                    f"*Title:* {issue['title']}\n"
                    f"*Description:*\n{issue_body}\n"
                )
                send_message(
                    chat_id,
                    message_text,
                    parse_mode='MarkdownV2'
                )
            except Exception as e:
                logger.error(f"Failed to send formatted GitHub issue message: {e}")
                # Fallback to plain text with no markdown
                plain_message = (
                    f"✅ Created instance {instance_id} from GitHub issue {issue_number}\n\n"
                    f"Title: {issue['title']}\n"
                    f"Description:\n{issue_body}\n"
                )
                send_message(chat_id, plain_message)
        except Exception as e:
            import traceback
            error_details = f"Error handling GitHub issue: {e}\n"
            error_details += f"Traceback: {traceback.format_exc()}\n"
            
            # Get additional details if it's an HTTP error
            if hasattr(e, 'response') and e.response is not None:
                response = e.response
                # Check if response is an object or dict and extract status code
                if isinstance(response, dict) and 'status_code' in response:
                    error_details += f"Status Code: {response['status_code']}\n"
                elif hasattr(response, 'status_code'):
                    error_details += f"Status Code: {response.status_code}\n"
                
                # Check for text content
                if isinstance(response, dict) and 'text' in response:
                    error_details += f"Response Content: {response['text']}\n"
                elif hasattr(response, 'text'):
                    error_details += f"Response Content: {response.text}\n"
                
                # Add URL, method, headers, and body if available
                if isinstance(response, dict) and 'url' in response:
                    error_details += f"Request URL: {response['url']}\n"
                elif hasattr(response, 'url'):
                    error_details += f"Request URL: {response.url}\n"
                
                if hasattr(e.response, 'request') and e.response.request is not None:
                    if hasattr(e.response.request, 'method'):
                        error_details += f"Request Method: {e.response.request.method}\n"
                    if hasattr(e.response.request, 'headers'):
                        error_details += f"Request Headers: {e.response.request.headers}\n"
                    if hasattr(e.response.request, 'body'):
                        error_details += f"Request Body: {e.response.request.body}\n"
            
            logger.error(error_details)
            send_message(
                chat_id,
                f"❌ Failed to process GitHub issue: {str(e)}. Please try again later.",
            )

async def handle_new_chat_members(message: Dict[str, Any]) -> None:
    """Handle new members joining the chat"""
    chat_id = message['chat']['id']
    for member in message['new_chat_members']:
        if member.get('username') == "group_code_bot":
            try:
                set_bot_commands(chat_id)
                # Add small delay before sending welcome message to ensure bot is fully initialized in the chat
                await asyncio.sleep(1)
                
                # First try with no formatting to ensure the message gets delivered
                try:
                    # Remove markdown formatting symbols from welcome message
                    plain_welcome = WELCOME_MESSAGE.replace('*', '').replace('`', '')
                    send_message(chat_id, plain_welcome)
                except Exception as e:
                    logger.error(f"Failed to send plain welcome message to chat {chat_id}: {e}")
                    # Fallback to even simpler message if plain message fails
                    simple_message = "👋 Welcome to Group Code Bot! Type /help to see available commands."
                    send_message(chat_id, simple_message)
            except Exception as e:
                logger.error(f"Failed to send welcome message to chat {chat_id}: {e}")
                # We'll log but not re-raise the error to prevent the function from failing completely

async def handle_provider_reply(message: Dict[str, Any], replied_msg: Dict[str, Any]) -> bool:
    """Handle replies to provider messages"""
    chat_id = message['chat']['id']
    text = message['text']
    
    if 'text' not in replied_msg or 'message from' not in replied_msg['text'].lower():
        return False
        
    try:
        provider_id = replied_msg['text'].split('(')[1].split(')')[0]
        instance_info = replied_msg['text'].split('for instance: ')[1]
        instance_id = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', instance_info).group(0)

        chat_history = await get_chat_history(chat_id)
    
        conversation = "\nPrevious conversation:\n"
        for msg in chat_history:
            username = msg.get('username', 'unknown')
            text = msg.get('text', '')
            conversation += f"{username}: {text}\n"

        text = f"{text}\n{conversation}"

        await send_message_to_provider(chat_id, provider_id, text, instance_id=instance_id)
        return True
    except (IndexError, ValueError):
        logger.error("Failed to parse provider or instance ID from message")
        return False

async def handle_provider_mention(message: Dict[str, Any]) -> bool:
    """Handle direct provider mentions"""
    chat_id = message['chat']['id']
    text = message['text']
    
    if not text.startswith('@'):
        return False
        
    provider_info = parse_provider_mention(text)
    if not provider_info:
        return False
        
    provider_id, message_content, instance_id = provider_info

    chat_history = await get_chat_history(chat_id)
    
    conversation = "\nPrevious conversation:\n"
    for msg in chat_history:
        username = msg.get('username', 'unknown')
        text = msg.get('text', '')
        conversation += f"{username}: {text}\n"

    message_content = f"{message_content}\n{conversation}"
    
    await send_message_to_provider(chat_id, provider_id, message_content, instance_id=instance_id)
    return True

async def handle_message(message: Dict[str, Any]) -> None:
    """Main message handler that routes to specific handlers"""
    if 'new_chat_members' in message:
        await handle_new_chat_members(message)
        return
    
    if 'text' not in message:
        return

    if 'reply_to_message' in message:
        replied_to_bot = message['reply_to_message'].get('from', {}).get('username') == 'group_code_bot'
        if not replied_to_bot:
            message['text'] = add_chat_id_if_reply(message)
    
    # Store message in chat history
    chat_id = message['chat']['id']
    store_message(chat_id, message)
        
    text = message['text']
    
    # Handle commands first
    if text.startswith('/'):
        # Extract the command by removing the @ portion if present
        command = text.split('@')[0]  # This will convert "/help@group_code_bot" to "help"
        await handle_command(message, command)
        return
    
    # Handle replies to provider messages
    if 'reply_to_message' in message:
        if await handle_provider_reply(message, message['reply_to_message']):
            return
            
    # Handle provider mentions
    if await handle_provider_mention(message):
        return

    # Handle non-command messages
    if '@group_code_bot' in text.lower():
        await handle_code_request(message)
        return
    elif re.search(GITHUB_ISSUE_PATTERN, text):
        await handle_github_issue_link(message)
        return
    

def parse_bot_mention(text: str) -> Optional[str]:
    """Extract command text from bot mention"""
    match = re.search(BOT_MENTION_PATTERN, text)
    return match.group(1) if match else None


async def handle_command(message: Dict[str, Any], command: str) -> bool:
    """Handle bot commands"""
    chat_id = message['chat']['id']
    
    if command.startswith('/help'):
        try:
            # Try to send plain message without formatting
            plain_help = HELP_MESSAGE.replace('*', '').replace('`', '')
            send_message(chat_id, plain_help)
        except Exception as e:
            logger.error(f"Failed to send help message to chat {chat_id}: {e}")
            # Fallback to much simpler help message
            simple_help = "Available commands:\n/help - Show this message\n/clear - Clear chat history\n/submit_reward - Submit reward for completed task"
            send_message(chat_id, simple_help)
        return True
        
    if command.startswith('/submit_reward'):
        await handle_submit_reward(message)
        return True
        
    if command.startswith('/clear'):
        await clear_chat_history(chat_id)
        try:
            # Try with the template from success messages
            send_message(chat_id, SUCCESS_MESSAGES["history_cleared"].template)
        except Exception as e:
            logger.error(f"Failed to send clear history confirmation message: {e}")
            # Fallback to simpler message
            send_message(chat_id, "✅ Chat history cleared successfully!")
        return True
        
    return False

async def handle_submit_reward(message: Dict[str, Any]) -> None:
    """Handle the submit_reward command"""
    chat_id = message['chat']['id']
    parts = message['text'].split()
    
    if len(parts) != 3:
        send_message(chat_id, INVALID_REWARD_FORMAT)
        return
        
    instance_id = parts[1]
    try:
        amount = float(parts[2].replace(',', '.'))
        async with AgentMarketClient() as client:
            await client.report_reward(instance_id, amount)
        
        try:
            # Try to send formatted success message
            send_message(chat_id, REWARD_SUCCESS.format(amount=amount, instance_id=instance_id))
        except Exception as e:
            logger.error(f"Failed to send reward success message: {e}")
            # Fallback to simpler message
            send_message(chat_id, f"✅ Successfully submitted reward of {amount} for instance {instance_id}")
    except ValueError:
        send_message(chat_id, "❌ Amount must be a valid number")
    except Exception as e:
        import traceback
        error_details = f"Error submitting reward: {e}\n"
        error_details += f"Traceback: {traceback.format_exc()}\n"
        
        # Get additional details if it's an HTTP error
        if hasattr(e, 'response') and e.response is not None:
            response = e.response
            # Check if response is an object or dict and extract status code
            if isinstance(response, dict) and 'status_code' in response:
                error_details += f"Status Code: {response['status_code']}\n"
            elif hasattr(response, 'status_code'):
                error_details += f"Status Code: {response.status_code}\n"
            
            # Check for text content
            if isinstance(response, dict) and 'text' in response:
                error_details += f"Response Content: {response['text']}\n"
            elif hasattr(response, 'text'):
                error_details += f"Response Content: {response.text}\n"
            
            # Add URL, method, headers, and body if available
            if isinstance(response, dict) and 'url' in response:
                error_details += f"Request URL: {response['url']}\n"
            elif hasattr(response, 'url'):
                error_details += f"Request URL: {response.url}\n"
                
            if hasattr(e.response, 'request') and e.response.request is not None:
                if hasattr(e.response.request, 'method'):
                    error_details += f"Request Method: {e.response.request.method}\n"
                if hasattr(e.response.request, 'headers'):
                    error_details += f"Request Headers: {e.response.request.headers}\n"
                if hasattr(e.response.request, 'body'):
                    error_details += f"Request Body: {e.response.request.body}\n"
        
        logger.error(error_details)
        send_message(chat_id, f"❌ Failed to submit reward: {str(e)}")

async def initialize_bot() -> None:
    """Initialize bot settings and configurations"""
    logger.info("Initializing bot...")
    
    # Set up default commands for the bot
    token = os.environ.get('GROUPWRITE_TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("Bot token not found in environment variables")
        return
        
    # Set global bot commands
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    commands = [
        {
            "command": "help",
            "description": "Show help message"
        },
        {
            "command": "submit_reward",
            "description": "Submit reward for an instance"
        },
        {
            "command": "clear",
            "description": "Clear chat history"
        }
    ]
    
    try:
        response = requests.post(commands_url, json={"commands": commands})
        response.raise_for_status()
        logger.info("Successfully set global bot commands")
    except Exception as e:
        import traceback
        error_details = f"Failed to set bot commands: {e}\n"
        error_details += f"Traceback: {traceback.format_exc()}\n"
        
        # Get additional details if it's an HTTP error
        if hasattr(e, 'response') and e.response is not None:
            response = e.response
            # Check if response is an object or dict and extract status code
            if isinstance(response, dict) and 'status_code' in response:
                error_details += f"Status Code: {response['status_code']}\n"
            elif hasattr(response, 'status_code'):
                error_details += f"Status Code: {response.status_code}\n"
            
            # Check for text content
            if isinstance(response, dict) and 'text' in response:
                error_details += f"Response Content: {response['text']}\n"
            elif hasattr(response, 'text'):
                error_details += f"Response Content: {response.text}\n"
            
            # Add URL, method, headers, and body if available
            if isinstance(response, dict) and 'url' in response:
                error_details += f"Request URL: {response['url']}\n"
            elif hasattr(response, 'url'):
                error_details += f"Request URL: {response.url}\n"
                
            if hasattr(e.response, 'request') and e.response.request is not None:
                if hasattr(e.response.request, 'method'):
                    error_details += f"Request Method: {e.response.request.method}\n"
                if hasattr(e.response.request, 'headers'):
                    error_details += f"Request Headers: {e.response.request.headers}\n"
                if hasattr(e.response.request, 'body'):
                    error_details += f"Request Body: {e.response.request.body}\n"
        
        logger.error(error_details)

def set_bot_commands(chat_id: int) -> None:
    """Set up the bot's commands for a group chat with proper scope and language support."""
    
    commands = [
        {
            "command": "help",
            "description": "Show help message"
        },
        {
            "command": "submit_reward",
            "description": "Submit reward for an instance"
        },
        {
            "command": "clear",
            "description": "Clear chat history"
        }
    ]
    
    token = os.environ['GROUPWRITE_TELEGRAM_BOT_TOKEN']
    
    # Set commands with proper scope for the specific group chat
    commands_url = f"https://api.telegram.org/bot{token}/setMyCommands"
    # Commands by chat_id
    commands_payload = {
        "commands": commands,
        "chat_id": chat_id
    }
    
    try:
        commands_response = requests.post(commands_url, json=commands_payload)
        commands_response.raise_for_status()  # Raise exception for non-200 status codes
        logger.info(f"Successfully set commands for chat {chat_id}")
    except Exception as e:
        import traceback
        error_details = f"Error setting commands for chat {chat_id}: {e}\n"
        error_details += f"Traceback: {traceback.format_exc()}\n"
        
        # Get additional details if it's an HTTP error
        if hasattr(e, 'response') and e.response is not None:
            response = e.response
            # Check if response is an object or dict and extract status code
            if isinstance(response, dict) and 'status_code' in response:
                error_details += f"Status Code: {response['status_code']}\n"
            elif hasattr(response, 'status_code'):
                error_details += f"Status Code: {response.status_code}\n"
            
            # Check for text content
            if isinstance(response, dict) and 'text' in response:
                error_details += f"Response Content: {response['text']}\n"
            elif hasattr(response, 'text'):
                error_details += f"Response Content: {response.text}\n"
            
            # Add URL, method, headers, and body if available
            if isinstance(response, dict) and 'url' in response:
                error_details += f"Request URL: {response['url']}\n"
            elif hasattr(response, 'url'):
                error_details += f"Request URL: {response.url}\n"
                
            if hasattr(e.response, 'request') and e.response.request is not None:
                if hasattr(e.response.request, 'method'):
                    error_details += f"Request Method: {e.response.request.method}\n"
                if hasattr(e.response.request, 'headers'):
                    error_details += f"Request Headers: {e.response.request.headers}\n"
                if hasattr(e.response.request, 'body'):
                    error_details += f"Request Body: {e.response.request.body}\n"
        
        logger.error(error_details)
