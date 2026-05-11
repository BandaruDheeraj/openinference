import unittest
from opentelemetry.trace import NonRecordingSpan
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span

class TestWrappers(unittest.TestCase):
    def test_finalize_step_span_with_non_recording_span(self):
        span = NonRecordingSpan()
        try:
            _finalize_step_span(span)  # Should not raise an error
        except Exception:
            self.fail("_finalize_step_span raised an exception with NonRecordingSpan")

if __name__ == '__main__':
    unittest.main()