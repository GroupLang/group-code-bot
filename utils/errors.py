"""Error handling framework for the GroupCode bot application.

This module provides a comprehensive error handling framework including:
- Custom exception hierarchy
- Error context tracking
- Logging configuration
- Error handling utilities
"""

import sys
import traceback
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Type, Callable, TypeVar
from functools import wraps
from contextlib import contextmanager
from pathlib import Path
from loguru import logger

# Type variables for generics
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class BaseError(Exception):
    """Base exception class for all application errors."""
    def __init__(self, message: str, **kwargs):
        self.message = message
        self.context = ErrorContext(
            error_type=self.__class__.__name__,
            message=message,
            **kwargs
        )
        super().__init__(message)

class ConfigurationError(BaseError):
    """Raised when there's an error in configuration settings."""
    pass

class TelegramError(BaseError):
    """Raised when there's an error in Telegram API interactions."""
    pass

class GitHubError(BaseError):
    """Raised when there's an error in GitHub API interactions."""
    pass

class DatabaseError(BaseError):
    """Raised when there's an error in database operations."""
    pass

class ValidationError(BaseError):
    """Raised when there's an error in data validation."""
    pass

class ErrorContext:
    """Captures and stores context information about an error."""
    
    def __init__(
        self,
        error_type: str,
        message: str,
        **kwargs: Any
    ):
        self.error_type = error_type
        self.message = message
        self.timestamp = datetime.utcnow()
        self.stack_trace = traceback.format_exc()
        self.additional_context = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary format."""
        return {
            'error_type': self.error_type,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'stack_trace': self.stack_trace,
            **self.additional_context
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True
) -> None:
    """Configure application-wide logging settings.
    
    Args:
        log_level: Minimum log level to capture
        log_file: Optional file path for log output
        json_format: Whether to use JSON formatting
    """
    # Remove existing handlers
    logger.remove()
    
    # Configure format
    log_format = {
        "time": "{time:YYYY-MM-DD HH:mm:ss.SSS}",
        "level": "{level}",
        "message": "{message}",
        "extra": "{extra}"
    }
    
    if json_format:
        format_func = lambda record: json.dumps({
            **log_format,
            "exception": record["exception"]
        })
    else:
        format_func = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}"

    # Add console handler
    logger.add(
        sys.stderr,
        format=format_func,
        level=log_level,
        serialize=json_format
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            format=format_func,
            level=log_level,
            serialize=json_format,
            rotation="500 MB"
        )

def handle_error(
    error_type: Type[BaseError],
    message: str,
    **kwargs: Any
) -> None:
    """Handle an error by logging it and raising the appropriate exception.
    
    Args:
        error_type: Type of error to raise
        message: Error message
        **kwargs: Additional context to include
    """
    logger.error(
        message,
        error_type=error_type.__name__,
        **kwargs
    )
    raise error_type(message, **kwargs)

def error_handler(
    error_type: Type[BaseError]
) -> Callable[[F], F]:
    """Decorator to wrap functions with error handling.
    
    Args:
        error_type: Type of error to catch and re-raise
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(
                    error_type,
                    str(e),
                    function=func.__name__,
                    args=args,
                    kwargs=kwargs
                )
        return wrapper  # type: ignore
    return decorator

@contextmanager
def error_context(
    error_type: Type[BaseError],
    message: str,
    **kwargs: Any
):
    """Context manager for handling errors in a specific context.
    
    Args:
        error_type: Type of error to catch and re-raise
        message: Error message
        **kwargs: Additional context to include
    """
    try:
        yield
    except Exception as e:
        handle_error(
            error_type,
            f"{message}: {str(e)}",
            **kwargs
        )

def is_retryable_error(error: Exception) -> bool:
    """Determine if an error should trigger a retry.
    
    Args:
        error: The exception to check
        
    Returns:
        bool: Whether the error is retryable
    """
    # Add specific error types that should trigger retries
    retryable_errors = (
        TelegramError,
        GitHubError,
        DatabaseError
    )
    
    return isinstance(error, retryable_errors)
