from __future__ import annotations

import unittest

from scripts.verify_beta_stack import verify_documents


class Phase16BetaVerificationTests(unittest.TestCase):
    def setUp(self):
        self.stack = {
            "Stacks": [
                {
                    "StackStatus": "UPDATE_COMPLETE",
                    "Parameters": [
                        {"ParameterKey": "GitHubAppId", "ParameterValue": "4529329"},
                        {"ParameterKey": "GuardReservedConcurrency", "ParameterValue": "5"},
                        {
                            "ParameterKey": "GuardReservedConcurrencyEnabled",
                            "ParameterValue": "false",
                        },
                        {
                            "ParameterKey": "GitHubPrivateKeySecretArn",
                            "ParameterValue": "arn:aws:secretsmanager:x:key",
                        },
                        {
                            "ParameterKey": "GitHubWebhookSecretArn",
                            "ParameterValue": "arn:aws:secretsmanager:x:webhook",
                        },
                    ],
                    "Outputs": [
                        {
                            "OutputKey": "WebhookUrl",
                            "OutputValue": "https://example.invalid/",
                        }
                    ],
                }
            ]
        }
        self.resources = {
            "StackResources": [
                {
                    "LogicalResourceId": "GuardFunction",
                    "ResourceType": "AWS::Lambda::Function",
                    "ResourceStatus": "UPDATE_COMPLETE",
                },
                {
                    "LogicalResourceId": "GuardFunctionLogGroup",
                    "ResourceType": "AWS::Logs::LogGroup",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
                {
                    "LogicalResourceId": "GuardFunctionErrorsAlarm",
                    "ResourceType": "AWS::CloudWatch::Alarm",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
                {
                    "LogicalResourceId": "GuardFunctionThrottlesAlarm",
                    "ResourceType": "AWS::CloudWatch::Alarm",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
                {
                    "LogicalResourceId": "GuardFunctionDurationAlarm",
                    "ResourceType": "AWS::CloudWatch::Alarm",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
            ]
        }
        self.template = {
            "TemplateBody": {
                "Resources": {
                    "GuardFunctionLogGroup": {
                        "Properties": {"RetentionInDays": 14}
                    },
                    "GuardFunctionErrorsAlarm": {
                        "Properties": {
                            "Namespace": "AWS/Lambda",
                            "MetricName": "Errors",
                            "Statistic": "Sum",
                            "Threshold": 1,
                            "TreatMissingData": "notBreaching",
                        }
                    },
                    "GuardFunctionThrottlesAlarm": {
                        "Properties": {
                            "Namespace": "AWS/Lambda",
                            "MetricName": "Throttles",
                            "Statistic": "Sum",
                            "Threshold": 1,
                            "TreatMissingData": "notBreaching",
                        }
                    },
                    "GuardFunctionDurationAlarm": {
                        "Properties": {
                            "Namespace": "AWS/Lambda",
                            "MetricName": "Duration",
                            "Statistic": "Maximum",
                            "Threshold": 50000,
                            "TreatMissingData": "notBreaching",
                        }
                    },
                }
            }
        }
        self.health = {"service": "iaap-guard", "status": "ok"}

    def test_complete_deployed_contract_passes(self):
        lines = verify_documents(
            self.stack,
            self.template,
            self.resources,
            self.health,
        )
        self.assertIn("Required resources: 5/5 complete", lines)

    def test_missing_alarm_fails_closed(self):
        self.resources["StackResources"] = [
            item
            for item in self.resources["StackResources"]
            if item["LogicalResourceId"] != "GuardFunctionErrorsAlarm"
        ]
        with self.assertRaisesRegex(ValueError, "missing deployed resource"):
            verify_documents(
                self.stack,
                self.template,
                self.resources,
                self.health,
            )

    def test_health_contract_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "health response"):
            verify_documents(
                self.stack,
                self.template,
                self.resources,
                {"service": "iaap-guard", "status": "degraded"},
            )


if __name__ == "__main__":
    unittest.main()
