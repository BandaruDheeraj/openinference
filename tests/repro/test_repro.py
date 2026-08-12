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
import pkgutil


def _find_span_processor_module():
    """Try to find the span processor module in the openinference.instrumentation.openllmetry package."""
    candidates = [
        "openinference.instrumentation.openllmetry._span_processor",
        "openinference.instrumentation.openllmetry.span_processor",
        "openinference.instrumentation.openllmetry._processor",
        "openinference.instrumentation.openllmetry",
    ]
    for candidate in candidates:
        try:
            mod = importlib.import_module(candidate)
            return mod
        except ImportError:
            continue
    return None


def _find_processor_class():
    """Find the OpenInferenceSpanProcessor class."""
    # Try direct import first
    try:
        from openinference.instrumentation.openllmetry._span_processor import (
            OpenInferenceSpanProcessor,
        )
        return OpenInferenceSpanProcessor
    except ImportError:
        pass

    # Try the package itself
    try:
        import openinference.instrumentation.openllmetry as pkg
        if hasattr(pkg, 'OpenInferenceSpanProcessor'):
            return pkg.OpenInferenceSpanProcessor
    except ImportError:
        pass

    # Walk submodules
    try:
        import openinference.instrumentation.openllmetry as pkg
        import pkgutil
        for importer, modname, ispkg in pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=pkg.__name__ + '.',
            onerror=lambda x: None
        ):
            try:
                mod = importlib.import_module(modname)
                if hasattr(mod, 'OpenInferenceSpanProcessor'):
                    return mod.OpenInferenceSpanProcessor
            except Exception:
                continue
    except Exception:
        pass

    return None


def test_discover_modules():
    """Discover what modules are available in the openllmetry instrumentation package."""
    import openinference.instrumentation.openllmetry as pkg
    print(f"\nPackage path: {pkg.__path__}")
    print(f"Package file: {getattr(pkg, '__file__', 'N/A')}")

    try:
        import pkgutil
        mods = list(pkgutil.walk_packages(
            path=pkg.__path__,
            prefix=pkg.__name__ + '.',
            onerror=lambda x: None
        ))
        print(f"\nSubmodules found:")
        for m in mods:
            print(f"  {m.name}")
    except Exception as e:
        print(f"Error walking packages: {e}")

    # List all attributes of the package
    print(f"\nPackage attributes: {[a for a in dir(pkg) if not a.startswith('__')]}")
    assert True


def test_tool_span_input_unwrapping():
    """Bug: tool span input.value should be the unwrapped inputs dict,
    not the full Traceloop envelope JSON string."""
    from unittest.mock import MagicMock

    ProcessorClass = _find_processor_class()
    assert ProcessorClass is not None, (
        "Could not find OpenInferenceSpanProcessor in any submodule of "
        "openinference.instrumentation.openllmetry"
    )

    try:
        from opentelemetry.semconv_ai import SpanAttributes
    except ImportError:
        import pytest
        pytest.skip("opentelemetry-semantic-conventions-ai not available")

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
    from unittest.mock import MagicMock

    ProcessorClass = _find_processor_class()
    assert ProcessorClass is not None, (
        "Could not find OpenInferenceSpanProcessor in any submodule of "
        "openinference.instrumentation.openllmetry"
    )

    try:
        from opentelemetry.semconv_ai import SpanAttributes
    except ImportError:
        import pytest
        pytest.skip("opentelemetry-semantic-conventions-ai not available")

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
        f'{{"query": "hello", "count": 3}}, got: {input_value!r}. '
        f"The bug is that the Traceloop input envelope is not correctly unwrapped."
    )
