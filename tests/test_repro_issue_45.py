#!/usr/bin/env python3
"""Reproduction for issue #45: smolagents tool calls fail with NonRecordingSpan."""

import sys

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

# Import the wrapper that has the bug
from openinference.instrumentation.smolagents._wrappers import _ToolCallWrapper


def main():
    # Create a NonRecordingSpan (no-op span)
    ctx = SpanContext(trace_id=0, span_id=0, is_remote=False, trace_flags=TraceFlags(0))
    nr_span = NonRecordingSpan(ctx)
    tracer = trace.get_tracer(__name__)

    # Create a fake tool that matches smolagents Tool interface
    class FakeTool:
        name = "echo"
        description = "echoes input"
        inputs = {"x": {"type": "string"}}
        output_type = "string"

        def forward(self, x):
            return x

        def __call__(self, x):
            return self.forward(x)

    # Create the wrapper and try to call it
    wrapper = _ToolCallWrapper(tracer=tracer)
    tool = FakeTool()

    try:
        # This should fail when the bug is present because the wrapper
        # calls span.set_status() on a NonRecordingSpan without checking is_recording()
        result = wrapper(tool, ("hello",), {})
        # If we get here, the bug is fixed
        print("OK_no_error", flush=True)
        sys.exit(0)
    except Exception as e:
        # Bug reproduced - the wrapper crashed
        print("REPRO_FAILURE_NONRECORDING_SPAN_STATUS", flush=True)
        raise


if __name__ == "__main__":
    main()
