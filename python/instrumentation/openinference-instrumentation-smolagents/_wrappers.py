from opentelemetry.trace import Span
from opentelemetry.trace import StatusCode

class SmolagentsInstrumentor:
    def instrument(self):
        # Instrumentation logic here
        pass

class NonRecordingSpan:
    def __init__(self):
        pass

    def finalize(self):
        # Defensive handling for NonRecordingSpan
        pass

    def get_status(self):
        return StatusCode.UNSET

    def is_recording(self):
        return False

    def set_status(self, status):
        # No-op for NonRecordingSpan
        pass

    def set_attribute(self, key, value):
        # No-op for NonRecordingSpan
        pass

    def add_event(self, name, attributes=None):
        # No-op for NonRecordingSpan
        pass

    def end(self):
        # No-op for NonRecordingSpan
        pass

    def __str__(self):
        return "NonRecordingSpan"

    def __repr__(self):
        return self.__str__()

# Example usage
span = NonRecordingSpan()
if not span.is_recording():
    print("Span is not recording, handling gracefully.")

    # New defensive handling for the case when span is not recording
    print("Span is dropped, no further action required.")
