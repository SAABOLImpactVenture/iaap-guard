from __future__ import annotations

import argparse
import json
from pathlib import Path

from .planning import build_planning_report, render_planning_markdown
from .product import build_product_assessment, load_product_manifest, load_scan_results, render_product_markdown
from .product_planning import build_product_planning_report, render_product_planning_markdown
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


def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", type=Path)
    parser.add_argument("--repository")
    parser.add_argument("--revision", default="0" * 40)
    parser.add_argument("--ref")
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--output", type=Path)


def _add_product_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("manifest", type=Path, help="iaap-product/v1 YAML manifest")
    parser.add_argument("results", nargs="+", type=Path, help="member scan-result/v1 JSON files")
    parser.add_argument("--output", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Infrastructure-as-a-Product architecture guard")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan a repository, directory, or fixture")
    _add_scan_arguments(scan)
    scan.add_argument("--format", choices=("text", "json"), default="text")

    plan = subparsers.add_parser(
        "plan",
        help="scan a repository and generate an evidence-traceable OKR improvement plan",
    )
    _add_scan_arguments(plan)
    plan.add_argument("--planning-catalog", type=Path)
    plan.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_assess = subparsers.add_parser(
        "product-assess",
        help="aggregate registered repository scan evidence into one product assessment",
    )
    _add_product_arguments(product_assess)
    product_assess.add_argument("--format", choices=("markdown", "json"), default="markdown")

    product_plan = subparsers.add_parser(
        "product-plan",
        help="generate a product-level OKR improvement plan from registered repository evidence",
    )
    _add_product_arguments(product_plan)
    product_plan.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser


def _write_or_print(rendered: str, output: Path | None) -> None:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def main() -> int:
    args = build_parser().parse_args()

    if args.command in {"product-assess", "product-plan"}:
        manifest = load_product_manifest(args.manifest)
        results = load_scan_results(args.results)
        assessment = build_product_assessment(manifest, results)
        if args.command == "product-assess":
            rendered = (
                json.dumps(assessment, indent=2, sort_keys=False) + "\n"
                if args.format == "json"
                else render_product_markdown(assessment)
            )
        else:
            report = build_product_planning_report(assessment)
            rendered = (
                json.dumps(report, indent=2, sort_keys=False) + "\n"
                if args.format == "json"
                else render_product_planning_markdown(report)
            )
        _write_or_print(rendered, args.output)
        return 1 if assessment["conclusion"] in {"failure", "incomplete"} else 0

    result = scan_path(
        args.target,
        repository=args.repository,
        revision=args.revision,
        ref=args.ref,
        catalog_path=args.catalog,
    )

    if args.command == "scan":
        rendered = json.dumps(result, indent=2, sort_keys=False) + "\n" if args.format == "json" else render_text(result)
    else:
        report = build_planning_report(result, catalog_path=args.planning_catalog)
        rendered = (
            json.dumps(report, indent=2, sort_keys=False) + "\n"
            if args.format == "json"
            else render_planning_markdown(report)
        )

    _write_or_print(rendered, args.output)
    return 1 if result["conclusion"] == "failure" else 0


if __name__ == "__main__":
    raise SystemExit(main())
