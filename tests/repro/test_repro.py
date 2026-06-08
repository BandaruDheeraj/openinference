import json
import types
import pytest


def test_repro():
    try:
        from openinference.instrumentation.claude_agent_sdk._wrappers import (
            _update_tool_spans_from_messages,
        )
    except ImportError as e:
        pytest.skip(f"Could not import _update_tool_spans_from_messages: {e}")

    # Try to find or create a minimal tracker
    try:
        from openinference.instrumentation.claude_agent_sdk._wrappers import _ToolSpanTrackerBase

        class _CaptureTracker(_ToolSpanTrackerBase):
            def __init__(self):
                self.error_calls = []
                self.end_calls = []

            def start_tool_span(self, name, input, id, parent=None):
                pass

            def end_tool_span(self, id, response):
                self.end_calls.append(response)

            def end_tool_span_with_error(self, id, error):
                self.error_calls.append(error)

            def end_all_in_flight(self):
                pass

    except ImportError:
        # Fallback: create a plain tracker without base class
        class _CaptureTracker:
            def __init__(self):
                self.error_calls = []
                self.end_calls = []

            def start_tool_span(self, name, input, id, parent=None):
                pass

            def end_tool_span(self, id, response):
                self.end_calls.append(response)

            def end_tool_span_with_error(self, id, error):
                self.error_calls.append(error)

            def end_all_in_flight(self):
                pass

    tracker = _CaptureTracker()
    block = {
        "type": "tool_result",
        "tool_use_id": "tu1",
        "is_error": True,
        "content": [{"type": "text", "text": "actual error text"}],
    }
    msg = types.SimpleNamespace(content=[block])
    _update_tool_spans_from_messages(msg, tracker)
    assert tracker.error_calls, "_update_tool_spans_from_messages did not call end_tool_span_with_error"
    actual = tracker.error_calls[0]
    assert actual != "Tool execution error", (
        f"_update_tool_spans_from_messages BUG: end_tool_span_with_error received "
        f'"Tool execution error" (hardcoded) instead of actual content. Got: {actual!r}'
    )
