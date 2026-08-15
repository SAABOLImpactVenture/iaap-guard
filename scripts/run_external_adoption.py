#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from iaap_guard.scanner import scan_path

CAMPAIGN_VERSION = "external-adoption/v1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ECOSYSTEMS = {"aws", "azure", "gcp"}


def repository_slug(repository: str) -> str:
    return repository.replace("/", "__")


def load_campaign(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("campaign manifest must be a JSON object")
    if value.get("campaignVersion") != CAMPAIGN_VERSION:
        raise ValueError(f"campaignVersion must be {CAMPAIGN_VERSION!r}")

    repositories = value.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("repositories must be a non-empty array")

    seen_repositories: set[str] = set()
    seen_revisions: set[tuple[str, str]] = set()
    normalized: list[dict] = []
    for index, item in enumerate(repositories):
        if not isinstance(item, dict):
            raise ValueError(f"repositories[{index}] must be an object")
        repository = item.get("repository")
        revision = item.get("revision")
        ecosystem = item.get("ecosystem")
        source_url = item.get("sourceUrl")
        if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
            raise ValueError(f"repositories[{index}].repository must be owner/name")
        if not isinstance(revision, str) or not SHA_RE.fullmatch(revision):
            raise ValueError(f"repositories[{index}].revision must be a lowercase 40-character SHA")
        if ecosystem not in ECOSYSTEMS:
            raise ValueError(f"repositories[{index}].ecosystem must be one of {sorted(ECOSYSTEMS)}")
        expected_url = f"https://github.com/{repository}"
        if source_url != expected_url:
            raise ValueError(f"repositories[{index}].sourceUrl must be {expected_url!r}")
        if repository in seen_repositories:
            raise ValueError(f"duplicate repository: {repository}")
        identity = (repository, revision)
        if identity in seen_revisions:
            raise ValueError(f"duplicate repository revision: {repository}@{revision}")
        seen_repositories.add(repository)
        seen_revisions.add(identity)
        normalized.append(
            {
                "repository": repository,
                "revision": revision,
                "ecosystem": ecosystem,
                "sourceUrl": source_url,
            }
        )

    return {"campaignVersion": CAMPAIGN_VERSION, "repositories": normalized}


def run_campaign(manifest: dict, workspace: Path) -> dict:
    workspace = workspace.resolve()
    results: list[dict] = []
    for item in manifest["repositories"]:
        target = (workspace / repository_slug(item["repository"])).resolve()
        if workspace not in target.parents:
            raise ValueError(f"repository path escapes workspace: {target}")
        if not target.is_dir():
            raise FileNotFoundError(f"missing checked-out repository: {target}")

        scan_result = scan_path(
            target,
            repository=item["repository"],
            revision=item["revision"],
            ref=item["revision"],
        )
        findings = scan_result.get("findings", [])
        results.append(
            {
                **item,
                "conclusion": scan_result["conclusion"],
                "overallScore": scan_result["overallScore"],
                "findingCount": len(findings),
                "ruleIds": sorted({finding["ruleId"] for finding in findings}),
                "scanResult": scan_result,
            }
        )

    return {
        "campaignVersion": CAMPAIGN_VERSION,
        "repositoryCount": len(results),
        "ecosystems": sorted({item["ecosystem"] for item in results}),
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic, read-only IaaP Guard campaign over pinned external repositories"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    campaign = load_campaign(args.manifest)
    result = run_campaign(campaign, args.workspace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
