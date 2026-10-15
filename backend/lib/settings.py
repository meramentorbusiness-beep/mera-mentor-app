"""Small environment helpers; no URLs or credentials are guessed."""
import logging
import os
from urllib.parse import urlsplit


def http_origin(value: str) -> str:
    value = value.strip().rstrip("/")
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Validate malformed ports without logging the value.
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.path
                or parsed.query or parsed.fragment or port == 0):
            return ""
        return f"{parsed.scheme}://{parsed.netloc.lower()}"
    except ValueError:
        return ""


def frontend_url() -> str:
    return http_origin(os.environ.get("FRONTEND_URL", ""))


def cors_origins() -> list[str]:
    """Empty means same-origin only, never a credentialed wildcard."""
    origins = []
    values = [os.environ.get("FRONTEND_URL", "")]
    values += os.environ.get("CORS_ORIGINS", "").split(",")
    for value in values:
        origin = http_origin(value)
        if origin and origin not in origins:
            origins.append(origin)
        elif value.strip() and not origin:
            logging.warning("Ignoring invalid FRONTEND_URL/CORS_ORIGINS entry; use an HTTP(S) origin without paths or wildcards")
    return origins


def preview_database_enabled() -> bool:
    return (os.environ.get("RENDER", "").strip().lower() != "true"
            and bool(os.environ.get("PREVIEW_POSTGRES_DATA", "").strip()))