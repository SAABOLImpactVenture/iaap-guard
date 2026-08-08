from __future__ import annotations

import base64
import json
import os
from typing import Any

from .github_app import AppSecrets, GitHubAppError, verify_webhook_signature
from .github_beta_runtime import BetaGitHubApi, handle_beta_github_event


def _secret_from_aws(secret_arn: str) -> str:
    """Read the current Secrets Manager value.

    Phase 10 intentionally avoids process-lifetime caching so webhook-secret or
    private-key rotation under the same ARN is observed by warm Lambda
    environments without requiring a redeploy.
    """

    import boto3

    response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    value = response.get("SecretString")
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Secrets Manager value {secret_arn!r} is not a non-empty SecretString")
    return value


def _load_secret(direct_env: str, arn_env: str) -> str:
    direct = os.environ.get(direct_env)
    if direct:
        return direct
    arn = os.environ.get(arn_env)
    if arn:
        return _secret_from_aws(arn)
    raise RuntimeError(f"configure {direct_env} for local testing or {arn_env} for deployed runtime")


def _load_app_secrets(*, webhook_secret: str | None = None) -> AppSecrets:
    app_id_raw = os.environ.get("IAAP_GUARD_GITHUB_APP_ID", "").strip()
    if not app_id_raw:
        raise RuntimeError("IAAP_GUARD_GITHUB_APP_ID is required")
    try:
        app_id = int(app_id_raw)
    except ValueError as exc:
        raise RuntimeError("IAAP_GUARD_GITHUB_APP_ID must be the numeric GitHub App ID") from exc
    if app_id <= 0:
        raise RuntimeError("IAAP_GUARD_GITHUB_APP_ID must be a positive integer")
    return AppSecrets(
        app_id=app_id,
        private_key=_load_secret("IAAP_GUARD_GITHUB_PRIVATE_KEY", "IAAP_GUARD_GITHUB_PRIVATE_KEY_SECRET_ARN"),
        webhook_secret=webhook_secret
        if webhook_secret is not None
        else _load_secret("IAAP_GUARD_GITHUB_WEBHOOK_SECRET", "IAAP_GUARD_GITHUB_WEBHOOK_SECRET_ARN"),
    )


def _headers(event: dict[str, Any]) -> dict[str, str]:
    source = event.get("headers") or {}
    if not isinstance(source, dict):
        return {}
    return {str(key).lower(): str(value) for key, value in source.items() if value is not None}


def _body_bytes(event: dict[str, Any]) -> bytes:
    body = event.get("body")
    if body is None:
        return b""
    if not isinstance(body, str):
        raise ValueError("Lambda Function URL body must be a string")
    if event.get("isBase64Encoded"):
        return base64.b64decode(body, validate=True)
    return body.encode("utf-8")


def _response(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, separators=(",", ":")),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:  # noqa: ARG001
    request_context = event.get("requestContext") or {}
    http = request_context.get("http") or {}
    method = str(http.get("method") or "POST").upper()
    if method == "GET":
        return _response(200, {"service": "iaap-guard", "status": "ok"})
    if method != "POST":
        return _response(405, {"error": "method_not_allowed"})

    try:
        headers = _headers(event)
        raw_body = _body_bytes(event)
        webhook_secret = _load_secret(
            "IAAP_GUARD_GITHUB_WEBHOOK_SECRET",
            "IAAP_GUARD_GITHUB_WEBHOOK_SECRET_ARN",
        )
        if not verify_webhook_signature(raw_body, webhook_secret, headers.get("x-hub-signature-256")):
            return _response(401, {"error": "invalid_webhook_signature"})

        secrets = _load_app_secrets(webhook_secret=webhook_secret)
        event_name = headers.get("x-github-event")
        delivery = headers.get("x-github-delivery")
        if not event_name:
            return _response(400, {"error": "missing_github_event"})
        payload = json.loads(raw_body.decode("utf-8"))
        if not isinstance(payload, dict):
            return _response(400, {"error": "invalid_json_payload"})

        api = BetaGitHubApi(base_url=os.environ.get("IAAP_GUARD_GITHUB_API_URL", "https://api.github.com"))
        result = handle_beta_github_event(event_name, payload, api=api, secrets=secrets)
        result["delivery"] = delivery
        return _response(200 if result.get("handled") else 202, result)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"IaaP Guard rejected webhook payload: {type(exc).__name__}: {exc}")
        return _response(400, {"error": "invalid_webhook_payload"})
    except (GitHubAppError, RuntimeError) as exc:
        print(f"IaaP Guard webhook processing failed: {type(exc).__name__}: {exc}")
        return _response(500, {"error": "webhook_processing_failed"})
