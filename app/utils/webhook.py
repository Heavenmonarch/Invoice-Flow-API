import hashlib
import hmac
import json
import logging
import time
import httpx
from datetime import datetime, timezone
from uuid import UUID

logger = logging.getLogger(__name__)

# Events your system can fire
SALE_CREATED = "sale.created"
COMMISSION_APPROVED = "commission.approved"
COMMISSION_PAID = "commission.paid"
COMMISSION_DISPUTED = "commission.disputed"
USER_INVITED = "user.invited"
USER_DEACTIVATED = "user.deactivated"

MAX_RETRIES = 3
RETRY_DELAYS = [5, 30, 120]  # seconds between retries: 5s, 30s, 2min
TIMEOUT_SECONDS = 10


def sign_payload(secret: str, payload: str) -> str:
    """
    Creates an HMAC-SHA256 signature of the payload.
    The receiving server uses this to verify the request
    genuinely came from CommissionTrack and wasn't tampered with.
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def build_payload(
    event: str,
    data: dict,
    organization_id: UUID,
) -> dict:
    """
    Wraps the event data in a standard envelope.
    Every webhook your system sends has this same outer structure
    regardless of event type — makes it easy for receivers to
    parse consistently.
    """
    return {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "organization_id": str(organization_id),
        "data": data,
    }


async def deliver_webhook(
    url: str,
    secret: str,
    event: str,
    payload: dict,
) -> tuple[bool, int | None, str | None]:
    """
    Attempts to deliver a webhook with retries.
    Returns (success, response_status, response_body).

    Retries up to MAX_RETRIES times with exponential backoff
    on network errors or non-2xx responses.
    """
    payload_str = json.dumps(payload, default=str)
    signature = sign_payload(secret, payload_str)

    headers = {
        "Content-Type": "application/json",
        "X-CommissionTrack-Event": event,
        "X-CommissionTrack-Signature": f"sha256={signature}",
        "X-CommissionTrack-Timestamp": payload["timestamp"],
        "User-Agent": "CommissionTrack-Webhooks/1.0",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    url,
                    content=payload_str,
                    headers=headers,
                )

            success = 200 <= response.status_code < 300
            body = response.text[:500]  # Truncate long responses

            if success:
                logger.info(
                    "Webhook delivered | event=%s | url=%s | status=%s | attempt=%d",
                    event, url, response.status_code, attempt,
                )
                return True, response.status_code, body

            logger.warning(
                "Webhook delivery failed | event=%s | url=%s | "
                "status=%s | attempt=%d/%d",
                event, url, response.status_code, attempt, MAX_RETRIES,
            )

        except httpx.TimeoutException:
            logger.warning(
                "Webhook timeout | event=%s | url=%s | attempt=%d/%d",
                event, url, attempt, MAX_RETRIES,
            )
        except httpx.RequestError as e:
            logger.warning(
                "Webhook request error | event=%s | url=%s | "
                "error=%s | attempt=%d/%d",
                event, url, str(e), attempt, MAX_RETRIES,
            )

        # Wait before retry — except on last attempt
        if attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[attempt - 1]
            logger.info(
                "Retrying webhook in %ds | event=%s | url=%s",
                delay, event, url,
            )
            time.sleep(delay)

    return False, None, "Max retries exceeded"