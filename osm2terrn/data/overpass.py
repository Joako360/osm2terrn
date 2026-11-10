"""Bounded OSMnx requests to Overpass endpoints."""

from __future__ import annotations

import random
import re
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, TypeVar
from urllib.parse import urlsplit

import osmnx as ox
import osmnx._overpass as ox_overpass
import requests

from osm2terrn.utils.logger import get_logger, log_warning

logger = get_logger("overpass")
_T = TypeVar("_T")
_OVERPASS_PATCH_LOCK = threading.RLock()
_RETRYABLE_STATUS_CODES = {408, 425, 429}
_BASE_BACKOFF_SECONDS = 1.0
_MAX_BACKOFF_SECONDS = 30.0


class _ScopedRequests:
    """Proxy OSMnx Overpass HTTP calls to enforce the layer time budget."""

    def __init__(self, deadline: float, endpoint: str) -> None:
        self._deadline = deadline
        self._endpoint_host = urlsplit(endpoint).hostname

    def __getattr__(self, name: str) -> Any:
        return getattr(requests, name)

    def get(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self._request(requests.get, url, *args, **kwargs)

    def post(self, url: str, *args: Any, **kwargs: Any) -> requests.Response:
        return self._request(requests.post, url, *args, **kwargs)

    def _request(
        self,
        request: Callable[..., requests.Response],
        url: str,
        *args: Any,
        **kwargs: Any,
    ) -> requests.Response:
        if urlsplit(url).hostname != self._endpoint_host:
            return request(url, *args, **kwargs)

        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise requests.Timeout("Overpass layer time budget exhausted.")

        kwargs["timeout"] = _bounded_timeout(kwargs.get("timeout"), remaining)
        response = request(url, *args, **kwargs)
        if response.status_code >= 400:
            raise requests.HTTPError(
                f"Overpass returned HTTP {response.status_code}.",
                response=response,
            )
        return response


def _bounded_timeout(timeout: Any, remaining: float) -> float | tuple[float, float]:
    if isinstance(timeout, tuple):
        connect_timeout, read_timeout = timeout
        bounded_connect_timeout = (
            remaining
            if connect_timeout is None
            else min(float(connect_timeout), remaining)
        )
        bounded_read_timeout = (
            remaining
            if read_timeout is None
            else min(float(read_timeout), remaining)
        )
        return bounded_connect_timeout, bounded_read_timeout
    if timeout is None:
        return remaining
    return min(float(timeout), remaining)


def _http_status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    match = re.search(
        r"(?:responded:\s*|HTTP(?:\s+status\s+code)?\s*[:=]?\s*)(\d{3})",
        str(exc),
        re.I,
    )
    return int(match.group(1)) if match else None


def _is_retryable(exc: Exception) -> bool:
    status_code = _http_status_code(exc)
    if status_code is not None:
        return status_code in _RETRYABLE_STATUS_CODES or 500 <= status_code <= 599
    return isinstance(exc, (requests.Timeout, requests.ConnectionError))


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    value = headers.get("Retry-After") if headers is not None else None
    if not value:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


def _run_with_overpass_endpoint(
    request: Callable[[], _T],
    *,
    endpoint: str,
    deadline: float,
) -> _T:
    with _OVERPASS_PATCH_LOCK:
        original_requests = ox_overpass.requests
        original_pause = ox_overpass._get_overpass_pause
        original_endpoint = ox.settings.overpass_url
        original_log_console = ox.settings.log_console
        original_log_file = ox.settings.log_file
        pause_depth = 0

        def bounded_pause(
            base_endpoint: str,
            recursion_pause: float = 5,
            default_pause: float = 60,
        ) -> float:
            nonlocal pause_depth
            remaining = max(0.0, deadline - time.monotonic())
            if pause_depth:
                return remaining
            if remaining == 0:
                return 0.0

            pause_depth += 1
            try:
                pause = original_pause(
                    base_endpoint,
                    recursion_pause=min(recursion_pause, remaining),
                    default_pause=0,
                )
                return min(max(0.0, pause), max(0.0, deadline - time.monotonic()))
            finally:
                pause_depth -= 1

        try:
            ox_overpass.requests = _ScopedRequests(deadline, endpoint)
            ox_overpass._get_overpass_pause = bounded_pause
            ox.settings.overpass_url = endpoint
            ox.settings.log_console = False
            ox.settings.log_file = False
            return request()
        finally:
            ox_overpass.requests = original_requests
            ox_overpass._get_overpass_pause = original_pause
            ox.settings.overpass_url = original_endpoint
            ox.settings.log_console = original_log_console
            ox.settings.log_file = original_log_file


def call_with_retries(
    request: Callable[[], _T],
    *,
    endpoints: tuple[str, ...],
    max_attempts: int,
    max_elapsed_seconds: int,
) -> _T:
    """Run one OSMnx layer query with bounded retries across Overpass endpoints."""

    if not endpoints:
        raise ValueError("At least one Overpass endpoint is required")
    if max_attempts <= 0 or max_elapsed_seconds <= 0:
        raise ValueError("Overpass retry limits must be positive")

    deadline = time.monotonic() + max_elapsed_seconds
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        endpoint = endpoints[attempt % len(endpoints)]
        try:
            return _run_with_overpass_endpoint(
                request,
                endpoint=endpoint,
                deadline=deadline,
            )
        except Exception as exc:
            last_error = exc
            if not _is_retryable(exc):
                raise
            if attempt + 1 >= max_attempts:
                break

            remaining = deadline - time.monotonic()
            retry_after = _retry_after_seconds(exc)
            if retry_after is None:
                backoff_cap = min(
                    _MAX_BACKOFF_SECONDS,
                    _BASE_BACKOFF_SECONDS * (2 ** min(attempt, 5)),
                )
                delay = random.uniform(0.0, backoff_cap)
            else:
                delay = retry_after
            if delay >= remaining:
                break

            status_code = _http_status_code(exc)
            diagnostic = f"HTTP {status_code}" if status_code is not None else type(exc).__name__
            log_warning(
                logger,
                f"Temporary Overpass error ({diagnostic}); retrying "
                f"attempt {attempt + 2}/{max_attempts} after {delay:.1f}s.",
            )
            time.sleep(delay)

    if last_error is not None:
        raise last_error
    raise requests.Timeout("Overpass layer time budget exhausted.")
