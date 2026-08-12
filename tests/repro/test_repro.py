def test_repro():
    from opentelemetry.trace import NonRecordingSpan, INVALID_SPAN_CONTEXT
    from openinference.instrumentation.smolagents._wrappers import _finalize_step_span
    import inspect

    # Verify that NonRecordingSpan has no .status attribute (the root cause)
    span = NonRecordingSpan(INVALID_SPAN_CONTEXT)
    assert not span.is_recording(), "NonRecordingSpan should not be recording"
    assert not hasattr(span, 'status'), (
        "NonRecordingSpan should NOT have a .status attribute — "
        "if it does, the bug cannot be triggered this way"
    )

    # Check the source of _finalize_step_span to see if it guards against non-recording spans
    source = inspect.getsource(_finalize_step_span)
    has_guard = 'is_recording' in source

    # Create a mock step_log with observations and no error
    class MockStepLog:
        observations = "some output"
        error = None

    step_log = MockStepLog()

    # The bug: _finalize_step_span accesses span.status.status_code without checking
    # if the span is recording. On a NonRecordingSpan this raises AttributeError.
    # If the bug is present, this call raises AttributeError.
    # If the bug is fixed, this call succeeds.
    # We want the test to FAIL (reproduce the bug), so we assert the call raises.
    raised = False
    try:
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        raised = True
        # Bug is present - this is what we want to document
        print(f"Bug confirmed: AttributeError raised: {e}")

    # The test should FAIL if the bug is NOT present (i.e., no exception raised)
    # and PASS only when the bug IS present.
    # Since we want to REPRODUCE the bug, we assert the exception WAS raised.
    assert raised, (
        "REPRO_BUG_SENTINEL: _finalize_step_span did NOT raise AttributeError on "
        "NonRecordingSpan. Either the bug is already fixed or the code path changed. "
        f"has_guard={has_guard}, source snippet: {source[:500]}"
    )
