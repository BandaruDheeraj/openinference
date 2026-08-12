import json
from unittest.mock import MagicMock

from openinference.instrumentation.openllmetry._span_processor import (
    OpenInferenceSpanProcessor,
    _map_generic_span,
)
from opentelemetry.semconv_ai import SpanAttributes
import openinference.semconv.trace as sc


def test_repro():
    # Simulate a tool span with Traceloop envelope format
    tool_input = json.dumps({"inputs": {"query": "hello", "count": 3}})
    tool_output = json.dumps({"output": "result_value"})
    tool_name = "my_search_tool"

    attrs = {
        SpanAttributes.TRACELOOP_SPAN_KIND: "tool",
        SpanAttributes.TRACELOOP_ENTITY_NAME: tool_name,
        SpanAttributes.TRACELOOP_ENTITY_INPUT: tool_input,
        SpanAttributes.TRACELOOP_ENTITY_OUTPUT: tool_output,
    }

    # Create a mock span
    mock_span = MagicMock()
    mock_span._attributes = dict(attrs)
    mock_span.name = "my_search_tool_span"

    processor = OpenInferenceSpanProcessor()
    processor.on_end(mock_span)

    result = mock_span._attributes

    # Verify tool.name is set
    assert sc.SpanAttributes.TOOL_NAME in result, (
        f"REPRO_BUG_SENTINEL: tool.name not set in mapped attributes. "
        f"Got keys: {list(result.keys())}"
    )
    assert result[sc.SpanAttributes.TOOL_NAME] == tool_name, (
        f"REPRO_BUG_SENTINEL: tool.name expected '{tool_name}', got '{result.get(sc.SpanAttributes.TOOL_NAME)}'"
    )

    # Verify tool.parameters is set (should be the unwrapped inputs dict)
    assert sc.SpanAttributes.TOOL_PARAMETERS in result, (
        f"REPRO_BUG_SENTINEL: tool.parameters not set in mapped attributes. "
        f"Got keys: {list(result.keys())}"
    )

    # Verify input.value is the unwrapped args, not the raw envelope
    input_value = result.get("input.value")
    assert input_value is not None, "REPRO_BUG_SENTINEL: input.value not set"
    parsed_input = json.loads(input_value)
    assert parsed_input == {"query": "hello", "count": 3}, (
        f"REPRO_BUG_SENTINEL: input.value should be unwrapped inputs dict, got: {input_value}"
    )

    # Verify output.value is the bare result, not the envelope
    output_value = result.get("output.value")
    assert output_value is not None, "REPRO_BUG_SENTINEL: output.value not set"
    assert output_value == "result_value", (
        f"REPRO_BUG_SENTINEL: output.value should be bare 'result_value', got: {output_value}"
    )