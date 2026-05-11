import unittest
from openinference.instrumentation.smolagents import _wrappers
from opentelemetry.trace import NonRecordingSpan


class TestSmolagents(unittest.TestCase):
    def test_finalize_step_span_non_recording(self):
        span = NonRecordingSpan()
        try:
            _wrappers._finalize_step_span(span)
            self.assertTrue(True)  # No exception means it passed
        except Exception:
            self.fail("_finalize_step_span raised Exception unexpectedly!")


if __name__ == '__main__':
    unittest.main()
