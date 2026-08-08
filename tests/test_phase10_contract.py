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
        function = document["Resources"]["GuardFunction"]["Properties"]
        self.assertEqual(function["Handler"], "lambda_function.lambda_handler")
        self.assertEqual(function["Runtime"], "python3.12")
        self.assertEqual(function["FunctionUrlConfig"]["AuthType"], "NONE")
        self.assertEqual(function["FunctionUrlConfig"]["InvokeMode"], "BUFFERED")

        environment = function["Environment"]["Variables"]
        self.assertIn("IAAP_GUARD_GITHUB_CLIENT_ID", environment)
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

    def test_runtime_dependencies_are_pinned(self):
        requirements = (ROOT / "requirements-app.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            requirements,
            ["PyYAML==6.0.2", "PyJWT==2.13.0", "cryptography==49.0.0"],
        )


if __name__ == "__main__":
    unittest.main()
