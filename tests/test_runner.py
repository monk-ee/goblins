"""
tests/test_runner.py — Regression tests for rate-limit handling and DailyLimitError.
"""

from unittest.mock import MagicMock, patch

import pytest

from goblin.runner import (
    RESPONSES_API_MODELS,
    DailyLimitError,
    _call_responses_api,
    _parse_retry_after,
    call_model,
)


# ---------------------------------------------------------------------------
# _parse_retry_after — rate limit message parsing
# ---------------------------------------------------------------------------


def test_parse_retry_after_per_minute_limit():
    """'Please wait N second' pattern should return N (capped at 120)."""
    msg = "Please wait 45 seconds and try again."
    result = _parse_retry_after(msg)
    assert result == 45


def test_parse_retry_after_caps_at_120():
    """Per-minute wait should be capped at 120 seconds."""
    msg = "Please wait 999 seconds and try again."
    result = _parse_retry_after(msg)
    assert result == 120


def test_parse_retry_after_daily_limit_raises_per_86400s():
    """'per 86400s' in message must raise DailyLimitError."""
    msg = "RateLimitReached: quota exceeded per 86400s"
    with pytest.raises(DailyLimitError):
        _parse_retry_after(msg)


def test_parse_retry_after_daily_limit_raises_per_day():
    """'per day' in message must raise DailyLimitError."""
    msg = "You have exceeded your quota per day for this model."
    with pytest.raises(DailyLimitError):
        _parse_retry_after(msg)


def test_parse_retry_after_ratelimitreached_returns_60():
    """'RateLimitReached' without day-level suffix should return 60."""
    msg = "429 RateLimitReached"
    result = _parse_retry_after(msg)
    assert result == 60


def test_parse_retry_after_unknown_returns_none():
    """Unrecognised message returns None."""
    msg = "Something went wrong."
    result = _parse_retry_after(msg)
    assert result is None


# ---------------------------------------------------------------------------
# DailyLimitError
# ---------------------------------------------------------------------------


def test_daily_limit_error_is_runtime_error():
    err = DailyLimitError("quota hit")
    assert isinstance(err, RuntimeError)


def test_daily_limit_error_message():
    err = DailyLimitError("quota hit for model gpt-5")
    assert "gpt-5" in str(err)


# ---------------------------------------------------------------------------
# RESPONSES_API_MODELS — models routed to /responses endpoint
# ---------------------------------------------------------------------------


def test_responses_api_models_contains_gpt55():
    """gpt-5.5 must be in RESPONSES_API_MODELS (confirmed via experiment)."""
    assert "gpt-5.5" in RESPONSES_API_MODELS


def test_gpt55_not_in_reasoning_models():
    """gpt-5.5 should not be in REASONING_MODELS — it uses a different API path."""
    from goblin.words import REASONING_MODELS

    # gpt-5.5 uses responses API, not chat.completions with max_completion_tokens
    assert "gpt-5.5" not in REASONING_MODELS


# ---------------------------------------------------------------------------
# _call_responses_api — responses endpoint extraction
# ---------------------------------------------------------------------------


def _make_responses_response(text: str):
    """Build a minimal mock matching the responses API output_text shape."""
    resp = MagicMock()
    resp.output_text = text
    return resp


def test_call_responses_api_returns_output_text():
    """_call_responses_api should return response.output_text."""
    client = MagicMock()
    client.responses.create.return_value = _make_responses_response("hello goblin")

    result = _call_responses_api(client, "gpt-5.5", "test prompt", system=None)

    assert result == "hello goblin"


def test_call_responses_api_passes_system_in_input():
    """System prompt should appear as first item in the input list."""
    client = MagicMock()
    client.responses.create.return_value = _make_responses_response("")

    _call_responses_api(client, "gpt-5.5", "user prompt", system="be nerdy")

    call_kwargs = client.responses.create.call_args.kwargs
    input_items = call_kwargs["input"]
    assert input_items[0] == {"role": "system", "content": "be nerdy"}
    assert input_items[1] == {"role": "user", "content": "user prompt"}


def test_call_responses_api_no_system_sends_one_item():
    """Without a system prompt, input should have only the user message."""
    client = MagicMock()
    client.responses.create.return_value = _make_responses_response("")

    _call_responses_api(client, "gpt-5.5", "user prompt", system=None)

    call_kwargs = client.responses.create.call_args.kwargs
    assert len(call_kwargs["input"]) == 1


def test_call_responses_api_fallback_on_missing_output_text():
    """If output_text is missing, fall back to scanning output items."""
    client = MagicMock()
    part = MagicMock()
    part.type = "output_text"
    part.text = "from output items"
    item = MagicMock()
    item.content = [part]
    resp = MagicMock(spec=[])  # no output_text attribute
    resp.output = [item]
    client.responses.create.return_value = resp

    result = _call_responses_api(client, "gpt-5.5", "p", system=None)
    assert result == "from output items"


# ---------------------------------------------------------------------------
# call_model — routing regression
# ---------------------------------------------------------------------------


def test_call_model_routes_gpt55_to_responses_api():
    """call_model must use the responses API for gpt-5.5, not chat.completions."""
    client = MagicMock()
    client.responses.create.return_value = _make_responses_response("hi")

    with patch("goblin.runner._call_responses_api", return_value="hi") as mock_resp:
        call_model(client, "gpt-5.5", "prompt", system=None)
        mock_resp.assert_called_once()
        client.chat.completions.create.assert_not_called()


def test_call_model_uses_chat_completions_for_standard_model():
    """call_model must use chat.completions for non-responses-API models."""
    client = MagicMock()
    msg = MagicMock()
    msg.content = "response text"
    choice = MagicMock()
    choice.message = msg
    client.chat.completions.create.return_value = MagicMock(choices=[choice])

    result = call_model(client, "gpt-4o", "prompt", system=None)

    client.chat.completions.create.assert_called_once()
    assert result == "response text"
