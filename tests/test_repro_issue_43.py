"""Reproduces AttributeError: NonRecordingSpan has no .status."""
import sys
import types

from opentelemetry.trace import NonRecordingSpan, INVALID_SPAN_CONTEXT

SENTINEL = "REPRO_FAILURE_NONRECORDING_SPAN_STATUS"

# Import the function under test
from openinference.instrumentation.smolagents._wrappers import _finalize_step_span


def main():
    # Create a NonRecordingSpan (has no .status attribute)
    span = NonRecordingSpan(INVALID_SPAN_CONTEXT)
    
    # Create a mock step_log with the expected attributes
    step_log = types.SimpleNamespace(
        error=None,
        observations=None,
        action_output=None
    )
    
    try:
        # This should raise AttributeError when accessing span.status.status_code
        _finalize_step_span(span, step_log)
    except AttributeError as e:
        # Check if the error is about 'status' attribute
        if "status" in str(e).lower():
            print(SENTINEL, flush=True)
            sys.exit(1)
        # Re-raise if it's a different AttributeError
        raise
    except Exception as e:
        # Unexpected exception type
        print(f"Unexpected exception: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
    
    # If we reach here, the bug did not reproduce (function returned successfully)
    # This means the fix is in place
    print("Function completed without error - bug is fixed")
    sys.exit(0)


if __name__ == "__main__":
    main()
