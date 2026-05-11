from opentelemetry.trace import NonRecordingSpan


def _finalize_step_span(span):
    if isinstance(span, NonRecordingSpan):
        return
    if span.status.status_code != trace_api.StatusCode.ERROR:
        # ... existing logic unchanged
