import unittest
from python.instrumentation.openinference-instrumentation-smolagents._wrappers import NonRecordingSpan

class TestNonRecordingSpan(unittest.TestCase):
    def test_non_recording_span(self):
        span = NonRecordingSpan()
        self.assertFalse(span.is_recording())
        self.assertEqual(span.get_status(), 'UNSET')
        span.finalize()  # Should not raise any errors

if __name__ == '__main__':
    unittest.main()
