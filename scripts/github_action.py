from __future__ import annotations

import json
import os
from pathlib import Path

from iaap_guard.scanner import scan_path


def _within_workspace(workspace: Path, requested: str) -> Path:
    path = (workspace / requested).resolve()
    if not path.is_relative_to(workspace):
        raise ValueError(f"path escapes GITHUB_WORKSPACE: {requested}")
    return path


def _write_output(name: str, value: str) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def _summary(result: dict) -> str:
    lines = [
        "## IaaP Guard",
        "",
        f"**Repository:** `{result['repository']['name']}`  ",
        f"**Revision:** `{result['revision']['sha']}`  ",
        f"**Conclusion:** **{result['conclusion'].upper()}**  ",
        f"**Overall score:** **{result['overallScore'] if result['overallScore'] is not None else 'N/A'}**",
        "",
        "| Dimension | Score | Evidence |",
        "| --- | ---: | ---: |",
    ]
    for item in result["dimensionScores"]:
        score = "N/A" if item["score"] is None else str(item["score"])
        lines.append(f"| {item['dimension']} | {score} | {item['passed']}/{item['applicable']} |")

    lines.extend(["", "### Findings", ""])
    if not result["findings"]:
        lines.append("No WARNING or FAIL findings.")
    else:
        for finding in result["findings"]:
            location = finding["path"]
            if finding.get("line"):
                location += f":{finding['line']}"
            experimental = " · experimental" if finding["experimental"] else ""
            lines.append(
                f"- **{finding['result']} {finding['ruleId']}**{experimental} — `{location}` — {finding['evidence']}"
            )
    lines.extend(
        [
            "",
            f"Ruleset: `{result['ruleCatalogVersion']}` · Scoring: `{result['scoringModelVersion']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    target = _within_workspace(workspace, os.environ.get("IAAP_GUARD_TARGET", "."))
    output = _within_workspace(workspace, os.environ.get("IAAP_GUARD_OUTPUT", "artifacts/iaap-guard/scan-result.json"))

    repository = os.environ.get("GITHUB_REPOSITORY") or workspace.name
    revision = os.environ.get("GITHUB_SHA", "")
    ref = os.environ.get("GITHUB_REF")

    result = scan_path(target, repository=repository, revision=revision, ref=ref)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    relative_output = output.relative_to(workspace).as_posix()
    _write_output("conclusion", result["conclusion"])
    _write_output("score", "" if result["overallScore"] is None else str(result["overallScore"]))
    _write_output("result-path", relative_output)
    _write_output("findings", str(len(result["findings"])))

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(_summary(result))

    print(
        f"IaaP Guard: conclusion={result['conclusion']} score={result['overallScore']} "
        f"findings={len(result['findings'])} result={relative_output}"
    )

    fail_on_failure = os.environ.get("IAAP_GUARD_FAIL_ON_FAILURE", "false").strip().lower() in {"1", "true", "yes"}
    return 1 if fail_on_failure and result["conclusion"] == "failure" else 0


if __name__ == "__main__":
    raise SystemExit(main())
