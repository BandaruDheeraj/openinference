import json

from openinference.instrumentation.openllmetry._span_processor import _map_generic_span


def test_repro() -> None:
    tool_input_envelope = json.dumps(
        {
            "input_str": "some string",
            "tags": ["tag1"],
            "metadata": {},
            "inputs": {"query": "what is 2+2?"},
            "kwargs": {},
        }
    )
    tool_output_envelope = json.dumps(
        {
            "output": "4",
            "kwargs": {},
        }
    )

    attrs = {
        "traceloop.span.kind": "tool",
        "traceloop.entity.name": "my_calculator_tool",
        "traceloop.entity.input": tool_input_envelope,
        "traceloop.entity.output": tool_output_envelope,
    }

    result = _map_generic_span(attrs)

    # 1. Check that tool.name is set
    assert "tool.name" in result, (
        "REPRO_BUG_SENTINEL: _map_generic_span() does not set 'tool.name' "
        f"for tool spans. Got keys: {list(result.keys())}"
    )
    assert result["tool.name"] == "my_calculator_tool", (
        "REPRO_BUG_SENTINEL: tool.name should be 'my_calculator_tool', "
        f"got {result.get('tool.name')}"
    )

    # 2. Check that input.value is unwrapped from the 'inputs' sub-dict
    assert "input.value" in result, (
        f"REPRO_BUG_SENTINEL: 'input.value' not found in result. Got: {result}"
    )
    input_val = result["input.value"]
    try:
        parsed_input = json.loads(input_val)
    except Exception:
        parsed_input = input_val
    assert parsed_input == {"query": "what is 2+2?"}, (
        f"REPRO_BUG_SENTINEL: input.value should be unwrapped 'inputs' sub-dict "
        f"{{'query': 'what is 2+2?'}}, but got: {input_val}"
    )

    # 3. Check that output.value is unwrapped from the 'output' key
    assert "output.value" in result, (
        f"REPRO_BUG_SENTINEL: 'output.value' not found in result. Got: {result}"
    )
    output_val = result["output.value"]
    assert output_val == "4", (
        f"REPRO_BUG_SENTINEL: output.value should be unwrapped 'output' field '4', "
        f"but got: {output_val}"
    )
