"""
Repro test for GitHub issue #62:
[bug][agno] _extract_output stringifies pydantic content instead of serializing to JSON

The bug: when a workflow/step response has a `content` attribute that is a Pydantic
BaseModel, _extract_output used to call str(response.content) which produces a Python
repr (e.g. "MyModel(field='value')") instead of proper JSON.

The fix: _content_to_str helper checks hasattr(content, 'model_dump_json') first and
calls content.model_dump_json() before falling back to str().
"""
import json
import types

from pydantic import BaseModel

from openinference.instrumentation.agno._workflow_wrapper import (
    _content_to_str,
    _extract_output,
)


class _MyContent(BaseModel):
    message: str
    value: int


def test_repro():
    """_extract_output must serialize Pydantic content as JSON, not Python repr."""
    content = _MyContent(message="hello", value=42)
    response = types.SimpleNamespace(content=content)

    result = _extract_output(response)

    # The result must be valid JSON
    parsed = json.loads(result)
    assert parsed == {"message": "hello", "value": 42}, (
        f"Expected JSON dict, got: {parsed!r}"
    )

    # The result must match model_dump_json() output
    expected_json = content.model_dump_json()
    assert result == expected_json, (
        f"_extract_output BUG: expected model_dump_json() output {expected_json!r}, "
        f"got {result!r}"
    )

    # The result must NOT be the Python repr (str(content))
    python_repr = str(content)
    assert result != python_repr, (
        f"_extract_output BUG: returned Python repr {python_repr!r} instead of JSON"
    )


def test_content_to_str_pydantic():
    """_content_to_str must use model_dump_json for Pydantic models."""
    content = _MyContent(message="world", value=99)
    result = _content_to_str(content)

    expected_json = content.model_dump_json()
    assert result == expected_json, (
        f"_content_to_str BUG: expected {expected_json!r}, got {result!r}"
    )


def test_content_to_str_plain_string():
    """_content_to_str must pass plain strings through unchanged."""
    result = _content_to_str("plain text")
    assert result == "plain text"


def test_extract_output_plain_string():
    """_extract_output must return plain string responses unchanged."""
    result = _extract_output("just a string")
    assert result == "just a string"


def test_extract_output_none():
    """_extract_output must return empty string for None."""
    result = _extract_output(None)
    assert result == ""
