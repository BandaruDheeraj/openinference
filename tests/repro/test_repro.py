import json
from openinference.instrumentation.openllmetry._span_processor import _map_generic_span


def test_repro():
    # Simulate a LangChain retriever span with traceloop.span.kind = "task"
    # and gen_ai.operation.name = "vector_db_retrieve"
    documents = [
        {"page_content": "Paris is the capital of France.", "metadata": {"source": "wiki"}},
        {"page_content": "The Eiffel Tower is in Paris.", "metadata": {"source": "wiki"}},
    ]
    attrs = {
        "traceloop.span.kind": "task",
        "gen_ai.operation.name": "vector_db_retrieve",
        "traceloop.entity.name": "retriever",
        "traceloop.entity.input": json.dumps({"query": "What is the capital of France?"}),
        "traceloop.entity.output": json.dumps({"documents": documents}),
    }

    result = _map_generic_span(attrs, span_name="retriever")

    # The bug: span kind is mapped to TOOL instead of RETRIEVER
    span_kind = result.get("openinference.span.kind")
    assert span_kind != "TOOL", (
        f"REPRO_BUG_SENTINEL: retriever span was incorrectly mapped to span kind '{span_kind}' "
        f"(expected 'RETRIEVER'). The _map_generic_span function has no retriever-aware branch "
        f"for gen_ai.operation.name='vector_db_retrieve', so it falls through to the TOOL mapping."
    )

    assert span_kind == "RETRIEVER", (
        f"REPRO_BUG_SENTINEL: expected openinference.span.kind='RETRIEVER' but got '{span_kind}'"
    )

    # Also verify that retrieval.documents attributes are produced
    doc_keys = [k for k in result if k.startswith("retrieval.documents")]
    assert len(doc_keys) > 0, (
        f"REPRO_BUG_SENTINEL: no 'retrieval.documents.*' attributes found in result. "
        f"Got keys: {list(result.keys())}. The retrieved documents are lost as raw JSON blob."
    )

    # Verify first document content is mapped
    assert "retrieval.documents.0.document.content" in result, (
        f"REPRO_BUG_SENTINEL: 'retrieval.documents.0.document.content' not found in result. "
        f"Got keys: {list(result.keys())}"
    )
    assert result["retrieval.documents.0.document.content"] == "Paris is the capital of France.", (
        f"REPRO_BUG_SENTINEL: unexpected document content: "
        f"{result.get('retrieval.documents.0.document.content')}"
    )