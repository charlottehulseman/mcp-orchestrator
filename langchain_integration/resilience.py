"""
Resilience Module

Provides retry logic, circuit breakers, and error handling for production deployments.
Ensures robust operation even when individual tools or servers fail.
"""

import asyncio
from typing import Callable, Any, Optional, TypeVar
from functools import wraps
import time


T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        *args: Positional arguments for func
        config: Retry configuration
        **kwargs: Keyword arguments for func
    
    Returns:
        Result of successful function call
    
    Raises:
        Exception: Last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    delay = config.initial_delay
    
    for attempt in range(1, config.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt == config.max_attempts:
                # last attempt
                raise
            
            print(f"⚠️  Attempt {attempt}/{config.max_attempts} failed: {e}")
            print(f"   Retrying in {delay:.1f}s...")
            
            await asyncio.sleep(delay)
            delay = min(delay * config.backoff_factor, config.max_delay)
    
    raise last_exception


def retry_on_failure(config: Optional[RetryConfig] = None):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Usage:
        @retry_on_failure(config=RetryConfig(max_attempts=5))
        async def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for failing fast when a service is down.
    
    States:
        CLOSED: Normal operation, requests go through
        OPEN: Service is failing, requests fail immediately
        HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        if self.state == "OPEN":
            # Check if should try recovery
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.success_count = 0
                print("🔄 Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
                return False
            return True
        return False
    
    def record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        
        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = "CLOSED"
                print("✅ Circuit breaker: HALF_OPEN → CLOSED (recovered)")
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            self.state = "OPEN"
            print(" Circuit breaker: HALF_OPEN → OPEN (recovery failed)")
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            print(f" Circuit breaker: CLOSED → OPEN ({self.failure_count} failures)")
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function through the circuit breaker.
        
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.is_open():
            raise Exception(f"Circuit breaker is OPEN (service unavailable)")
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class FallbackHandler:
    """Provides fallback values when tools fail."""
    
    @staticmethod
    def get_fallback(tool_name: str, error: Exception) -> dict:
        """
        Get fallback response for a failed tool call.
        
        Args:
            tool_name: Name of the tool that failed
            error: The exception that occurred
        
        Returns:
            Fallback response dictionary
        """
        return {
            "error": str(error),
            "fallback": True,
            "tool": tool_name,
            "message": f"Tool '{tool_name}' unavailable. Using fallback data.",
            "data": FallbackHandler._get_demo_data(tool_name)
        }
    
    @staticmethod
    def _get_demo_data(tool_name: str) -> dict:
        """Get demo/default data for a tool."""
        if "fighter_stats" in tool_name:
            return {
                "name": "Unknown Fighter",
                "record": "N/A",
                "note": "Fighter data unavailable"
            }
        elif "odds" in tool_name:
            return {
                "odds": "N/A",
                "note": "Betting data unavailable"
            }
        elif "news" in tool_name:
            return {
                "articles": [],
                "note": "News data unavailable"
            }
        else:
            return {"note": "Data unavailable"}


async def call_with_timeout(
    func: Callable[..., T],
    timeout: float,
    *args,
    **kwargs
) -> T:
    """
    Call an async function with a timeout.
    
    Args:
        func: Async function to call
        timeout: Timeout in seconds
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Function result
    
    Raises:
        asyncio.TimeoutError: If function times out
    """
    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)

# Global circuit breakers for each server
_circuit_breakers = {}

def get_circuit_breaker(server_name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a server."""
    if server_name not in _circuit_breakers:
        _circuit_breakers[server_name] = CircuitBreaker()
    return _circuit_breakers[server_name]