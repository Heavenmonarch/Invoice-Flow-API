import logging
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


MAX_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 60 * 15  
ATTEMPT_WINDOW_SECONDS = 60 * 10  # attempts reset after 10 min of no failures


def _get_redis():
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


def _attempt_key(email: str) -> str:
    """Redis key tracking failed attempt count for an email."""
    return f"login_attempts:{email.lower()}"


def _lockout_key(email: str) -> str:
    """Redis key that exists only while the account is locked."""
    return f"login_lockout:{email.lower()}"




async def is_locked_out(email: str) -> bool:
    """
    Returns True if this email is currently locked out.
    Checks for the lockout key in Redis.
    Fails open if Redis is unavailable.
    """
    try:
        redis = _get_redis()
        result = await redis.exists(_lockout_key(email))
        await redis.aclose()
        return bool(result)
    except Exception as e:
        logger.error("Lockout check failed for %s: %s", email, str(e))
        return False  # Fail open — don't block legitimate users


async def record_failed_attempt(email: str) -> int:
    """
    Increments the failed attempt counter for this email.
    Locks the account if the threshold is reached.
    Returns the current attempt count.
    Fails silently if Redis is unavailable.
    """
    try:
        redis = _get_redis()
        attempt_key = _attempt_key(email)

        pipe = redis.pipeline()
        await pipe.incr(attempt_key)
        await pipe.expire(attempt_key, ATTEMPT_WINDOW_SECONDS)
        results = await pipe.execute()
        attempts = results[0]

        if attempts >= MAX_ATTEMPTS:
            # Lock the account
            await redis.set(
                _lockout_key(email),
                "locked",
                ex=LOCKOUT_WINDOW_SECONDS,
            )
            logger.warning(
                "Account locked out after %d failed attempts: %s",
                attempts,
                email,
            )

        await redis.aclose()
        return attempts

    except Exception as e:
        logger.error("Failed to record login attempt for %s: %s", email, str(e))
        return 0


async def clear_failed_attempts(email: str) -> None:
    """
    Clears the failed attempt counter and any lockout on successful login.
    Called immediately after a successful authentication.
    Fails silently if Redis is unavailable.
    """
    try:
        redis = _get_redis()
        await redis.delete(_attempt_key(email))
        await redis.delete(_lockout_key(email))
        await redis.aclose()
        logger.info("Cleared login attempts for %s", email)
    except Exception as e:
        logger.error("Failed to clear login attempts for %s: %s", email, str(e))


async def get_remaining_attempts(email: str) -> int:
    """
    Returns how many attempts the user has left before lockout.
    Used to include in the error response so the user knows
    how many tries they have left.
    """
    try:
        redis = _get_redis()
        count = await redis.get(_attempt_key(email))
        await redis.aclose()
        current = int(count) if count else 0
        return max(0, MAX_ATTEMPTS - current)
    except Exception as e:
        logger.error("Failed to get remaining attempts for %s: %s", email, str(e))
        return MAX_ATTEMPTS


async def get_lockout_ttl(email: str) -> int:
    """
    Returns seconds remaining on the lockout.
    Used to tell the user exactly how long to wait.
    """
    try:
        redis = _get_redis()
        ttl = await redis.ttl(_lockout_key(email))
        await redis.aclose()
        return max(0, ttl)
    except Exception as e:
        logger.error("Failed to get lockout TTL for %s: %s", email, str(e))
        return 0