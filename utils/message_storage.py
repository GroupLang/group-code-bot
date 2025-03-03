"""Utility functions for message storage and retrieval."""

import os
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
import boto3

class Config:
    """DynamoDB configuration"""
    _dynamodb = boto3.resource('dynamodb')
    _table = _dynamodb.Table(os.environ.get('DYNAMODB_TABLE_NAME', 'agent_requests'))

async def get_chat_history(chat_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch recent messages from chat history stored in DynamoDB"""
    try:
        # Ensure chat_id is properly formatted
        if not isinstance(chat_id, (int, str)):
            raise ValueError("chat_id must be an integer or string")
        
        # Format chat_id as string, ensuring it's not empty
        chat_id_str = str(chat_id).strip()
        if not chat_id_str:
            raise ValueError("chat_id cannot be empty")
            
        # Get messages from DynamoDB
        response = Config._table.get_item(
            Key={'chat_id': chat_id_str}
        )
        
        # Get messages array from item, default to empty list if not found
        item = response.get('Item', {})
        messages = item.get('messages', [])
        
        # Return most recent messages up to limit
        return messages[-limit:]
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return []

def store_message(chat_id: int, message: Dict[str, Any]) -> None:
    """Store a new message in the chat history"""
    try:
        # Ensure chat_id is properly formatted
        if not isinstance(chat_id, (int, str)):
            raise ValueError("chat_id must be an integer or string")
        
        # Format chat_id as string, ensuring it's not empty
        chat_id_str = str(chat_id).strip()
        if not chat_id_str:
            raise ValueError("chat_id cannot be empty")
            
        # Extract username from message
        username = message.get('from', {}).get('username', 'unknown')
        if username == "unknown" or username == "":
            username = message.get('from', {}).get('first_name', '')
        
        # Create message object with username
        # Check if message is from group_code_bot
        is_bot_message = message.get('from', {}).get('username') == 'group_code_bot'
        
        message_with_user = {
            'text': message.get('text', ''),
            'username': username,
            'timestamp': message.get('date', datetime.utcnow().timestamp()),
            'message_id': message.get('message_id', ''),
            'is_bot_message': is_bot_message
        }
        
        # Get existing messages
        response = Config._table.get_item(
            Key={'chat_id': chat_id_str}
        )
        
        # Initialize messages list, either from existing item or as empty list
        item = response.get('Item')
        
        if item is None:
            # Create new item if it doesn't exist
            Config._table.put_item(
                Item={
                    'chat_id': chat_id_str,
                    'messages': [message_with_user],
                    'reactions': {}
                }
            )
        else:
            # Add new message to existing item
            messages = item.get('messages', [])
            messages.append(message_with_user)
            messages = messages[-100:]  # Keep only last 100 messages
            
            Config._table.update_item(
                Key={'chat_id': chat_id_str},
                UpdateExpression='SET messages = :messages',
                ExpressionAttributeValues={':messages': messages}
            )
    except Exception as e:
        logger.error(f"Error storing message: {e}")
        raise e

def add_chat_id_if_reply(message: Dict[str, Any]) -> str:
    """Add reference to replied message in text"""
    text = message["text"]
    text = f"(Reply to message_id: {message['reply_to_message']['message_id']}) {text}"
    return text

def get_from_reaction_to_message(message_reaction: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a reaction update to a message format"""
    emoji = message_reaction['new_reaction'][0]['emoji']
    message_id = message_reaction['message_id']
    
    # Common message structure for both positive and negative reactions
    reaction_message = {
        'message_id': message_id,
        'from': {
            'id': message_reaction['user']['id'],
            'is_bot': message_reaction['user'].get('is_bot', False),
            'first_name': message_reaction['user'].get('first_name', ''),
            'username': message_reaction['user'].get('username', '')
        },
        'chat': {
            'id': message_reaction['chat']['id'],
            'type': message_reaction['chat'].get('type', 'unknown')
        },
        'date': message_reaction['date'],
        'text': f"{emoji} to message_id: {message_id}"
    }
    return reaction_message

async def clear_chat_history(chat_id: int) -> None:
    """Clear all messages for a specific chat_id from DynamoDB"""
    try:
        # Ensure chat_id is properly formatted
        if not isinstance(chat_id, (int, str)):
            raise ValueError("chat_id must be an integer or string")
        
        # Format chat_id as string, ensuring it's not empty
        chat_id_str = str(chat_id).strip()
        if not chat_id_str:
            raise ValueError("chat_id cannot be empty")
            
        # Update the item to have an empty messages array
        Config._table.update_item(
            Key={'chat_id': chat_id_str},
            UpdateExpression='SET messages = :empty_list',
            ExpressionAttributeValues={':empty_list': []}
        )
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise e
