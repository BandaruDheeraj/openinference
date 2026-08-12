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
import sys
import importlib
from unittest.mock import MagicMock

import pytest


def _get_processor_class():
    """Find the OpenInferenceSpanProcessor class from the openllmetry instrumentation."""
    # Try all known module paths
    module_paths = [
        "openinference.instrumentation.openllmetry._span_processor",
        "openinference.instrumentation.openllmetry.span_processor",
        "openinference.instrumentation.openllmetry._processor",
        "openinference.instrumentation.openllmetry",
    ]
    for path in module_paths:
        try:
            mod = importlib.import_module(path)
            if hasattr(mod, "OpenInferenceSpanProcessor"):
                return mod.OpenInferenceSpanProcessor
        except (ImportError, ModuleNotFoundError):
            continue

    # Walk submodules
    try:
        import pkgutil
        import openinference.instrumentation.openllmetry as pkg
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=pkg.__name__ + ".",
            onerror=lambda x: None,
        ):
            try:
                mod = importlib.import_module(modname)
                if hasattr(mod, "OpenInferenceSpanProcessor"):
                    return mod.OpenInferenceSpanProcessor
            except Exception:
                continue
    except Exception:
        pass

    return None


def _get_span_attributes():
    """Get SpanAttributes from opentelemetry-semantic-conventions-ai."""
    try:
        from opentelemetry.semconv_ai import SpanAttributes
        return SpanAttributes
    except ImportError:
        return None


def test_discover_modules():
    """Discover what modules are available in the openllmetry instrumentation package."""
    import openinference.instrumentation.openllmetry as pkg
    import pkgutil
    print(f"\nPackage path: {pkg.__path__}")
    print(f"Package file: {getattr(pkg, '__file__', 'N/A')}")

    mods = list(pkgutil.walk_packages(
        path=pkg.__path__,
        prefix=pkg.__name__ + ".",
        onerror=lambda x: None,
    ))
    print(f"\nSubmodules found:")
    for m in mods:
        print(f"  {m.name}")

    print(f"\nPackage attributes: {[a for a in dir(pkg) if not a.startswith('__')]}")

    cls = _get_processor_class()
    print(f"\nProcessor class found: {cls}")
    assert True


def test_tool_span_output_unwrapping():
    """Bug: tool span output.value should be the unwrapped output string,
    not the full Traceloop envelope JSON string.

    The buggy code sets output.value to the full envelope JSON
    '{"output": "result_value"}' instead of the bare string 'result_value'.
    """
    SpanAttributes = _get_span_attributes()
    if SpanAttributes is None:
        pytest.skip("opentelemetry-semantic-conventions-ai not available")

    ProcessorClass = _get_processor_class()
    if ProcessorClass is None:
        pytest.skip(
            "Could not find OpenInferenceSpanProcessor in "
            "openinference.instrumentation.openllmetry"
        )

    tool_input = json.dumps({"inputs": {"query": "hello", "count": 3}})
    tool_output = json.dumps({"output": "result_value"})
    tool_name = "my_search_tool"

    attrs = {
        SpanAttributes.TRACELOOP_SPAN_KIND: "tool",
        SpanAttributes.TRACELOOP_ENTITY_NAME: tool_name,
        SpanAttributes.TRACELOOP_ENTITY_INPUT: tool_input,
        SpanAttributes.TRACELOOP_ENTITY_OUTPUT: tool_output,
    }

    mock_span = MagicMock()
    mock_span._attributes = dict(attrs)
    mock_span.name = "test_span"

    processor = ProcessorClass()
    processor.on_end(mock_span)

    result = mock_span._attributes

    print("\nActual result attributes:")
    for k, v in result.items():
        print(f"  {k!r}: {v!r}")

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


def test_tool_span_input_unwrapping():
    """Bug: tool span input.value should be the unwrapped inputs dict.

    The buggy code sets input.value to the full envelope JSON
    '{"inputs": {"query": "hello", "count": 3}}' instead of
    the unwrapped '{"query": "hello", "count": 3}'.
    """
    SpanAttributes = _get_span_attributes()
    if SpanAttributes is None:
        pytest.skip("opentelemetry-semantic-conventions-ai not available")

    ProcessorClass = _get_processor_class()
    if ProcessorClass is None:
        pytest.skip(
            "Could not find OpenInferenceSpanProcessor in "
            "openinference.instrumentation.openllmetry"
        )

    tool_input = json.dumps({"inputs": {"query": "hello", "count": 3}})
    tool_output = json.dumps({"output": "result_value"})
    tool_name = "my_search_tool"

    attrs = {
        SpanAttributes.TRACELOOP_SPAN_KIND: "tool",
        SpanAttributes.TRACELOOP_ENTITY_NAME: tool_name,
        SpanAttributes.TRACELOOP_ENTITY_INPUT: tool_input,
        SpanAttributes.TRACELOOP_ENTITY_OUTPUT: tool_output,
    }

    mock_span = MagicMock()
    mock_span._attributes = dict(attrs)
    mock_span.name = "test_span"

    processor = ProcessorClass()
    processor.on_end(mock_span)

    result = mock_span._attributes

    input_value = result.get("input.value")
    print(f"\ninput.value = {input_value!r}")

    assert input_value is not None, "REPRO_BUG_SENTINEL: input.value not set at all"

    try:
        parsed = json.loads(input_value)
    except (json.JSONDecodeError, TypeError):
        parsed = input_value

    # This assertion should FAIL due to the bug:
    # The buggy code does not correctly unwrap the input envelope,
    # so input.value ends up being the full envelope JSON or something else.
    assert parsed == {"query": "hello", "count": 3}, (
        f"REPRO_BUG_SENTINEL: input.value should be unwrapped inputs dict "
        f'{{"query": "hello", "count": 3}}, got: {input_value!r}. '
        f"The bug is that the Traceloop input envelope is not correctly unwrapped."
    )
