from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml

from .classifier import classify
from .model import Artifact

SUPPORTED_SUFFIXES = {".yaml", ".yml", ".json", ".tf", ".tofu", ".hcl", ".md", ".py", ".sh"}
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "vendor", "dist", "build", "__pycache__", "artifacts", ".work"}
MAX_FILE_BYTES = 1_000_000


def iter_candidate_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in SUPPORTED_SUFFIXES:
            yield root
        return

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def _parse(path: Path, text: str) -> tuple[tuple[Any, ...], dict[str, Any]]:
    suffix = path.suffix.lower()
    documents: list[Any] = []
    fixture: dict[str, Any] = {}
    try:
        if suffix in {".yaml", ".yml"}:
            documents = [doc for doc in yaml.safe_load_all(text) if doc is not None]
            if documents and isinstance(documents[0], dict) and isinstance(documents[0].get("fixture"), dict):
                fixture = dict(documents[0]["fixture"])
                documents = documents[1:]
        elif suffix == ".json":
            document = json.loads(text)
            documents = [document]
            if isinstance(document, dict) and isinstance(document.get("fixture"), dict):
                fixture = dict(document["fixture"])
    except (yaml.YAMLError, json.JSONDecodeError):
        documents = []
    return tuple(documents), fixture


def load_artifacts(root: Path) -> list[Artifact]:
    root = root.resolve()
    base = root if root.is_dir() else root.parent
    # A single frozen fixture is intentionally evaluated as the context it
    # represents. During a normal directory/repository scan, fixture metadata
    # is never allowed to turn test data into live architecture.
    honor_fixture_context = root.is_file()
    artifacts: list[Artifact] = []
    for path in iter_candidate_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        documents, fixture = _parse(path, text)
        relative = path.relative_to(base).as_posix()
        contexts = classify(
            path,
            relative,
            documents,
            text,
            fixture if honor_fixture_context else {},
        )
        artifacts.append(
            Artifact(
                path=path,
                relative_path=relative,
                text=text,
                documents=documents,
                contexts=contexts,
                fixture=fixture,
            )
        )
    return artifacts
