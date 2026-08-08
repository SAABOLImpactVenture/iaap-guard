from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONTEXT_ORDER = (
    "consumer-contract",
    "experience",
    "ai-authority",
    "control-plane-implementation",
    "bootstrap",
    "evidence",
    "documentation-fixture",
    "unknown",
)


@dataclass(frozen=True)
class Artifact:
    path: Path
    relative_path: str
    text: str
    documents: tuple[Any, ...]
    contexts: tuple[str, ...]
    fixture: dict[str, Any] = field(default_factory=dict)

    def has_context(self, context: str) -> bool:
        return context in self.contexts


@dataclass(frozen=True)
class Violation:
    artifact: Artifact
    evidence: str
    line: int | None = None
    context: str | None = None
