from opentelemetry.trace import Span

class NonRecordingSpan:
    def __init__(self):
        pass

    def is_recording(self):
        return False

    def set_attribute(self, key, value):
        pass

    def add_event(self, name, attributes=None):
        pass

    def end(self):
        pass

class SmolagentsInstrumentor:
    def instrument(self):
        # Instrumentation logic here
        pass

    def _finalize_step_span(self, span):
        if not isinstance(span, Span):
            # Defensive check for NonRecordingSpan
            return
        if span.status.status_code != trace_api.StatusCode.ERROR:
            # Finalization logic here
            pass
