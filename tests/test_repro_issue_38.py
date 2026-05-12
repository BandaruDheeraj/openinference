#!/usr/bin/env python3
"""Reproduces issue #38: AttributeError in _finalize_step_span with NonRecordingSpan."""

import sys
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


class MockStepLog:
    """Mock step log object with observations attribute."""
    def __init__(self):
        self.observations = "test observation"
        self.error = None


def main():
    # Create a NonRecordingSpan (simulates no active tracer/processor)
    span_context = SpanContext(
        trace_id=1,
        span_id=1,
        is_remote=False,
        trace_flags=TraceFlags(0x00)
    )
    non_recording_span = NonRecordingSpan(span_context)
    
    # Create a mock step log
    step_log = MockStepLog()
    
    # This should trigger the AttributeError when accessing span.status
    try:
        _finalize_step_span(non_recording_span, step_log)
    except AttributeError as e:
        if "NonRecordingSpan" in str(e) and "status" in str(e):
            print("REPRO_FAILURE_NONRECORDING_SPAN_STATUS", flush=True)
            raise
        else:
            # Different AttributeError - not the bug we're looking for
            raise
    else:
        # Bug did not fire - function completed without error
        sys.exit(0)


if __name__ == "__main__":
    main()
