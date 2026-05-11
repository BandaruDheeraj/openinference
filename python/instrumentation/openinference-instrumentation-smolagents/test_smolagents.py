import unittest
from openinference.instrumentation.smolagents import SmolagentsInstrumentor, NonRecordingSpan

class TestSmolagentsInstrumentor(unittest.TestCase):
    def test_finalize_step_span_non_recording(self):
        instrumentor = SmolagentsInstrumentor()
        span = NonRecordingSpan()
        # This should not raise an error
        instrumentor._finalize_step_span(span)

if __name__ == '__main__':
    unittest.main()
