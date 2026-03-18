"""
Centralized error handling for ChatChaos.
Provides user-friendly error messages, logging, and recovery strategies.
"""

import logging
import traceback
import json
from typing import Optional, Dict, Any, Callable
from enum import Enum
from functools import wraps
from datetime import datetime

# Configure logging
import os as _os
_log_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'logs')
_os.makedirs(_log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_os.path.join(_log_dir, 'error.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for better handling"""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    AUTH_ERROR = "auth_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"

class ChatChaosError(Exception):
    """Base exception for ChatChaos"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_message: Optional[str] = None,
        recovery_suggestion: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._default_user_message()
        self.recovery_suggestion = recovery_suggestion or self._default_recovery()
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        super().__init__(self.message)
    
    def _default_user_message(self) -> str:
        """Get default user-friendly message"""
        messages = {
            ErrorCategory.API_ERROR: "Failed to reach AI service. Please try again.",
            ErrorCategory.DATABASE_ERROR: "Unable to save data. Please try again.",
            ErrorCategory.AUTH_ERROR: "Authentication failed. Please log in again.",
            ErrorCategory.VALIDATION_ERROR: "Invalid input. Please check your data.",
            ErrorCategory.FILE_ERROR: "File operation failed. Please try again.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please wait a moment and try again.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please contact support.",
        }
        return messages.get(self.category, "An error occurred.")
    
    def _default_recovery(self) -> str:
        """Get default recovery suggestion"""
        suggestions = {
            ErrorCategory.API_ERROR: "Check your internet connection and try again.",
            ErrorCategory.DATABASE_ERROR: "Ensure the database is running and try again.",
            ErrorCategory.AUTH_ERROR: "Log in with your credentials.",
            ErrorCategory.VALIDATION_ERROR: "Review the input and correct any errors.",
            ErrorCategory.FILE_ERROR: "Ensure the file exists and is accessible.",
            ErrorCategory.RATE_LIMIT: "Wait a few seconds before retrying.",
            ErrorCategory.UNKNOWN: "Restart the application.",
        }
        return suggestions.get(self.category, "Try again later.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "user_message": self.user_message,
            "recovery_suggestion": self.recovery_suggestion,
            "timestamp": self.timestamp,
            "details": self.details,
        }

class APIError(ChatChaosError):
    """API-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        self.status_code = status_code
        
        # Customize message based on status code
        if status_code == 429:
            category = ErrorCategory.RATE_LIMIT
            user_msg = "Too many API requests. Please wait a moment."
            recovery = "The system will automatically retry. No action needed."
        elif status_code in [500, 502, 503, 504]:
            category = ErrorCategory.API_ERROR
            user_msg = "AI service is temporarily unavailable."
            recovery = "Please try again in a few minutes."
        elif status_code in [401, 403]:
            category = ErrorCategory.AUTH_ERROR
            user_msg = "API authentication failed."
            recovery = "Check your API key and try again."
        else:
            category = ErrorCategory.API_ERROR
            user_msg = f"API error (status: {status_code})" if status_code else "API error"
            recovery = "Please try again."
        
        super().__init__(
            message=message,
            category=category,
            user_message=user_msg,
            recovery_suggestion=recovery,
            details={"status_code": status_code},
            **kwargs
        )

class DatabaseError(ChatChaosError):
    """Database-related errors"""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE_ERROR,
            details={"operation": operation},
            **kwargs
        )

class ValidationError(ChatChaosError):
    """Validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION_ERROR,
            details={"field": field},
            **kwargs
        )

class RateLimitError(ChatChaosError):
    """Rate limit errors"""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.WARNING,
            user_message=f"Too many requests. Please wait {retry_after} seconds.",
            recovery_suggestion="The system will automatically retry.",
            details={"retry_after": retry_after},
            **kwargs
        )

class CircuitBreaker:
    """Circuit breaker pattern for failing services"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed | open | half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == "open":
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure > self.recovery_timeout:
                    self.state = "half_open"
                    logger.info(f"[circuit-breaker] {self.name} entering half-open state")
                else:
                    raise Exception(
                        f"Circuit breaker {self.name} is open. "
                        f"Service unavailable. Retry in {self.recovery_timeout - int(time_since_failure)}s"
                    )
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info(f"[circuit-breaker] {self.name} closed (recovered)")
            
            return result
        
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            logger.error(
                f"[circuit-breaker] {self.name} failure #{self.failure_count}: {str(e)}"
            )
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"[circuit-breaker] {self.name} opened after {self.failure_count} failures"
                )
            
            raise

class ErrorLogger:
    """Structured error logging"""
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log error with context"""
        
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "user_action": user_action,
        }
        
        # Log based on error type
        if isinstance(error, ChatChaosError):
            log_level = logging.WARNING if error.severity == ErrorSeverity.WARNING else logging.ERROR
            error_info["category"] = error.category.value
            error_info["user_message"] = error.user_message
            error_info["recovery_suggestion"] = error.recovery_suggestion
        else:
            log_level = logging.ERROR
        
        logger.log(log_level, json.dumps(error_info, indent=2))
        
        return error_info

def safe_operation(
    operation_name: str,
    retries: int = 3,
    backoff_factor: float = 2.0,
):
    """Decorator for safe operations with retry logic"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(retries):
                try:
                    logger.info(f"[{operation_name}] Attempt {attempt + 1}/{retries}")
                    return func(*args, **kwargs)
                
                except ChatChaosError as e:
                    last_error = e
                    
                    # Don't retry validation errors
                    if e.category == ErrorCategory.VALIDATION_ERROR:
                        logger.error(f"[{operation_name}] Validation error: {e.message}")
                        raise
                    
                    # For rate limits, wait and retry
                    if e.category == ErrorCategory.RATE_LIMIT:
                        wait_time = int(e.details.get("retry_after", 60))
                        logger.warning(f"[{operation_name}] Rate limited. Retrying in {wait_time}s")
                        import time
                        time.sleep(wait_time)
                        continue
                    
                    # For other errors, exponential backoff
                    if attempt < retries - 1:
                        wait_time = (backoff_factor ** attempt)
                        logger.warning(
                            f"[{operation_name}] Failed: {e.message}. "
                            f"Retrying in {wait_time:.1f}s"
                        )
                        import time
                        time.sleep(wait_time)
                        continue
                    
                    raise
                
                except Exception as e:
                    last_error = e
                    
                    if attempt < retries - 1:
                        wait_time = (backoff_factor ** attempt)
                        logger.error(
                            f"[{operation_name}] Error: {str(e)}. "
                            f"Retrying in {wait_time:.1f}s"
                        )
                        import time
                        time.sleep(wait_time)
                        continue
                    
                    ErrorLogger.log_error(
                        e,
                        context={"operation": operation_name},
                        user_action="retried operation"
                    )
                    raise
            
            # If we get here, all retries failed
            if last_error:
                raise last_error
        
        return wrapper
    return decorator

# Global circuit breakers
gemini_breaker = CircuitBreaker(
    name="gemini_api",
    failure_threshold=5,
    recovery_timeout=300,  # 5 minutes
)

database_breaker = CircuitBreaker(
    name="database",
    failure_threshold=3,
    recovery_timeout=60,  # 1 minute
)

bridge_breaker = CircuitBreaker(
    name="whatsapp_bridge",
    failure_threshold=5,
    recovery_timeout=120,  # 2 minutes
)

# Example usage functions
def check_gemini_health() -> bool:
    """Check if Gemini API is healthy"""
    try:
        def health_check():
            # Placeholder - actual health check would call Gemini
            return True
        
        result = gemini_breaker.call(health_check)
        return result
    except Exception as e:
        logger.error(f"Gemini API health check failed: {e}")
        return False

def check_database_health() -> bool:
    """Check if database is healthy"""
    try:
        from core.database import get_connection
        
        def health_check():
            with get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        
        result = database_breaker.call(health_check)
        return result
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def check_bridge_health() -> bool:
    """Check if WhatsApp bridge is healthy"""
    try:
        import requests
        
        def health_check():
            response = requests.get('http://localhost:3001/health', timeout=5)
            return response.status_code == 200
        
        result = bridge_breaker.call(health_check)
        return result
    except Exception as e:
        logger.error(f"Bridge health check failed: {e}")
        return False

def get_system_health() -> Dict[str, bool]:
    """Get overall system health"""
    return {
        "gemini_api": check_gemini_health(),
        "database": check_database_health(),
        "whatsapp_bridge": check_bridge_health(),
    }
