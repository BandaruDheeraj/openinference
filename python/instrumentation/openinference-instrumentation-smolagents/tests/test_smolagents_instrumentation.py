import unittest
from opentelemetry.trace import NonRecordingSpan
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

class TestSmolagentsInstrumentor(unittest.TestCase):
    def test_non_recording_span(self):
        instrumentor = SmolagentsInstrumentor()
        span = NonRecordingSpan()
        # Ensure no exception is raised when finalizing a NonRecordingSpan
        instrumentor._finalize_step_span(span)

if __name__ == '__main__':
    unittest.main()
