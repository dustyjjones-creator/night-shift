#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path("/home/dusty/night-shift").resolve()
AGENT_ROOT = PROJECT_ROOT / "services" / "agent"

if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from lib.redaction import REDACTION, redact_text, redact_value


class RedactionTests(unittest.TestCase):

    def assert_redacted(self, value, secret):
        result = redact_text(value)
        self.assertNotIn(secret, result)
        self.assertIn(REDACTION, result)

    def test_bearer_token_redacted(self):
        secret = "super-secret-token-value"
        self.assert_redacted(
            f"Authorization: Bearer {secret}",
            secret,
        )

    def test_splunk_token_redacted(self):
        secret = "splunk-hec-secret-value"
        self.assert_redacted(
            f"Authorization: Splunk {secret}",
            secret,
        )

    def test_password_redacted(self):
        secret = "correct-horse-battery-staple"
        self.assert_redacted(
            f"password={secret}",
            secret,
        )

    def test_api_key_redacted(self):
        secret = "my-api-key-secret"
        self.assert_redacted(
            f"api_key: {secret}",
            secret,
        )

    def test_openai_style_key_redacted(self):
        secret = "sk-abcdefghijklmnopqrstuvwxyz123456"
        self.assert_redacted(secret, secret)

    def test_github_token_redacted(self):
        secret = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        self.assert_redacted(secret, secret)

    def test_aws_access_key_redacted(self):
        secret = "AKIA1234567890ABCDEF"
        self.assert_redacted(secret, secret)

    def test_jwt_redacted(self):
        secret = (
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        self.assert_redacted(secret, secret)

    def test_pem_block_redacted(self):
        secret = (
            "-----BEGIN PRIVATE KEY-----\n"
            "this-is-secret-material\n"
            "-----END PRIVATE KEY-----"
        )
        self.assert_redacted(secret, secret)

    def test_sensitive_dictionary_values_redacted(self):
        secret = "nested-secret-value"

        value = {
            "event": {
                "token": secret,
                "message": f"password={secret}",
            },
            "items": [
                "ordinary-log-message",
                {
                    "authorization": (
                        f"Bearer {secret}"
                    ),
                },
            ],
        }

        result = redact_value(value)
        rendered = str(result)

        self.assertNotIn(secret, rendered)
        self.assertIn(REDACTION, rendered)

        self.assertEqual(
            result["items"][0],
            "ordinary-log-message",
        )

    def test_normal_text_unchanged(self):
        value = "Night Shift policy test completed successfully."
        self.assertEqual(redact_text(value), value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
