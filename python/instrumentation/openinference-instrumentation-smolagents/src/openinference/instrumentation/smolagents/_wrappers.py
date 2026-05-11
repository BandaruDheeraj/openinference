from opentelemetry.trace import NonRecordingSpan

# Other imports...

def _finalize_step_span(span):
    # Guard against NonRecordingSpan
    if isinstance(span, NonRecordingSpan):
        return
    if span.status.status_code != trace_api.StatusCode.ERROR:  # type: ignore[attr-defined]
        # Existing logic...
