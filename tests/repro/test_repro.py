def test_repro():
    """
    Regression test for issue #43: AttributeError in smolagents _finalize_step_span
    when NonRecordingSpan has no .status attribute.

    The fix adds `if not span.is_recording(): return` at the top of _finalize_step_span.
    This test verifies the fix is in place and working correctly.
    """
    from opentelemetry.trace import NonRecordingSpan, INVALID_SPAN_CONTEXT
    from openinference.instrumentation.smolagents._wrappers import _finalize_step_span

    # Create a NonRecordingSpan (what you get when no TracerProvider is configured)
    span = NonRecordingSpan(INVALID_SPAN_CONTEXT)

    # Verify it's not recording
    assert not span.is_recording(), "NonRecordingSpan should not be recording"

    # Create a mock step_log with observations and no error
    class MockStepLog:
        observations = "some output"
        error = None

    step_log = MockStepLog()

    # The bug: accessing span.status.status_code on a NonRecordingSpan raises AttributeError
    # because NonRecordingSpan has no .status attribute.
    # The fix adds `if not span.is_recording(): return` at the top of _finalize_step_span.
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        raise AssertionError(
            f"REPRO_BUG_SENTINEL: _finalize_step_span raised AttributeError on NonRecordingSpan: {e}"
        )
