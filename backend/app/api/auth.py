import hashlib
import hmac
import json
import time
from typing import Annotated, Any, Dict, Optional
from urllib.parse import parse_qsl

from fastapi import Header, HTTPException, status

from app.core.config import settings


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int,
    now: Optional[int] = None,
) -> Dict[str, Any]:
    """Validate Telegram Mini App initData and return its decoded fields."""
    values = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = values.pop("hash", None)
    if not received_hash:
        raise ValueError("Telegram initData has no hash")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(values.items())
    )
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Telegram initData signature is invalid")

    try:
        auth_date = int(values["auth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Telegram initData has an invalid auth_date") from exc

    current_time = int(time.time()) if now is None else now
    if auth_date > current_time + 30:
        raise ValueError("Telegram initData auth_date is in the future")
    if current_time - auth_date > max_age_seconds:
        raise ValueError("Telegram initData has expired")

    decoded: Dict[str, Any] = dict(values)
    for field in ("user", "receiver", "chat"):
        if field in decoded:
            try:
                decoded[field] = json.loads(decoded[field])
            except json.JSONDecodeError as exc:
                raise ValueError(f"Telegram initData contains invalid {field} JSON") from exc
    return decoded


async def require_telegram_user(
    x_telegram_init_data: Annotated[
        Optional[str], Header(alias="X-Telegram-Init-Data")
    ] = None,
) -> Dict[str, Any]:
    if not settings.TELEGRAM_AUTH_REQUIRED:
        return {}
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram authentication is enabled but BOT_TOKEN is not configured",
        )
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram Mini App authorization is required",
        )

    try:
        return validate_telegram_init_data(
            x_telegram_init_data,
            settings.TELEGRAM_BOT_TOKEN,
            settings.TELEGRAM_INIT_DATA_TTL_SECONDS,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


async def require_admin_api_key(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
) -> None:
    if not settings.API_ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative API is disabled until API_ADMIN_TOKEN is configured",
        )
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.API_ADMIN_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative API key",
        )
