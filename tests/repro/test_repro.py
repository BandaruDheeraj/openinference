"""
Repro test for: AttributeError: 'NonRecordingSpan' object has no attribute 'status'
in _finalize_step_span when OTEL returns a NonRecordingSpan (e.g., no tracer provider
configured).

The fix adds `if not span.is_recording(): return` as the first statement in
_finalize_step_span, preventing the AttributeError.
"""
from unittest.mock import MagicMock

from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def make_non_recording_span() -> NonRecordingSpan:
    """Construct a dropped/invalid span exactly as OTEL produces when no provider is configured."""
    return NonRecordingSpan(
        SpanContext(
            trace_id=0,
            span_id=0,
            is_remote=False,
            trace_flags=TraceFlags(0),
        )
    )


def test_repro() -> None:
    """
    _finalize_step_span must NOT raise AttributeError when given a NonRecordingSpan.

    Before the fix, accessing span.status.status_code on a NonRecordingSpan raised:
        AttributeError: 'NonRecordingSpan' object has no attribute 'status'
    """
    span = make_non_recording_span()
    assert not span.is_recording(), "Precondition: span must be non-recording"

    step_log = MagicMock()
    step_log.observations = "some observations"
    step_log.error = None

    # This must not raise AttributeError
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        raise AssertionError(
            f"_finalize_step_span raised AttributeError on NonRecordingSpan: {e}"
        ) from e
