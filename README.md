# group-write-bot

group-write-bot is a Telegram bot that helps groups collaboratively create and maintain consensus documents. It collects messages from group discussions and uses AI to generate and update a living document that reflects the group's consensus.

## Features

- Collects text messages from Telegram groups
- Automatically generates consensus documents from group discussions
- Allows group members to approve or reject document updates
- Rewards contributors when their updates are approved
- Supports message reactions for feedback
- Integrates with MarketRouter AI for intelligent document generation

## Prerequisites

- Poetry for dependency management
- Telegram Bot Token
- MarketRouter API Key
- A Telegram group for discussions
- A Telegram channel for document updates

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/group-write-bot.git
   cd group-write-bot
   ```

2. Install Poetry if you haven't already:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies using Poetry:
   ```
   poetry install
   ```

## Configuration

Set up the following environment variables:

- `GROUPWRITE_TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
- `MARKETROUTER_API_KEY`: Your MarketRouter API Key

## Usage

1. Start the bot:
   ```
   poetry run uvicorn main:app --reload
   ```

2. Set up your Telegram environment:
   - Add the bot to your group
   - Create a channel for document updates
   - Make the bot an admin in both the group and channel

3. How it works:
   - Members send messages in the group
   - The bot collects messages and periodically generates document updates
   - Updates are posted to the document channel
   - Group members can approve or reject updates using inline buttons
   - Approved updates become the new current document
   - Contributors receive rewards for approved updates

## Document Generation Process

1. Message Collection
   - The bot collects text messages from the group
   - After collecting 5 messages, it triggers a document update

2. Update Generation
   - The bot uses MarketRouter AI to generate an updated document
   - The update considers both the current document and new messages
   - The goal is to maintain consensus while incorporating new information

3. Approval Process
   - Generated updates are posted to the document channel
   - Members can vote using 👍 (approve) or 👎 (reject) buttons
   - Approved updates replace the current document
   - Contributors receive rewards for approved updates

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.