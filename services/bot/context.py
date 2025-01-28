"""Message context tracking and management."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class MessageContext:
    """Tracks context for message processing."""
    
    chat_id: int
    message_id: int
    user_id: Optional[int] = None
    instance_id: Optional[str] = None
    provider_id: Optional[str] = None
    command: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to context.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Value associated with key or default
        """
        return self.metadata.get(key, default)
