from __future__ import annotations

from typing import Any, Iterator, Tuple

from openinference.instrumentation.smolagents._wrappers import _flatten


class MutatingMapping(dict[str, Any]):
    def items(self) -> Iterator[Tuple[str, Any]]:  # type: ignore[override]
        iterator = super().items()
        mutated = False
        for item in iterator:
            if not mutated:
                # Simulate concurrent mutation from another execution path while
                # _flatten is iterating this mapping.
                self["late"] = 99
                mutated = True
            yield item


def test_flatten_tolerates_mapping_size_change_during_iteration() -> None:
    payload: dict[str, Any] = {
        "message": MutatingMapping({"foo": "bar", "nested": {"value": 1}}),
    }

    flattened = dict(_flatten(payload))

    assert flattened["message.foo"] == "bar"
    assert flattened["message.nested.value"] == 1
