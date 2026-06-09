import json
import types
from openinference.instrumentation.smolagents._wrappers import _RunWrapper
# No tracker base class found; using object

class _CaptureTracker(object):
    def __init__(self):
        self.error_calls = []
        self.end_calls = []
    def start_tool_span(self, name, input, id, parent=None): pass
    def end_tool_span(self, id, response): self.end_calls.append(response)
    def end_tool_span_with_error(self, id, error): self.error_calls.append(error)
    def end_all_in_flight(self): pass

def test_repro():
    tracker = _CaptureTracker()
    block = json.loads('{"type": "tool_result", "tool_use_id": "tu1", "is_error": true, "content": [{"type": "text", "text": "actual error text"}]}')
    msg = types.SimpleNamespace(content=[block])
    _RunWrapper(msg, tracker)
    assert tracker.error_calls, '_RunWrapper did not call end_tool_span_with_error'
    actual = tracker.error_calls[0]
    assert actual != "Tool execution error", (
        f'_RunWrapper BUG: end_tool_span_with_error received '
        f'"Tool execution error" (hardcoded) instead of actual content. Got: {actual!r}'
    )