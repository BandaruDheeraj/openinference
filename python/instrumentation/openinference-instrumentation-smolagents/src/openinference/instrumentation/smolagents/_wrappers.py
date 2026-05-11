from opentelemetry.trace import NonRecordingSpan


def _finalize_step_span(span):
    # Early return if the span is not recording
    if isinstance(span, NonRecordingSpan):
        return
    
    if span.status.status_code != trace_api.StatusCode.ERROR:
        # Existing logic for handling recording spans
        pass
    # Additional logic for finalizing the span
