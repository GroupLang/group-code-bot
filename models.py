"""Models for the GroupCode bot application.

This module contains Pydantic models for validating and serializing data structures
used throughout the application, particularly for Telegram API interactions and
instance tracking.
"""

from typing import Optional, Dict, Any, TypedDict, List, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, HttpUrl

# Type aliases for Telegram types
TelegramUpdate = Dict[str, Any]  # Base type for Telegram updates
TelegramMessage = Dict[str, Any]  # Type for message objects
TelegramUser = Dict[str, Any]    # Type for user objects
TelegramChat = Dict[str, Any]    # Type for chat objects

class RequestMetadata(BaseModel):
    """Metadata associated with an instance request."""
    
    github_issue_url: Optional[HttpUrl] = Field(
        None, 
        description="URL of associated GitHub issue"
    )
    provider_ids: List[str] = Field(
        default_factory=list,
        description="List of provider IDs involved"
    )
    labels: List[str] = Field(
        default_factory=list,
        description="Custom labels for the request"
    )

class TelegramUserModel(BaseModel):
    """Model representing a Telegram user."""
    
    id: int = Field(..., description="Telegram user ID")
    is_bot: bool = Field(default=False, description="Whether the user is a bot")
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    username: Optional[str] = Field(None, description="User's username")
    language_code: Optional[str] = Field(None, description="User's language code")

class TelegramChatModel(BaseModel):
    """Model representing a Telegram chat."""
    
    id: int = Field(..., description="Telegram chat ID")
    type: str = Field(..., description="Type of chat (private, group, etc)")
    title: Optional[str] = Field(None, description="Chat title for groups")
    username: Optional[str] = Field(None, description="Username for private chats")

class TelegramMessageModel(BaseModel):
    """Model representing a Telegram message."""
    
    message_id: int = Field(..., description="Unique message identifier")
    from_user: TelegramUserModel = Field(..., alias="from")
    chat: TelegramChatModel
    date: datetime
    text: Optional[str] = Field(None, description="Message text if any")
    reply_to_message: Optional['TelegramMessageModel'] = None

class TelegramUpdateModel(BaseModel):
    """Model representing a Telegram update."""
    
    update_id: int = Field(..., description="Update's unique identifier")
    message: Optional[TelegramMessageModel] = Field(None, description="New message")

class InstanceRequest(BaseModel):
    """Model representing an instance request."""
    
    instance_id: UUID = Field(
        ..., 
        description="Unique identifier for the instance"
    )
    chat_id: int = Field(
        ..., 
        description="Telegram chat ID where request originated"
    )
    status: str = Field(
        ...,
        description="Current status of the request",
        pattern="^(pending|active|completed|failed)$"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when request was created"
    )
    metadata: Optional[RequestMetadata] = Field(
        None,
        description="Additional metadata for the request"
    )

    @validator('created_at')
    def ensure_utc(cls, v):
        """Ensure timestamp is in UTC."""
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v

class ProviderMessage(BaseModel):
    """Model representing a message from a provider."""
    
    provider_id: UUID = Field(
        ...,
        description="Unique identifier of the provider"
    )
    instance_id: UUID = Field(
        ...,
        description="ID of the instance this message belongs to"
    )
    content: str = Field(
        ...,
        description="Message content",
        min_length=1,
        max_length=4096
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the message was sent"
    )

    @validator('timestamp')
    def ensure_utc(cls, v):
        """Ensure timestamp is in UTC."""
        if v.tzinfo is not None:
            v = v.replace(tzinfo=None)
        return v

TelegramMessageModel.update_forward_refs()
