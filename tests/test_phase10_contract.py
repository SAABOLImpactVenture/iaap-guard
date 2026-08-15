from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class Phase10ContractTests(unittest.TestCase):
    def test_github_app_contract_is_exactly_least_privilege(self):
        contract = json.loads((ROOT / "config/github-app-v0.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["visibility"], "public-installable")
        self.assertEqual(contract["checkName"], "IaaP Guard / Architecture")
        self.assertEqual(
            contract["repositoryPermissions"],
            {
                "metadata": "read",
                "contents": "read",
                "pull_requests": "read",
                "checks": "write",
            },
        )
        self.assertEqual(
            contract["events"],
            {
                "pull_request": ["opened", "synchronize", "reopened", "ready_for_review"],
                "check_run": ["rerequested"],
            },
        )
        self.assertTrue(contract["installationToken"]["scopeToTriggeringRepository"])
        self.assertEqual(
            contract["installationToken"]["permissions"],
            {"contents": "read", "pull_requests": "read", "checks": "write"},
        )
        self.assertFalse(contract["customerInfrastructureCredentialsRequired"])
        self.assertFalse(contract["personalAccessTokenRequired"])

    def test_lambda_template_has_public_webhook_but_narrow_aws_authority(self):
        text = (ROOT / "deploy/aws-lambda/template.yaml").read_text(encoding="utf-8")
        document = yaml.safe_load(text)
        self.assertEqual(document["Parameters"]["GitHubAppId"]["Type"], "Number")
        self.assertNotIn("GitHubAppClientId", document["Parameters"])

        function = document["Resources"]["GuardFunction"]["Properties"]
        self.assertEqual(function["Handler"], "lambda_function.lambda_handler")
        self.assertEqual(function["Runtime"], "python3.12")
        self.assertEqual(function["FunctionUrlConfig"]["AuthType"], "NONE")
        self.assertEqual(function["FunctionUrlConfig"]["InvokeMode"], "BUFFERED")
        self.assertEqual(
            function["ReservedConcurrentExecutions"],
            {
                "Fn::If": [
                    "GuardReservedConcurrencyIsEnabled",
                    {"Ref": "GuardReservedConcurrency"},
                    {"Ref": "AWS::NoValue"},
                ]
            },
        )

        concurrency = document["Parameters"]["GuardReservedConcurrency"]
        self.assertEqual(concurrency["Type"], "Number")
        self.assertEqual(concurrency["Default"], 5)
        self.assertEqual(concurrency["MinValue"], 0)

        concurrency_enabled = document["Parameters"]["GuardReservedConcurrencyEnabled"]
        self.assertEqual(concurrency_enabled["Type"], "String")
        self.assertEqual(concurrency_enabled["Default"], "true")
        self.assertEqual(concurrency_enabled["AllowedValues"], ["true", "false"])
        self.assertEqual(
            document["Conditions"]["GuardReservedConcurrencyIsEnabled"],
            {
                "Fn::Equals": [
                    {"Ref": "GuardReservedConcurrencyEnabled"},
                    "true",
                ]
            },
        )

        environment = function["Environment"]["Variables"]
        self.assertIn("IAAP_GUARD_GITHUB_APP_ID", environment)
        self.assertNotIn("IAAP_GUARD_GITHUB_CLIENT_ID", environment)
        self.assertIn("IAAP_GUARD_GITHUB_PRIVATE_KEY_SECRET_ARN", environment)
        self.assertIn("IAAP_GUARD_GITHUB_WEBHOOK_SECRET_ARN", environment)
        self.assertNotIn("IAAP_GUARD_GITHUB_PRIVATE_KEY", environment)
        self.assertNotIn("IAAP_GUARD_GITHUB_WEBHOOK_SECRET", environment)

        statements = function["Policies"][0]["Statement"]
        self.assertEqual(len(statements), 1)
        self.assertEqual(statements[0]["Effect"], "Allow")
        self.assertEqual(statements[0]["Action"], ["secretsmanager:GetSecretValue"])
        self.assertEqual(len(statements[0]["Resource"]), 2)
        self.assertNotIn("Resource: '*'", text)
        self.assertNotIn('Resource: "*"', text)

    def test_lambda_template_has_beta_operational_visibility(self):
        document = yaml.safe_load(
            (ROOT / "deploy/aws-lambda/template.yaml").read_text(encoding="utf-8")
        )
        resources = document["Resources"]

        log_group = resources["GuardFunctionLogGroup"]
        self.assertEqual(log_group["Type"], "AWS::Logs::LogGroup")
        self.assertEqual(
            log_group["Properties"],
            {
                "LogGroupName": {"Fn::Sub": "/aws/lambda/${GuardFunction}"},
                "RetentionInDays": 14,
            },
        )

        expected_alarms = {
            "GuardFunctionErrorsAlarm": ("Errors", "Sum", 1),
            "GuardFunctionThrottlesAlarm": ("Throttles", "Sum", 1),
            "GuardFunctionDurationAlarm": ("Duration", "Maximum", 50000),
        }
        for logical_id, (metric, statistic, threshold) in expected_alarms.items():
            alarm = resources[logical_id]
            self.assertEqual(alarm["Type"], "AWS::CloudWatch::Alarm")
            properties = alarm["Properties"]
            self.assertEqual(properties["Namespace"], "AWS/Lambda")
            self.assertEqual(properties["MetricName"], metric)
            self.assertEqual(
                properties["Dimensions"],
                [{"Name": "FunctionName", "Value": {"Ref": "GuardFunction"}}],
            )
            self.assertEqual(properties["Statistic"], statistic)
            self.assertEqual(properties["Period"], 60)
            self.assertEqual(properties["EvaluationPeriods"], 1)
            self.assertEqual(properties["Threshold"], threshold)
            self.assertEqual(
                properties["ComparisonOperator"],
                "GreaterThanOrEqualToThreshold",
            )
            self.assertEqual(properties["TreatMissingData"], "notBreaching")
            self.assertNotIn("AlarmActions", properties)
            self.assertNotIn("OKActions", properties)
            self.assertNotIn("InsufficientDataActions", properties)

    def test_oidc_workflow_has_read_only_beta_verification(self):
        text = (
            ROOT / ".github/workflows/deploy-aws-beta.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("- verify", text)
        self.assertIn("inputs.operation == 'verify'", text)
        self.assertIn("cloudformation get-template", text)
        self.assertIn("cloudformation describe-stack-resources", text)
        self.assertIn("scripts/verify_beta_stack.py", text)
        self.assertNotIn("secretsmanager get-secret-value", text.lower())
        self.assertNotIn("aws login", text.lower())

    def test_runtime_dependencies_are_pinned(self):
        requirements = (ROOT / "requirements-app.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            requirements,
            ["PyYAML==6.0.2", "PyJWT==2.13.0", "cryptography==50.0.0"],
        )

    def test_sam_builder_uses_runtime_dependency_entrypoint(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(requirements, ["-r requirements-app.txt"])


if __name__ == "__main__":
    unittest.main()
