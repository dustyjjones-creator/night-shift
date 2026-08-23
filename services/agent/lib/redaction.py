#!/usr/bin/env python3

import re


REDACTION = "[REDACTED]"


SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "access_key",
    "access-key",
    "private_key",
    "private-key",
    "authorization",
}


PATTERNS = [
    # Authorization headers and bearer-style tokens.
    (
        re.compile(
            r'(?i)(Authorization\s*:\s*(?:Bearer|Splunk|Token)\s+)([^\s"\']+)'
        ),
        r"\1" + REDACTION,
    ),

    # Generic key/value secrets.
    (
        re.compile(
            r'(?i)\b('
            r'password|passwd|secret|token|'
            r'api[_-]?key|access[_-]?key|private[_-]?key'
            r')(\s*[:=]\s*)([^\s,"\']+)'
        ),
        lambda match: (
            f"{match.group(1)}{match.group(2)}{REDACTION}"
        ),
    ),

    # Common OpenAI-style keys.
    (
        re.compile(r'\bsk-[A-Za-z0-9_-]{12,}\b'),
        REDACTION,
    ),

    # GitHub classic and fine-grained tokens.
    (
        re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
        REDACTION,
    ),

    # AWS access-key IDs.
    (
        re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
        REDACTION,
    ),

    # JWTs.
    (
        re.compile(
            r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'
        ),
        REDACTION,
    ),
]


PEM_BLOCK = re.compile(
    r"-----BEGIN [^-]+-----.*?-----END [^-]+-----",
    re.DOTALL,
)


def normalize_key(key):
    """Normalize a dictionary key for sensitive-key matching."""

    return (
        str(key)
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def is_sensitive_key(key):
    """Return whether a dictionary key normally contains a secret."""

    return normalize_key(key) in {
        value.replace("-", "_")
        for value in SENSITIVE_KEYS
    }


def redact_text(value):
    """Redact likely secrets from text before it enters an audit receipt."""

    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    value = PEM_BLOCK.sub(REDACTION, value)

    for pattern, replacement in PATTERNS:
        value = pattern.sub(replacement, value)

    return value


def redact_value(value):
    """Recursively redact strings inside JSON-like data."""

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [redact_value(item) for item in value]

    if isinstance(value, dict):
        result = {}

        for key, item in value.items():
            if is_sensitive_key(key):
                result[key] = REDACTION
            else:
                result[key] = redact_value(item)

        return result

    return value
