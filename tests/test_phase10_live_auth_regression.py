from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from iaap_guard.github_app import create_app_jwt
from iaap_guard.lambda_handler import _load_app_secrets


class Phase10LiveAuthRegressionTests(unittest.TestCase):
    def test_deployed_app_id_is_parsed_as_integer_jwt_issuer(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("utf-8")

        with patch.dict(
            os.environ,
            {
                "IAAP_GUARD_GITHUB_APP_ID": "4529329",
                "IAAP_GUARD_GITHUB_PRIVATE_KEY": pem,
                "IAAP_GUARD_GITHUB_WEBHOOK_SECRET": "secret",
            },
            clear=False,
        ):
            secrets = _load_app_secrets()

        token = create_app_jwt(secrets.client_id, secrets.private_key, now=1_000_000)
        claims = jwt.decode(
            token,
            private_key.public_key(),
            algorithms=["RS256"],
            options={"verify_exp": False, "verify_iat": False},
        )
        self.assertEqual(claims["iss"], 4529329)
        self.assertIsInstance(claims["iss"], int)

    def test_non_numeric_app_id_is_rejected_before_api_authentication(self):
        with patch.dict(
            os.environ,
            {
                "IAAP_GUARD_GITHUB_APP_ID": "Iv1.not-an-app-id",
                "IAAP_GUARD_GITHUB_PRIVATE_KEY": "not-used",
                "IAAP_GUARD_GITHUB_WEBHOOK_SECRET": "secret",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(RuntimeError, "numeric GitHub App ID"):
                _load_app_secrets()


if __name__ == "__main__":
    unittest.main()
