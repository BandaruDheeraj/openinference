#!/usr/bin/env python3
"""Reproduces issue #23: AttributeError in _finalize_step_span with NonRecordingSpan."""
import sys
from unittest.mock import Mock

from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def main():
    """Trigger the bug: _finalize_step_span tries to access .status on NonRecordingSpan."""
    # Create a NonRecordingSpan (has no .status attribute)
    span_context = SpanContext(
        trace_id=1,
        span_id=1,
        is_remote=False,
        trace_flags=TraceFlags(0x00),
    )
    non_recording_span = NonRecordingSpan(span_context)

    # Create a mock step_log with observations
    step_log = Mock()
    step_log.observations = "test observation"
    step_log.error = None

    # This should raise AttributeError when trying to access span.status
    try:
        _finalize_step_span(non_recording_span, step_log)
    except AttributeError as e:
        # Verify it's the specific bug we're testing
        if "NonRecordingSpan" in str(e) and "status" in str(e):
            print("REPRO_FAILURE_NONRECORDING_SPAN_STATUS", flush=True)
            raise
        else:
            # Different AttributeError - not the bug we're looking for
            sys.exit(0)
    else:
        # Bug did not fire - function completed without error
        sys.exit(0)


if __name__ == "__main__":
    main()
