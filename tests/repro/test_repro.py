import pytest
from opentelemetry.trace import NonRecordingSpan, INVALID_SPAN_CONTEXT
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def test_repro():
    # Create a NonRecordingSpan (what you get when no TracerProvider is configured)
    span = NonRecordingSpan(INVALID_SPAN_CONTEXT)
    
    # Verify precondition: is_recording() returns False for NonRecordingSpan
    assert not span.is_recording(), "Precondition: NonRecordingSpan.is_recording() should be False"
    
    # Create a mock step_log with observations and no error
    class MockStepLog:
        observations = "some observation"
        error = None
    
    step_log = MockStepLog()
    
    # The bug: _finalize_step_span accesses span.status.status_code unconditionally
    # on a NonRecordingSpan which has no .status attribute, causing AttributeError.
    # With the fix (early return when not span.is_recording()), this should not raise.
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        raise AssertionError(
            f"REPRO_BUG_SENTINEL: _finalize_step_span raised AttributeError on NonRecordingSpan "
            f"because it accessed span.status.status_code without checking is_recording() first. "
            f"Error: {e}"
        )