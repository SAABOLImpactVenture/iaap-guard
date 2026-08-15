#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_RESOURCES = {
    "GuardFunction": "AWS::Lambda::Function",
    "GuardFunctionLogGroup": "AWS::Logs::LogGroup",
    "GuardFunctionErrorsAlarm": "AWS::CloudWatch::Alarm",
    "GuardFunctionThrottlesAlarm": "AWS::CloudWatch::Alarm",
    "GuardFunctionDurationAlarm": "AWS::CloudWatch::Alarm",
}

EXPECTED_ALARMS = {
    "GuardFunctionErrorsAlarm": ("Errors", "Sum", 1),
    "GuardFunctionThrottlesAlarm": ("Throttles", "Sum", 1),
    "GuardFunctionDurationAlarm": ("Duration", "Maximum", 50000),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_documents(
    stack_document: dict[str, Any],
    template_document: dict[str, Any],
    resources_document: dict[str, Any],
    health_document: dict[str, Any],
) -> list[str]:
    stacks = stack_document.get("Stacks") or []
    require(len(stacks) == 1, "expected exactly one deployed stack")
    stack = stacks[0]

    status = stack.get("StackStatus")
    require(
        status in {"CREATE_COMPLETE", "UPDATE_COMPLETE"},
        f"stack is not stable: {status}",
    )

    parameters = {
        item["ParameterKey"]: item.get("ParameterValue")
        for item in stack.get("Parameters") or []
    }
    require(parameters.get("GitHubAppId") == "4529329", "unexpected GitHub App ID")
    require(
        parameters.get("GuardReservedConcurrency") == "5",
        "unexpected reserved concurrency value",
    )
    require(
        parameters.get("GuardReservedConcurrencyEnabled") == "false",
        "deployed beta concurrency mode changed",
    )

    private_key_arn = parameters.get("GitHubPrivateKeySecretArn", "")
    webhook_secret_arn = parameters.get("GitHubWebhookSecretArn", "")
    require(
        private_key_arn.startswith("arn:aws:secretsmanager:"),
        "private-key secret reference is not an ARN",
    )
    require(
        webhook_secret_arn.startswith("arn:aws:secretsmanager:"),
        "webhook secret reference is not an ARN",
    )
    require(private_key_arn != webhook_secret_arn, "secret references must be distinct")

    outputs = {
        item["OutputKey"]: item.get("OutputValue")
        for item in stack.get("Outputs") or []
    }
    require(
        str(outputs.get("WebhookUrl", "")).startswith("https://"),
        "WebhookUrl output is missing or not HTTPS",
    )

    deployed = {
        item["LogicalResourceId"]: item
        for item in resources_document.get("StackResources") or []
    }
    for logical_id, resource_type in EXPECTED_RESOURCES.items():
        require(logical_id in deployed, f"missing deployed resource: {logical_id}")
        resource = deployed[logical_id]
        require(
            resource.get("ResourceType") == resource_type,
            f"{logical_id} has unexpected type",
        )
        require(
            resource.get("ResourceStatus") in {"CREATE_COMPLETE", "UPDATE_COMPLETE"},
            f"{logical_id} is not complete",
        )

    template = template_document.get("TemplateBody") or {}
    template_resources = template.get("Resources") or {}

    log_group = template_resources.get("GuardFunctionLogGroup") or {}
    require(
        log_group.get("Properties", {}).get("RetentionInDays") == 14,
        "deployed log retention is not 14 days",
    )

    for logical_id, (metric, statistic, threshold) in EXPECTED_ALARMS.items():
        alarm = template_resources.get(logical_id) or {}
        properties = alarm.get("Properties") or {}
        require(properties.get("Namespace") == "AWS/Lambda", f"{logical_id} namespace changed")
        require(properties.get("MetricName") == metric, f"{logical_id} metric changed")
        require(properties.get("Statistic") == statistic, f"{logical_id} statistic changed")
        require(properties.get("Threshold") == threshold, f"{logical_id} threshold changed")
        require(
            properties.get("TreatMissingData") == "notBreaching",
            f"{logical_id} missing-data behavior changed",
        )

    require(
        health_document == {"service": "iaap-guard", "status": "ok"},
        "public health response did not match the contract",
    )

    return [
        f"Stack status: {status}",
        "Required resources: 5/5 complete",
        "Managed log retention: 14 days",
        "CloudWatch alarms: Errors, Throttles, Duration",
        "Reserved concurrency parameter: 5",
        "Reserved concurrency application: disabled",
        "Secret references: 2 distinct ARNs; values not retrieved",
        "Public health contract: iaap-guard / ok",
    ]


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--resources", required=True)
    parser.add_argument("--health", required=True)
    args = parser.parse_args()

    try:
        lines = verify_documents(
            load(args.stack),
            load(args.template),
            load(args.resources),
            load(args.health),
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"beta operational verification failed: {exc}")
        return 1

    print("beta operational verification passed")
    for line in lines:
        print(f"- {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
