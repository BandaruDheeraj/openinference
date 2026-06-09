"""
Regression test for Bug #43:
AttributeError in _finalize_step_span when span is NonRecordingSpan.

When no TracerProvider is configured, start_as_current_span returns a
NonRecordingSpan which has no .status attribute. The fix adds an early-return
guard: `if not span.is_recording(): return`.
"""
from unittest.mock import MagicMock

import pytest
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def make_non_recording_span() -> NonRecordingSpan:
    """Construct a dropped/invalid span as OTEL produces when no TracerProvider is configured."""
    return NonRecordingSpan(
        SpanContext(
            trace_id=0,
            span_id=0,
            is_remote=False,
            trace_flags=TraceFlags(0),
        )
    )


def test_finalize_step_span_with_non_recording_span_does_not_raise():
    """
    _finalize_step_span must not raise AttributeError when called with a NonRecordingSpan.
    This is the exact scenario from Bug #43: no TracerProvider configured.
    """
    span = make_non_recording_span()
    assert not span.is_recording(), "Precondition: span must be non-recording"

    step_log = MagicMock()
    step_log.observations = "Some observations"
    step_log.error = None

    # Must not raise AttributeError (span.status does not exist on NonRecordingSpan)
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        pytest.fail(
            f"Bug #43 regression: _finalize_step_span raised AttributeError on NonRecordingSpan: {e}"
        )


def test_finalize_step_span_with_non_recording_span_and_error_does_not_raise():
    """
    _finalize_step_span must not raise AttributeError even when step_log has an error.
    """
    span = make_non_recording_span()
    step_log = MagicMock()
    step_log.observations = None
    step_log.error = RuntimeError("Something went wrong")

    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        pytest.fail(
            f"Bug #43 regression: _finalize_step_span raised AttributeError on NonRecordingSpan: {e}"
        )
