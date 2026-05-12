import sys
from unittest.mock import Mock

from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

# Import the function that has the bug
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def test_nonrecording_span_attribute_error():
    """Reproduce AttributeError when _finalize_step_span receives NonRecordingSpan."""
    
    # Create a NonRecordingSpan (has no .status attribute)
    span_context = SpanContext(
        trace_id=1,
        span_id=1,
        is_remote=False,
        trace_flags=TraceFlags(0x01),
    )
    span = NonRecordingSpan(span_context)
    
    # Create a mock step_log with observations
    step_log = Mock()
    step_log.observations = "test observation"
    step_log.error = None
    
    # This should trigger the AttributeError: 'NonRecordingSpan' object has no attribute 'status'
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        if "'NonRecordingSpan' object has no attribute 'status'" in str(e):
            print("REPRO_FAILURE_NONRECORDING_SPAN", flush=True)
            raise
        else:
            # Different AttributeError, re-raise
            raise
    else:
        # Bug did not fire - test should fail when bug is present
        sys.exit(0)


if __name__ == "__main__":
    test_nonrecording_span_attribute_error()
