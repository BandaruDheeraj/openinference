"""Unit tests for helpers in `_wrappers.py` that don't need the full instrumentor.

Currently focused on `_extract_model_name_from_usage` (regression coverage for
issue #3136, where the helper returned the first dict key instead of the model
that actually did the bulk of the work in a multi-model run).
"""

from __future__ import annotations

import pytest

from openinference.instrumentation.claude_agent_sdk._wrappers import (
    _extract_model_name_from_usage,
)

# ---------------------------------------------------------------------------
# Mapping-shaped `modelUsage` — the case #3136 was about
# ---------------------------------------------------------------------------


def test_single_model_dict_returns_that_model() -> None:
    usage = {
        "claude-sonnet-4-6": {
            "outputTokens": 4,
            "inputTokens": 3,
            "costUSD": 0.008627,
        }
    }
    assert _extract_model_name_from_usage(usage) == "claude-sonnet-4-6"


def test_multi_model_dict_picks_max_output_tokens() -> None:
    # The fast/router model emits a tiny number of tokens; the main model does
    # the bulk of the generation. The span attribute should reflect the latter.
    usage = {
        "claude-haiku-4-5": {"outputTokens": 5, "inputTokens": 200},
        "claude-sonnet-4-6": {"outputTokens": 350, "inputTokens": 8},
    }
    assert _extract_model_name_from_usage(usage) == "claude-sonnet-4-6"


def test_multi_model_dict_picks_max_output_tokens_irrespective_of_dict_order() -> None:
    # Same shape, opposite insertion order — must still pick the heavy-output model.
    usage = {
        "claude-sonnet-4-6": {"outputTokens": 350, "inputTokens": 8},
        "claude-haiku-4-5": {"outputTokens": 5, "inputTokens": 200},
    }
    assert _extract_model_name_from_usage(usage) == "claude-sonnet-4-6"


def test_snake_case_output_tokens_also_accepted() -> None:
    # Some SDK shapes use snake_case; both should be treated as the same field.
    usage = {
        "claude-haiku-4-5": {"output_tokens": 5},
        "claude-sonnet-4-6": {"output_tokens": 400},
    }
    assert _extract_model_name_from_usage(usage) == "claude-sonnet-4-6"


def test_missing_output_tokens_falls_back_to_zero_weight() -> None:
    # If neither key has an outputTokens field, max() falls back to 0 weight for
    # every entry and the first key (by max-of-equals) is returned — but the
    # function must not crash.
    usage = {
        "model-a": {"inputTokens": 10},
        "model-b": {"inputTokens": 20},
    }
    # Either model is acceptable behavior; just assert no crash + a real name.
    result = _extract_model_name_from_usage(usage)
    assert result in ("model-a", "model-b")


def test_non_mapping_entry_value_does_not_crash() -> None:
    # Defensive: some SDK versions might pass a string or None alongside a dict.
    usage = {
        "model-a": "unexpected-string-value",
        "model-b": {"outputTokens": 99},
    }
    assert _extract_model_name_from_usage(usage) == "model-b"


def test_non_int_output_tokens_does_not_crash() -> None:
    usage = {
        "model-a": {"outputTokens": "not-a-number"},
        "model-b": {"outputTokens": 50},
    }
    assert _extract_model_name_from_usage(usage) == "model-b"


def test_empty_dict_returns_none() -> None:
    assert _extract_model_name_from_usage({}) is None


# ---------------------------------------------------------------------------
# Non-mapping shapes — must still work as before (regression for the
# list / object fallback branches the original function had)
# ---------------------------------------------------------------------------


def test_list_of_entries_returns_first_named() -> None:
    usage = [
        {"model": "claude-sonnet-4-6", "outputTokens": 10},
        {"model": "claude-haiku-4-5", "outputTokens": 200},
    ]
    # List branch keeps its original "first named entry" semantics — this PR
    # only changes the dict branch. Calling out the deliberate divergence.
    assert _extract_model_name_from_usage(usage) == "claude-sonnet-4-6"


def test_object_with_model_attribute() -> None:
    class FakeUsage:
        model = "claude-sonnet-4-6"

    assert _extract_model_name_from_usage(FakeUsage()) == "claude-sonnet-4-6"


def test_none_returns_none() -> None:
    assert _extract_model_name_from_usage(None) is None


@pytest.mark.parametrize("value", ["", 0, [], {}])
def test_falsy_inputs_return_none(value: object) -> None:
    assert _extract_model_name_from_usage(value) is None


# ---------------------------------------------------------------------------
# _update_tool_spans_from_messages — regression for issue #55
# (error content was discarded; hardcoded "Tool execution error" was used)
# ---------------------------------------------------------------------------


from openinference.instrumentation.claude_agent_sdk._wrappers import (  # noqa: E402
    _ToolSpanTrackerBase,
    _update_tool_spans_from_messages,
)


class _CapturingTracker(_ToolSpanTrackerBase):
    """Minimal tracker that records calls to end_tool_span_with_error."""

    def __init__(self) -> None:
        self.error_calls: list[tuple[object, object]] = []
        self.end_calls: list[tuple[object, object]] = []

    def start_tool_span(
        self,
        tool_name: object,
        tool_input: object,
        tool_use_id: object,
        parent_tool_use_id: object = None,
    ) -> None:
        pass

    def end_tool_span(self, tool_use_id: object, tool_response: object) -> None:
        self.end_calls.append((tool_use_id, tool_response))

    def end_tool_span_with_error(self, tool_use_id: object, error: object) -> None:
        self.error_calls.append((tool_use_id, error))

    def end_all_in_flight(self) -> None:
        pass


class _FakeBlock:
    """Attribute-based fake for a tool_result content block."""

    def __init__(
        self,
        tool_use_id: str,
        content: object,
        is_error: bool,
    ) -> None:
        self.type = "tool_result"
        self.tool_use_id = tool_use_id
        self.content = content
        self.is_error = is_error


class _FakeMessage:
    def __init__(self, blocks: list[object]) -> None:
        self.content = blocks


def test_update_tool_spans_passes_result_content_to_error_handler() -> None:
    """Regression test for issue #55.

    When a tool_result block has is_error=True, _update_tool_spans_from_messages
    must forward the actual result_content to end_tool_span_with_error instead of
    the old hardcoded "Tool execution error" string.
    """
    error_content = [{"type": "text", "text": "actual error text from tool"}]
    block = _FakeBlock(tool_use_id="tu-1", content=error_content, is_error=True)
    message = _FakeMessage(blocks=[block])

    tracker = _CapturingTracker()
    _update_tool_spans_from_messages(message, tracker)  # type: ignore[arg-type]

    assert tracker.error_calls, (
        "_update_tool_spans_from_messages did not call end_tool_span_with_error"
    )
    _tool_use_id, actual_error = tracker.error_calls[0]
    assert actual_error is error_content, (
        f"end_tool_span_with_error received {actual_error!r} instead of the actual "
        f"result_content {error_content!r}. The hardcoded 'Tool execution error' "
        f"string regression has re-appeared."
    )
    # Sanity-check: the non-error path must NOT call end_tool_span_with_error
    assert not tracker.end_calls, (
        "end_tool_span was unexpectedly called for an is_error=True block"
    )


def test_update_tool_spans_non_error_does_not_call_error_handler() -> None:
    """Complementary test: non-error tool_result must call end_tool_span, not the error variant."""
    ok_content = [{"type": "text", "text": "tool output"}]
    block = _FakeBlock(tool_use_id="tu-2", content=ok_content, is_error=False)
    message = _FakeMessage(blocks=[block])

    tracker = _CapturingTracker()
    _update_tool_spans_from_messages(message, tracker)  # type: ignore[arg-type]

    assert tracker.end_calls, (
        "_update_tool_spans_from_messages did not call end_tool_span for a non-error block"
    )
    assert not tracker.error_calls, (
        "end_tool_span_with_error was unexpectedly called for a non-error block"
    )
    _tool_use_id, actual_content = tracker.end_calls[0]
    assert actual_content is ok_content
