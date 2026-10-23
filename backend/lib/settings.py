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


def cors_origins() -> list[str]:
    """Optional comma-separated CORS_ORIGINS.

    Default (unset/empty) is same-origin only: the React app and API share one
    domain, so no CORS header is needed. Never a credentialed wildcard; never raises.
    """
    origins = []
    for value in os.environ.get("CORS_ORIGINS", "").split(","):
        origin = http_origin(value)
        if origin and origin not in origins:
            origins.append(origin)
        elif value.strip() and not origin:
            logging.warning("Ignoring invalid CORS_ORIGINS entry; use an HTTP(S) origin without paths or wildcards")
    return origins


def request_origin(request) -> str:
    """Public origin of an incoming request, honoring X-Forwarded-Proto (Render proxy)."""
    proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip().lower()
    if proto not in {"http", "https"}:
        proto = request.url.scheme
    host = request.headers.get("host", "").strip() or request.url.netloc
    return http_origin(f"{proto}://{host}")


def public_origin() -> str:
    """Optional site origin for places without a request (e.g. email links), taken from GOOGLE_REDIRECT_URI."""
    try:
        parsed = urlsplit(os.environ.get("GOOGLE_REDIRECT_URI", "").strip())
        return http_origin(f"{parsed.scheme}://{parsed.netloc}") if parsed.netloc else ""
    except ValueError:
        return ""


def preview_database_enabled() -> bool:
    return (os.environ.get("RENDER", "").strip().lower() != "true"
            and bool(os.environ.get("PREVIEW_POSTGRES_DATA", "").strip()))