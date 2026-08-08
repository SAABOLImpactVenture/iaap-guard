from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scanner import scan_path


def render_text(result: dict) -> str:
    lines = [
        "IaaP Guard",
        f"Repository: {result['repository']['name']}",
        f"Revision: {result['revision']['sha']}",
        f"Conclusion: {result['conclusion'].upper()}",
        f"Overall: {result['overallScore'] if result['overallScore'] is not None else 'N/A'}",
        "",
        "Dimensions:",
    ]
    for item in result["dimensionScores"]:
        score = "N/A" if item["score"] is None else str(item["score"])
        lines.append(f"  {item['dimension']}: {score} ({item['passed']}/{item['applicable']})")

    lines.extend(["", "Findings:"])
    if not result["findings"]:
        lines.append("  None")
    else:
        for finding in result["findings"]:
            location = finding["path"]
            if finding.get("line"):
                location += f":{finding['line']}"
            experimental = " [experimental]" if finding["experimental"] else ""
            lines.append(
                f"  {finding['result']} {finding['ruleId']}{experimental} {location} — {finding['evidence']}"
            )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Infrastructure-as-a-Product architecture guard")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="scan a repository, directory, or fixture")
    scan.add_argument("target", type=Path)
    scan.add_argument("--repository")
    scan.add_argument("--revision", default="0" * 40)
    scan.add_argument("--ref")
    scan.add_argument("--catalog", type=Path)
    scan.add_argument("--format", choices=("text", "json"), default="text")
    scan.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = scan_path(
        args.target,
        repository=args.repository,
        revision=args.revision,
        ref=args.ref,
        catalog_path=args.catalog,
    )
    rendered = json.dumps(result, indent=2, sort_keys=False) + "\n" if args.format == "json" else render_text(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if result["conclusion"] == "failure" else 0


if __name__ == "__main__":
    raise SystemExit(main())
