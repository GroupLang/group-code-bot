"""Models for the GroupCode bot application.

This module contains Pydantic models for validating and serializing data structures
used throughout the application for instance tracking and provider messages.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, HttpUrl

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
