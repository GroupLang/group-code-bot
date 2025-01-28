from typing import Optional, Tuple
import uuid
from loguru import logger
from services.client import AgentMarketClient
from utils.telegram_utils import send_message

async def send_message_to_provider(
    chat_id: int,
    provider_id: str,
    content: str,
    instance_id: Optional[str] = None
) -> None:
    """Send a message to a provider via AgentMarket.
    
    Args:
        chat_id: Telegram chat ID where message originated
        provider_id: Provider's unique identifier
        content: Message content to send
        instance_id: Optional instance context for the message
    
    Raises:
        ValueError: If instance_id is missing
    """
    if not instance_id:
        raise ValueError("Instance ID is required to send a message to a provider")
        
    async with AgentMarketClient() as client:
        try:
            await client.send_message_in_conversation(
                instance_id=instance_id,
                message=content,
                provider_id=provider_id
            )
            send_message(chat_id, f"✅ Message sent to provider `@{provider_id}`.")
        except Exception as e:
            logger.error(f"Error sending message to provider: {e}")
            send_message(chat_id, "❌ Failed to send message to provider.")

def parse_provider_mention(text: str) -> Optional[Tuple[str, str, str]]:
    """Parse a provider mention from message text.
    
    Format: @provider_id [instance_id] message
    
    Returns:
        Tuple of (provider_id, message_content, instance_id) or None if invalid
    """
    if not text.startswith('@'):
        return None
        
    parts = text.split(maxsplit=2)
    if len(parts) < 2:
        return None
        
    provider_id = parts[0][1:]  # Remove @ symbol
    
    # Check if second part is instance_id
    if len(parts) == 3:
        instance_id = parts[1]
        message_content = parts[2]
    else:
        instance_id = None 
        message_content = parts[1]
    
    # Validate provider_id is UUID
    try:
        uuid.UUID(provider_id)
    except ValueError:
        return None
    
    return provider_id, message_content, instance_id
