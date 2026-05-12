import unittest
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span

class TestFinalizeStepSpan(unittest.TestCase):
    def test_finalize_step_span_with_non_recording_span(self):
        span_context = SpanContext(
            trace_id=1,
            span_id=1,
            is_remote=False,
            trace_flags=TraceFlags(0x00)
        )
        non_recording_span = NonRecordingSpan(span_context)
        step_log = MockStepLog()
        try:
            _finalize_step_span(non_recording_span, step_log)
        except AttributeError:
            self.fail("_finalize_step_span raised AttributeError unexpectedly!")
        self.assertTrue(True)  # Ensure the test passes if no exception is raised

class MockStepLog:
    def __init__(self):
        self.observations = "test observation"
        self.error = None

if __name__ == '__main__':
    unittest.main()