"""Reproduce the bug where tool span input/output values are not correctly
unwrapped from the Traceloop envelope format.

The bug: when a tool span has TRACELOOP_ENTITY_INPUT like
  {"inputs": {"query": "hello", "count": 3}}
the instrumentation should set input.value to the unwrapped inputs dict
  {"query": "hello", "count": 3}
but instead it sets it to the full envelope string or the raw value.

Similarly for output: TRACELOOP_ENTITY_OUTPUT like
  {"output": "result_value"}
should produce output.value = "result_value" (bare string),
but the bug causes it to be the full envelope or wrong value.
"""
import json
import inspect
from unittest.mock import MagicMock, patch

from opentelemetry.semconv_ai import SpanAttributes
import openinference.semconv.trace as sc


def _get_mapped_attributes(attrs: dict) -> dict:
    """Run the span through the processor and return the resulting attributes."""
    from openinference.instrumentation.openllmetry._span_processor import (
        OpenInferenceSpanProcessor,
    )

    mock_span = MagicMock()
    mock_span._attributes = dict(attrs)
    mock_span.name = "test_span"

    processor = OpenInferenceSpanProcessor()
    processor.on_end(mock_span)

    return mock_span._attributes


def test_tool_span_input_unwrapping():
    """Bug: tool span input.value should be the unwrapped inputs dict,
    not the full Traceloop envelope JSON string."""
    tool_input = json.dumps({"inputs": {"query": "hello", "count": 3}})
    tool_output = json.dumps({"output": "result_value"})
    tool_name = "my_search_tool"

    attrs = {
        SpanAttributes.TRACELOOP_SPAN_KIND: "tool",
        SpanAttributes.TRACELOOP_ENTITY_NAME: tool_name,
        SpanAttributes.TRACELOOP_ENTITY_INPUT: tool_input,
        SpanAttributes.TRACELOOP_ENTITY_OUTPUT: tool_output,
    }

    result = _get_mapped_attributes(attrs)

    # Print what we actually got for debugging
    print("\nActual result attributes:")
    for k, v in result.items():
        print(f"  {k!r}: {v!r}")

    # The bug: output.value should be the bare string "result_value",
    # not the full envelope JSON or something else.
    output_value = result.get("output.value")
    print(f"\noutput.value = {output_value!r}")
    print(f"Expected: 'result_value'")

    # This assertion should FAIL due to the bug:
    # The buggy code does not correctly unwrap the output envelope,
    # so output.value ends up being the full JSON string or None.
    assert output_value == "result_value", (
        f"REPRO_BUG_SENTINEL: output.value should be bare 'result_value', "
        f"got: {output_value!r}. "
        f"The bug is that the Traceloop output envelope is not correctly unwrapped."
    )


def test_tool_span_input_value_unwrapping():
    """Bug: tool span input.value should be the unwrapped inputs dict."""
    tool_input = json.dumps({"inputs": {"query": "hello", "count": 3}})
    tool_output = json.dumps({"output": "result_value"})
    tool_name = "my_search_tool"

    attrs = {
        SpanAttributes.TRACELOOP_SPAN_KIND: "tool",
        SpanAttributes.TRACELOOP_ENTITY_NAME: tool_name,
        SpanAttributes.TRACELOOP_ENTITY_INPUT: tool_input,
        SpanAttributes.TRACELOOP_ENTITY_OUTPUT: tool_output,
    }

    result = _get_mapped_attributes(attrs)

    input_value = result.get("input.value")
    print(f"\ninput.value = {input_value!r}")

    # The bug: input.value should be the unwrapped inputs dict as JSON,
    # i.e. '{"query": "hello", "count": 3}'
    # but the buggy code may set it to the full envelope or something else.
    assert input_value is not None, "REPRO_BUG_SENTINEL: input.value not set"

    try:
        parsed = json.loads(input_value)
    except (json.JSONDecodeError, TypeError):
        parsed = input_value

    assert parsed == {"query": "hello", "count": 3}, (
        f"REPRO_BUG_SENTINEL: input.value should be unwrapped inputs dict "
        f"{{\"query\": \"hello\", \"count\": 3}}, got: {input_value!r}. "
        f"The bug is that the Traceloop input envelope is not correctly unwrapped."
    )


def test_inspect_map_generic_span_source():
    """Inspect the actual source of _map_generic_span to understand the bug."""
    try:
        from openinference.instrumentation.openllmetry._span_processor import (
            _map_generic_span,
        )
        src = inspect.getsource(_map_generic_span)
        print("\n_map_generic_span source:")
        print(src)
    except (ImportError, TypeError) as e:
        print(f"Could not inspect: {e}")

    # Also inspect the processor
    try:
        from openinference.instrumentation.openllmetry._span_processor import (
            OpenInferenceSpanProcessor,
        )
        src = inspect.getsource(OpenInferenceSpanProcessor)
        print("\nOpenInferenceSpanProcessor source:")
        print(src)
    except (ImportError, TypeError) as e:
        print(f"Could not inspect processor: {e}")

    # This test always passes — it's just for debugging
    assert True
