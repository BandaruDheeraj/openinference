from opentelemetry.trace import NonRecordingSpan

class SmolagentsInstrumentor:
    # ... existing code ...

    def _finalize_step_span(self, span):
        # Guard against NonRecordingSpan
        if isinstance(span, NonRecordingSpan):
            return
        if span.status.status_code != trace_api.StatusCode.ERROR:  # type: ignore[attr-defined]
            # ... existing logic ...
