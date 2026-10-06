from typing import Any


SENSITIVE_KEYS = {
    "password", "passwd", "pwd",
    "token", "access_token", "bearer_token",
    "secret", "client_secret",
    "api_key", "apikey",
}

MASK = "***"


def mask(data: Any) -> Any:

    if isinstance(data, dict):
        return {
            key: (MASK if _is_sensitive(key) else mask(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [mask(item) for item in data]

    return data


def _is_sensitive(key: str) -> bool:
    return key.lower() in SENSITIVE_KEYS


def truncate(text: str, limit: int = 500) -> str:

    if len(text) <= limit:
        return text
    return f"{text[:limit]}... (truncated, total {len(text)} chars)"