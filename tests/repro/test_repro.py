import json
from openinference.instrumentation.openllmetry._span_processor import _map_generic_span
import openinference.semconv.trace as sc


def test_repro():
    # Simulate a LangChain retriever span with traceloop.span.kind='task'
    # and gen_ai.operation.name='vector_db_retrieve'
    documents = [
        {"page_content": "Paris is the capital of France.", "metadata": {"source": "wiki"}, "score": 0.95},
        {"page_content": "The Eiffel Tower is in Paris.", "metadata": {}, "id": "doc2"},
    ]
    attrs = {
        "traceloop.span.kind": "task",
        "gen_ai.operation.name": "vector_db_retrieve",
        "gen_ai.task.input": json.dumps({"query": "What is the capital of France?"}),
        "gen_ai.task.output": json.dumps({"documents": documents}),
    }

    result = _map_generic_span(attrs, span_name="retriever_span")

    # The span kind must be RETRIEVER, not TOOL
    span_kind = result.get("openinference.span.kind")
    assert span_kind == sc.OpenInferenceSpanKindValues.RETRIEVER.value, (
        f"REPRO_BUG_SENTINEL: Expected span kind RETRIEVER but got {span_kind!r}. "
        "Retriever spans with gen_ai.operation.name='vector_db_retrieve' are being "
        "incorrectly mapped to TOOL instead of RETRIEVER."
    )

    # The first document's content must be present
    doc0_content_key = f"retrieval.documents.0.{sc.DocumentAttributes.DOCUMENT_CONTENT}"
    assert doc0_content_key in result, (
        f"REPRO_BUG_SENTINEL: Expected key {doc0_content_key!r} in mapped attributes but got keys: "
        f"{list(result.keys())}. Retrieval document content is missing from the mapped span."
    )

    assert result[doc0_content_key] == "Paris is the capital of France.", (
        f"REPRO_BUG_SENTINEL: Document content mismatch: {result[doc0_content_key]!r}"
    )

    # The second document's content must also be present
    doc1_content_key = f"retrieval.documents.1.{sc.DocumentAttributes.DOCUMENT_CONTENT}"
    assert doc1_content_key in result, (
        f"REPRO_BUG_SENTINEL: Expected key {doc1_content_key!r} missing from mapped attributes."
    )

    # Input value should be the query text
    assert result.get(sc.SpanAttributes.INPUT_VALUE) == "What is the capital of France?", (
        f"REPRO_BUG_SENTINEL: Expected input.value to be the query string, got: "
        f"{result.get(sc.SpanAttributes.INPUT_VALUE)!r}"
    )