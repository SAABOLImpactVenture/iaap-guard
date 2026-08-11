from __future__ import annotations

import io
import tarfile
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from iaap_guard.github_app import AppSecrets, CHECK_NAME
from iaap_guard.github_beta_runtime import BetaGitHubApi
from iaap_guard.github_evidence_runtime import handle_evidence_aware_event


BASE_SHA = "a" * 40
HEAD_SHA = "b" * 40


def _tarball(product_yaml: bytes) -> bytes:
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        entries = {
            "repo-abc/product.yaml": product_yaml,
            "repo-abc/tests/test_contract.py": b"# deterministic validation evidence\n",
        }
        for name, body in entries.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
    return data.getvalue()


GOOD_PRODUCT = (
    b"apiVersion: platform.example.org/v1alpha1\n"
    b"kind: InfrastructureProductSchema\n"
    b"metadata:\n"
    b"  name: application-environment\n"
    b"spec:\n"
    b"  required: [owner]\n"
    b"  properties:\n"
    b"    owner:\n"
    b"      type: string\n"
)

PROVIDER_CONFIG_LEAK = (
    b"apiVersion: platform.example.org/v1alpha1\n"
    b"kind: InfrastructureProductSchema\n"
    b"metadata:\n"
    b"  name: application-environment\n"
    b"spec:\n"
    b"  required: [owner]\n"
    b"  properties:\n"
    b"    owner:\n"
    b"      type: string\n"
    b"    providerConfig:\n"
    b"      type: string\n"
    b"      description: Consumer chooses the Crossplane ProviderConfig used for provisioning.\n"
)


class _EvidenceApi(BetaGitHubApi):
    def __init__(self, archives: dict[str, bytes]):
        super().__init__()
        self.archives = archives
        self.initial_upsert = None
        self.replaced_payload = None

    def installation_token(self, app_jwt, installation_id, repository_id):  # noqa: ARG002
        return "ghs_phase14_test"

    def pull_request_files(self, token, repository, pull_number):  # noqa: ARG002
        return ["product.yaml"]

    def repository_tarball(self, token, repository, revision):  # noqa: ARG002
        return self.archives[revision]

    def upsert_check_run(self, token, target, result, *, no_relevant_changes):  # noqa: ARG002
        self.initial_upsert = (target, result, no_relevant_changes)
        return {"id": 42}

    def check_runs_for_revision(self, token, repository, revision):  # noqa: ARG002
        return [
            {
                "id": 42,
                "name": CHECK_NAME,
                "external_id": f"iaap-guard:14:{HEAD_SHA}",
            }
        ]

    def _request(self, method, path, **kwargs):
        if method == "PATCH" and path.endswith("/check-runs/42"):
            self.replaced_payload = kwargs.get("body")
            return {"id": 42}
        raise AssertionError(f"unexpected request: {method} {path}")


def _secrets() -> AppSecrets:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    return AppSecrets(4529329, pem, "secret")


def _payload() -> dict:
    return {
        "action": "synchronize",
        "number": 14,
        "installation": {"id": 89},
        "repository": {"id": 992, "full_name": "example/product"},
        "pull_request": {
            "head": {"sha": HEAD_SHA},
            "base": {"sha": BASE_SHA},
        },
    }


class Phase14PrBaseContinuityTests(unittest.TestCase):
    def test_same_guard_state_is_reported_as_supported_without_changing_check_conclusion(self):
        archive = _tarball(GOOD_PRODUCT)
        api = _EvidenceApi({BASE_SHA: archive, HEAD_SHA: archive})

        result = handle_evidence_aware_event(
            "pull_request",
            _payload(),
            api=api,
            secrets=_secrets(),
        )

        evidence = result["evidenceContinuity"]
        self.assertEqual(evidence["status"], "supported")
        self.assertEqual(evidence["baselineRevision"], BASE_SHA)
        self.assertEqual(evidence["materiality"], "no_guard_material_change_detected")
        self.assertIsNotNone(api.replaced_payload)
        self.assertEqual(api.replaced_payload["conclusion"], api.initial_upsert[1]["conclusion"])
        self.assertIn("Evidence continuity: **SUPPORTED**", api.replaced_payload["output"]["summary"])
        self.assertIn("Evidence continuity is not authorization continuity", api.replaced_payload["output"]["text"])

    def test_guard_material_change_requires_review_but_remains_advisory_to_check_conclusion(self):
        api = _EvidenceApi(
            {
                BASE_SHA: _tarball(GOOD_PRODUCT),
                HEAD_SHA: _tarball(PROVIDER_CONFIG_LEAK),
            }
        )

        result = handle_evidence_aware_event(
            "pull_request",
            _payload(),
            api=api,
            secrets=_secrets(),
        )

        evidence = result["evidenceContinuity"]
        self.assertEqual(evidence["status"], "review_required")
        self.assertEqual(evidence["materiality"], "guard_material_change_detected")
        self.assertEqual(evidence["disposition"], "human_review_required")
        self.assertEqual(api.replaced_payload["conclusion"], api.initial_upsert[1]["conclusion"])
        self.assertIn("Evidence continuity: **REVIEW REQUIRED**", api.replaced_payload["output"]["summary"])
        self.assertIn("Finding evidence:", api.replaced_payload["output"]["text"])


if __name__ == "__main__":
    unittest.main()
