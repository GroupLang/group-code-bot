"""Message templates and constants used throughout the bot.

This module centralizes all user-facing message strings used in the application.
Messages are organized by categories and use consistent formatting with Pydantic validation.
"""

from enum import Enum
from typing import Dict, Optional, List, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo

class MessageCategory(Enum):
    """Categories for different types of messages."""
    WELCOME = "welcome"
    HELP = "help" 
    ERROR = "error"
    SUCCESS = "success"
    PROVIDER = "provider"
    COMMAND = "command"
    GITHUB = "github"

class MessageTemplate(BaseModel):
    """Base model for message templates with placeholder validation."""
    template: str
    category: MessageCategory
    placeholders: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('template')
    def validate_placeholders(cls, v: str, info: ValidationInfo) -> str:
        """Validate that declared placeholders exist in template."""
        import re
        # Get placeholders from model fields
        placeholders = info.data.get('placeholders', [])
        if not placeholders:  # No validation needed if no placeholders declared
            return v
            
        # Only validate that declared placeholders exist in template
        found = set(re.findall(r'\{([^}]+)\}', v))
        missing = set(placeholders) - found
        if missing:
            raise ValueError(f"Template missing declared placeholders: {missing}")
        return v

class CommandUsage(BaseModel):
    """Command usage template with validation."""
    command: str = Field(..., pattern=r'^/')
    usage: str
    description: Optional[str]

class Emoji:
    """Emoji constants for consistent message formatting."""
    SUCCESS = "✅"
    ERROR = "❌"
    INFO = "ℹ️"
    WARNING = "⚠️"
    MESSAGE = "📩"
    CLOCK = "⏰"
    ROCKET = "🚀"
    WAVE = "👋"
    WRENCH = "🔧"
    MEMO = "📝"
    CHAT = "💬"
    SEARCH = "🔍"
    GITHUB = "📦"
    CODE = "💻"
    LINK = "🔗"

# Command related message templates
COMMAND_MESSAGES: Dict[str, MessageTemplate] = {
    "parse_error": MessageTemplate(
        template=f"{Emoji.ERROR} Failed to parse command: {{error}}",
        category=MessageCategory.ERROR,
        placeholders=["error"]
    ),
    "reward_parse_error": MessageTemplate(
        template=(
            f"{Emoji.ERROR} Invalid reward format\n"
            "Expected format: /submit_reward <instance_id> <amount>\n"
            "Example: /submit_reward abc123 1.5"
        ),
        category=MessageCategory.ERROR,
        placeholders=[]  # No placeholders in this template
    ),
    "reward_amount_error": MessageTemplate(
        template=f"{Emoji.ERROR} Invalid reward amount: {{amount}}. Must be a positive number.",
        category=MessageCategory.ERROR,
        placeholders=["amount"]
    )
}

# Command usage templates with validation
COMMAND_USAGE = {
    "balance": CommandUsage(
        command="/balance",
        usage="/balance",
        description="Check your wallet balance"
    ),
    "submit_reward": CommandUsage(
        command="/submit_reward",
        usage="/submit_reward <instance_id> <amount>",
        description="Submit reward for completed task"
    ),
    "help": CommandUsage(
        command="/help",
        usage="/help",
        description="Show help message"
    ),
    "clear": CommandUsage(
        command="/clear", 
        usage="/clear",
        description="Clear chat history"
    ),
    "start": CommandUsage(
        command="/start",
        usage="/start",
        description="Start the bot"
    )
}

# Welcome message with consistent formatting
WELCOME_MESSAGE = f"""
{Emoji.WAVE} *Welcome to Group Code Bot!*

I help manage code requests and GitHub issues in this group.

{Emoji.WRENCH} *Key Features*:
• Create code requests by mentioning me with your request
• Share GitHub issues for automated tracking
• Chat directly with providers using their ID
• Review and approve solutions with reactions
• Submit rewards for completed tasks

{Emoji.MEMO} *Quick Commands*:
• `{COMMAND_USAGE['help']}` - View all commands
• `{COMMAND_USAGE['clear']}` - Clear chat history
• `{COMMAND_USAGE['submit_reward']}` - Submit rewards

{Emoji.ROCKET} *Get Started*:
1. Share a GitHub issue or
2. Mention me with `@group_code_bot code <your request>`

{Emoji.CHAT} *Chat with Providers*:
Two ways to reply:
1. Direct reply to provider message
2. Using format: `@provider_id <instance_id> your message`
Example: `@abc123-def456 instance_789 Can you explain this part?`

Need help? Type `{COMMAND_USAGE['help']}` anytime!
"""

# Help message with consistent formatting
HELP_MESSAGE = f"""
{Emoji.INFO} *Group Code Bot Help*

{Emoji.MEMO} *Commands:*
• `{COMMAND_USAGE['clear']}` - Clear chat history and unresolved requests
• `{COMMAND_USAGE['help']}` - Show this help message
• `{COMMAND_USAGE['submit_reward']}` - Submit reward for an instance

{Emoji.CODE} *Usage:*
• Mention @group_code_bot with your code request
• Share a GitHub issue link to start a discussion
• Chat with providers using @provider_id your message

{Emoji.CHAT} *Provider Chat:*
• Provider IDs look like: abc123-def456
• Two ways to reply to providers:
  1. Simply reply to their message
  2. Use format: @provider_id <instance_id> your message
• You'll receive their replies in the group chat

{Emoji.GITHUB} *GitHub Integration:*
• Share issue links to track progress
• Automatically notifies on updates
• Links PRs to original requests
"""

# Error messages with validation
ERROR_MESSAGES: Dict[str, MessageTemplate] = {
    # Command errors
    "invalid_command": MessageTemplate(
        template=f"{Emoji.ERROR} Unknown command: {{command}}",
        category=MessageCategory.ERROR,
        placeholders=["command"]
    ),
    "missing_command_args": MessageTemplate(
        template=f"{Emoji.ERROR} Missing required command arguments",
        category=MessageCategory.ERROR,
        placeholders=[]
    ),
    "missing_code_request": MessageTemplate(
        template=f"{Emoji.ERROR} Please provide a code request description after the command.",
        category=MessageCategory.ERROR,
        placeholders=[]
    ),
    
    # Reward submission errors
    "invalid_reward_format": (
        f"{Emoji.ERROR} Invalid format. Use:\n"
        f"`{COMMAND_USAGE['submit_reward']}`\n"
        "Example: `/submit_reward abc123 1.5`"
    ),
    "invalid_reward_amount": f"{Emoji.ERROR} Amount must be a valid number",
    "reward_submission_failed": f"{Emoji.ERROR} Failed to submit reward: {{}}",
    
    # Provider communication errors
    "invalid_provider_format": MessageTemplate(
        template=f"{Emoji.ERROR} Invalid provider message format",
        category=MessageCategory.ERROR,
        placeholders=[]
    ),
    "provider_not_found": MessageTemplate(
        template=f"{Emoji.ERROR} Provider {{provider_id}} not found",
        category=MessageCategory.ERROR,
        placeholders=["provider_id"]
    ),
    "message_send_failed": MessageTemplate(
        template=f"{Emoji.ERROR} Failed to send message: {{error}}",
        category=MessageCategory.ERROR,
        placeholders=["error"]
    ),
    
    # GitHub errors
    "invalid_issue_link": MessageTemplate(
        template=f"{Emoji.ERROR} Invalid GitHub issue link format",
        category=MessageCategory.ERROR,
        placeholders=[]
    ),
    "issue_not_found": MessageTemplate(
        template=f"{Emoji.ERROR} GitHub issue not found: {{issue}}",
        category=MessageCategory.ERROR,
        placeholders=["issue"]
    ),
    "repo_access_error": MessageTemplate(
        template=f"{Emoji.ERROR} Cannot access repository: {{repo}}",
        category=MessageCategory.ERROR,
        placeholders=["repo"]
    )
}

# Success messages with validation
SUCCESS_MESSAGES: Dict[str, MessageTemplate] = {
    # Wallet related
    "wallet_balance": MessageTemplate(
        template=(
            f"{Emoji.INFO} *Wallet Balance*\n"
            "Balance: {{balance}} credits\n"
            "Status: {{status}}"
        ),
        category=MessageCategory.SUCCESS,
        placeholders=["balance", "status"]
    ),
    
    # Instance related
    "instance_created": MessageTemplate(
        template=(
            f"{Emoji.SUCCESS} Instance created!\n\n"
            f"{Emoji.SEARCH} Instance ID: `{{instance_id}}`\n"
        ),
        category=MessageCategory.SUCCESS,
        placeholders=["instance_id"]
    ),
    "instance_updated": f"{Emoji.SUCCESS} Instance {{}} has been updated",
    
    # Reward related
    "reward_submitted": f"{Emoji.SUCCESS} Successfully submitted reward of {{}} for instance {{}}",
    
    # Provider communication
    "message_sent": f"{Emoji.SUCCESS} Message sent to provider {{}}",
    "provider_added": f"{Emoji.SUCCESS} Provider {{}} has been added to instance {{}}",
    
    # GitHub related
    "issue_tracked": f"{Emoji.SUCCESS} Now tracking GitHub issue: {{}}",
    "pr_linked": f"{Emoji.SUCCESS} Pull request linked to instance {{}}"
}

# Provider message templates with validation
PROVIDER_MESSAGES: Dict[str, MessageTemplate] = {
    "new_message": MessageTemplate(
        template=(
            f"{Emoji.MESSAGE} Message from provider:\n"
            "({{provider_id}})\n"
            "for instance: {{instance_id}}\n"
            f"{Emoji.CLOCK} {{timestamp}}\n\n"
            "{{content}}"
        ),
        category=MessageCategory.PROVIDER,
        placeholders=["provider_id", "instance_id", "timestamp", "content"]
    ),
    "status_update": f"{Emoji.INFO} Provider {{provider_id}} updated status: {{status}}",
    "solution_submitted": (
        f"{Emoji.SUCCESS} Provider {{provider_id}} submitted a solution:\n"
        f"{Emoji.LINK} {{solution_link}}"
    )
}

# GitHub related messages with validation
GITHUB_MESSAGES: Dict[str, MessageTemplate] = {
    "issue_update": MessageTemplate(
        template=(
            f"{Emoji.GITHUB} GitHub Issue Update\n"
            "Repository: {{repo}}\n"
            "Issue #{{number}}: {{title}}\n"
            "Status: {{status}}\n"
            f"{Emoji.LINK} {{url}}"
        ),
        category=MessageCategory.GITHUB,
        placeholders=["repo", "number", "title", "status", "url"]
    ),
    "pr_update": (
        f"{Emoji.GITHUB} Pull Request Update\n"
        "PR #{{number}}: {{title}}\n"
        "Status: {{status}}\n"
        f"{Emoji.LINK} {{url}}"
    )
}
"""Message constants for the bot."""

WELCOME_MESSAGE = (
    "👋 *Welcome to Group Code Bot!*\n\n"
    "I help manage code requests and GitHub issues in this group.\n\n"
    "🔧 *Key Features*:\n"
    "• Create code requests by mentioning me with your request\n"
    "• Share GitHub issues for automated tracking\n"
    "• Chat directly with providers using their ID\n"
    "• Review and approve solutions with reactions\n"
    "• Submit rewards for completed tasks\n\n"
    "📝 *Quick Commands*:\n"
    "• `/help` - View all commands\n"
    "• `/clear` - Clear chat history\n"
    "• `/submit_reward <instance_id> <amount>` - Submit rewards \n\n"
    "🚀 *Get Started*:\n"
    "1. Share a GitHub issue or\n"
    "2. Mention me with `@group_code_bot code <your request>`\n"
    "⚠️ *Note*: For private repositories, you must grant read access to **agentmarketbot**\n\n"
    "💬 *Chat with Providers*:\n"
    "Two ways to reply:\n"
    "1. Direct reply to provider message\n"
    "2. Using format: `@provider_id <instance_id> your message`\n"
    "Example: `@abc123-def456 instance_789 Can you explain this part?`\n\n"
    "Need help? Type `/help` anytime!"
)

HELP_MESSAGE = (
    "*Group Code Bot Help*\n\n"
    "*Commands:*\n"
    "• /balance - Check your wallet balance\n"
    "• /clear - Clear chat history and unresolved requests\n"
    "• /help - Show this help message\n"
    "• /submit\\_reward <instance\\_id> <amount> - Submit reward for an instance\n\n"
    "*Usage:*\n"
    "• Mention @group\\_code\\_bot with your code request\n"
    "• Share a GitHub issue link to start a discussion\n"
    "• Chat with providers using @provider\\_id your message\n"
    "• For private repositories, grant read access to **agentmarketbot**\n\n"
    "*Provider Chat:*\n"
    "• Provider IDs look like: abc123\\-def456\n"
    "• Two ways to reply to providers:\n"
    "  1. Simply reply to their message\n"
    "  2. Use format: @provider\\_id <instance\\_id> your message\n"
    "• You'll receive their replies in the group chat"
)

INVALID_REWARD_FORMAT = (
    "❌ Invalid format. Use:\n"
    "`/submit_reward <instance_id> <amount>`\n"
    "Example: `/submit_reward abc123 1.5`"
)

REWARD_SUCCESS = "✅ Successfully submitted reward of {amount} for instance {instance_id}"