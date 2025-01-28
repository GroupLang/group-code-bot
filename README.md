# Group Code Bot

A Telegram bot that helps manage code requests and GitHub issues in group chats. The bot facilitates communication between users and code providers, tracks GitHub issues, and manages reward distributions for completed tasks.

## Key Features

- Create and manage code requests
- Track GitHub issues and pull requests
- Direct communication with code providers
- Solution review and approval system 
- Reward distribution for completed tasks
- Automated status updates

## Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/help` | `/help` | Show help message with all available commands |
| `/submit_reward` | `/submit_reward <instance_id> <amount>` | Submit reward for completed task |
| `/start` | `/start` | Start the bot and see welcome message |

## Usage Guide

### Creating Code Requests

There are two ways to create a code request:

1. **Direct Request**
    - Mention the bot with your request
    - Format: `@group_code_bot code <your request>`

2. **GitHub Issue**
    - Share a GitHub issue link in the chat
    - The bot will automatically track the issue

### Chatting with Providers

Provider IDs have the format: `abc123-def456`

There are two ways to communicate with providers:

1. **Direct Reply**
    - Simply reply to any provider message in the chat

2. **Mention Format**
    - Format: `@provider_id <instance_id> your message`
    - Example: `@abc123-def456 instance_789 Can you explain this part?`

### Reward Submission

To submit a reward for completed work:

```bash
/submit_reward <instance_id> <amount>
```

Example:
```bash
/submit_reward abc123 1.5
```

### Provider Messages

When providers respond, you'll receive messages in this format:

- Provider ID
- Instance ID
- Timestamp
- Message content

## Best Practices

1. Clear Communication
    - Be specific in code requests
    - Include relevant context
    - Use code blocks for code snippets

2. Issue Tracking
    - Link GitHub issues when available
    - Monitor issue updates through the bot

3. Provider Interaction
    - Respond promptly to provider questions
    - Use the correct provider ID and instance ID
    - Review solutions thoroughly before approval

## Getting Started

1. Add the bot to your Telegram group
2. Start with `/help` to see available commands
3. Create your first request or share a GitHub issue
4. Monitor responses and updates in the group chat

## Support

Need help? Use the `/help` command in the chat for quick reference to all features and commands.
