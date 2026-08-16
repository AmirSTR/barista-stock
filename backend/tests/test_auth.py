import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from app.api.auth import require_admin_api_key, validate_telegram_init_data
from app.core.config import settings


def _signed_init_data(bot_token: str, auth_date: int) -> str:
    values = {
        "auth_date": str(auth_date),
        "query_id": "AAEAAAE",
        "user": json.dumps(
            {"id": 12345, "first_name": "Иван"},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(values.items())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    values["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(values)


def test_validate_telegram_init_data_signature_and_ttl():
    token = "123456:test-token"
    init_data = _signed_init_data(token, auth_date=1_700_000_000)

    parsed = validate_telegram_init_data(
        init_data,
        token,
        max_age_seconds=300,
        now=1_700_000_100,
    )
    assert parsed["user"]["id"] == 12345

    with pytest.raises(ValueError, match="expired"):
        validate_telegram_init_data(
            init_data,
            token,
            max_age_seconds=30,
            now=1_700_000_100,
        )

    with pytest.raises(ValueError, match="signature"):
        validate_telegram_init_data(
            init_data.replace("%D0%98", "%D0%90", 1),
            token,
            max_age_seconds=300,
            now=1_700_000_100,
        )


@pytest.mark.asyncio
async def test_admin_api_key_is_fail_closed(monkeypatch):
    monkeypatch.setattr(settings, "API_ADMIN_TOKEN", "server-secret")

    await require_admin_api_key("server-secret")
    with pytest.raises(HTTPException) as exc:
        await require_admin_api_key("wrong-secret")
    assert exc.value.status_code == 401
