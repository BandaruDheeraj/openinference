import unittest
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span
from opentelemetry.trace import NonRecordingSpan


class TestFinalizeStepSpan(unittest.TestCase):
    def test_non_recording_span(self):
        span = NonRecordingSpan()
        try:
            _finalize_step_span(span)
            self.assertTrue(True)  # No exception should be raised
        except Exception:
            self.fail("_finalize_step_span raised Exception unexpectedly!")


if __name__ == '__main__':
    unittest.main()
