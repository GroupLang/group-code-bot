"""Message type definitions and validation."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class User(BaseModel):
    """Telegram user model."""
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

class Chat(BaseModel):
    """Telegram chat model."""
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None

class BaseMessage(BaseModel):
    """Base message model."""
    message_id: int
    from_user: Optional[User] = Field(None, alias='from')
    chat: Chat
    date: datetime
    text: Optional[str] = None
    reply_to_message: Optional['BaseMessage'] = None

class CommandMessage(BaseMessage):
    """Command message model."""
    command: str = Field(..., regex=r'^/[a-zA-Z0-9_]+$')
    args: str = ''

class CodeRequest(BaseMessage):
    """Code request message model."""
    request_text: str = Field(..., min_length=1)

class ProviderMessage(BaseMessage):
    """Provider message model."""
    provider_id: str
    instance_id: str
    content: str

class GitHubIssue(BaseMessage):
    """GitHub issue message model."""
    owner: str
    repo: str
    issue_number: int
    url: str

BaseMessage.update_forward_refs()
