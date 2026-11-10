from __future__ import annotations

from collections import OrderedDict

import osmnx._overpass as ox_overpass
import pytest
import requests

from osm2terrn.data import overpass


def _response(status_code: int, headers: dict[str, str] | None = None) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response.headers.update(headers or {})
    return response


def _post_current_endpoint():
    endpoint = ox_overpass.settings.overpass_url
    return ox_overpass.requests.post(f"{endpoint}/interpreter")


@pytest.mark.parametrize("status_code", [429, 502, 503, 504])
def test_temporary_http_statuses_retry_with_attempt_limit(
    monkeypatch, status_code: int
) -> None:
    calls: list[str] = []
    sleeps: list[float] = []

    def fake_post(url: str, **_kwargs):
        calls.append(url)
        return _response(status_code)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.random, "uniform", lambda _low, _high: 0.0)
    monkeypatch.setattr(overpass.time, "sleep", sleeps.append)

    with pytest.raises(requests.HTTPError) as error:
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=3,
            max_elapsed_seconds=120,
        )

    assert error.value.response.status_code == status_code
    assert len(calls) == 3
    assert sleeps == [0.0, 0.0]


@pytest.mark.parametrize(
    "error",
    [requests.ReadTimeout("read timed out"), requests.ConnectionError("connection failed")],
)
def test_temporary_transport_errors_retry(monkeypatch, error: Exception) -> None:
    calls = 0

    def fake_post(_url: str, **_kwargs):
        nonlocal calls
        calls += 1
        raise error

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.random, "uniform", lambda _low, _high: 0.0)
    monkeypatch.setattr(overpass.time, "sleep", lambda _delay: None)

    with pytest.raises(type(error)):
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=3,
            max_elapsed_seconds=120,
        )

    assert calls == 3


def test_permanent_http_error_is_not_retried(monkeypatch) -> None:
    calls = 0

    def fake_post(_url: str, **_kwargs):
        nonlocal calls
        calls += 1
        return _response(400)

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.HTTPError):
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=3,
            max_elapsed_seconds=120,
        )

    assert calls == 1


def test_retry_after_is_respected_and_alternate_endpoint_is_used(monkeypatch) -> None:
    urls: list[str] = []
    sleeps: list[float] = []
    responses = iter(
        [
            _response(429, {"Retry-After": "2"}),
            _response(200),
        ]
    )

    def fake_post(url: str, **_kwargs):
        urls.append(url)
        return next(responses)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.time, "sleep", sleeps.append)

    result = overpass.call_with_retries(
        _post_current_endpoint,
        endpoints=("https://primary.example/api", "https://alternate.example/api"),
        max_attempts=3,
        max_elapsed_seconds=120,
    )

    assert result.status_code == 200
    assert urls == [
        "https://primary.example/api/interpreter",
        "https://alternate.example/api/interpreter",
    ]
    assert sleeps == [2.0]


def test_retry_diagnostics_do_not_include_sensitive_response_urls(monkeypatch) -> None:
    messages: list[str] = []
    responses = [_response(502), _response(200)]
    responses[0].url = "https://overpass.example/interpreter?token=secret-value"
    responses[1].url = "https://overpass.example/interpreter"

    def fake_post(_url: str, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.random, "uniform", lambda _low, _high: 0.0)
    monkeypatch.setattr(overpass.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        overpass,
        "log_warning",
        lambda _logger, message: messages.append(message),
    )

    result = overpass.call_with_retries(
        _post_current_endpoint,
        endpoints=("https://overpass.example/api",),
        max_attempts=2,
        max_elapsed_seconds=120,
    )

    assert result.status_code == 200
    assert messages
    assert all("secret-value" not in message and "?" not in message for message in messages)


def test_retry_after_beyond_time_budget_does_not_start_another_attempt(monkeypatch) -> None:
    calls = 0
    sleeps: list[float] = []

    def fake_post(_url: str, **_kwargs):
        nonlocal calls
        calls += 1
        return _response(429, {"Retry-After": "30"})

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.time, "sleep", sleeps.append)

    with pytest.raises(requests.HTTPError):
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=3,
            max_elapsed_seconds=1,
        )

    assert calls == 1
    assert sleeps == []


def test_elapsed_budget_caps_request_timeouts_and_stops_retries(monkeypatch) -> None:
    elapsed = 0.0
    request_timeouts: list[float] = []

    def fake_monotonic() -> float:
        return elapsed

    def fake_sleep(delay: float) -> None:
        nonlocal elapsed
        elapsed += delay

    def fake_post(_url: str, *, timeout: float, **_kwargs):
        nonlocal elapsed
        request_timeouts.append(timeout)
        if timeout <= 0.31:
            elapsed += timeout
            raise requests.Timeout("request budget reached")
        elapsed += 0.6
        return _response(502)

    monkeypatch.setattr(overpass.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(overpass.time, "sleep", fake_sleep)
    monkeypatch.setattr(overpass.random, "uniform", lambda _low, _high: 0.1)
    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(requests.Timeout):
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=4,
            max_elapsed_seconds=1,
        )

    assert request_timeouts == pytest.approx([1, 0.3])
    assert elapsed == pytest.approx(1.0)


def test_exponential_backoff_uses_full_jitter_cap(monkeypatch) -> None:
    sleeps: list[float] = []
    caps: list[float] = []

    def fake_post(_url: str, **_kwargs):
        return _response(502)

    def maximum_jitter(low: float, high: float) -> float:
        assert low == 0.0
        caps.append(high)
        return high

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(overpass.random, "uniform", maximum_jitter)
    monkeypatch.setattr(overpass.time, "sleep", sleeps.append)

    with pytest.raises(requests.HTTPError):
        overpass.call_with_retries(
            _post_current_endpoint,
            endpoints=("https://primary.example/api",),
            max_attempts=8,
            max_elapsed_seconds=120,
        )

    assert caps == [1, 2, 4, 8, 16, 30, 30]
    assert sleeps == caps


@pytest.mark.parametrize("status_code", [429, 504])
def test_osmnx_builtin_retries_are_intercepted(monkeypatch, status_code: int) -> None:
    calls = 0
    pause_calls = 0
    responses = [_response(status_code), _response(200)]
    responses[1]._content = b'{"elements": []}'
    responses[1].url = "https://primary.example/api/interpreter"

    def fake_post(_url: str, **_kwargs):
        nonlocal calls
        response = responses[calls]
        calls += 1
        return response

    def fake_pause(_endpoint: str, **_kwargs) -> float:
        nonlocal pause_calls
        pause_calls += 1
        return 0.0

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(ox_overpass._http, "_config_dns", lambda _endpoint: None)
    monkeypatch.setattr(ox_overpass._http, "_retrieve_from_cache", lambda _url: None)
    monkeypatch.setattr(ox_overpass._http, "_save_to_cache", lambda *_args: None)
    monkeypatch.setattr(ox_overpass, "_get_overpass_pause", fake_pause)
    monkeypatch.setattr(overpass.random, "uniform", lambda _low, _high: 0.0)
    monkeypatch.setattr(overpass.time, "sleep", lambda _delay: None)

    result = overpass.call_with_retries(
        lambda: ox_overpass._overpass_request(OrderedDict(data="[out:json];")),
        endpoints=("https://primary.example/api",),
        max_attempts=3,
        max_elapsed_seconds=120,
    )

    assert result == {"elements": []}
    assert calls == 2
    assert pause_calls == 2
