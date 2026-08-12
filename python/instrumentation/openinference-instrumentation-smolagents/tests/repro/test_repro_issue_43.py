"""
Regression test for issue #43:
AttributeError in _finalize_step_span when span is NonRecordingSpan.

The fix `if not span.is_recording(): return` at lines 246-247 of _wrappers.py
prevents AttributeError when span.status is accessed on a NonRecordingSpan.

This test lives in tests/repro/ (NOT under tests/openinference/instrumentation/smolagents/)
so the autouse=True `instrument` fixture from the existing conftest.py does NOT apply.
That means no TracerProvider is configured, and spans are NonRecordingSpan instances
with is_recording()=False — exactly the condition that triggered the bug.
"""

from opentelemetry.trace import INVALID_SPAN_CONTEXT, NonRecordingSpan

from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def test_finalize_step_span_with_non_recording_span() -> None:
    """
    _finalize_step_span must not raise AttributeError when given a NonRecordingSpan.

    NonRecordingSpan is what the OpenTelemetry API returns when no TracerProvider
    is configured (the no-op default). It has no .status attribute, so the original
    code `span.status.status_code` would raise AttributeError. The fix adds an early
    return guard: `if not span.is_recording(): return`.
    """
    # Create a NonRecordingSpan — what you get when no TracerProvider is configured.
    span = NonRecordingSpan(INVALID_SPAN_CONTEXT)

    # Verify the precondition: is_recording() must be False for this span type.
    assert not span.is_recording(), (
        "Precondition failed: NonRecordingSpan.is_recording() should return False"
    )

    # Create a minimal step_log with the attributes _finalize_step_span reads.
    class StepLog:
        observations = "some observation"
        error = None

    step_log = StepLog()

    # Without the fix, this raises:
    #   AttributeError: 'NonRecordingSpan' object has no attribute 'status'
    # With the fix (early return when not span.is_recording()), it must return cleanly.
    _finalize_step_span(span, step_log)
