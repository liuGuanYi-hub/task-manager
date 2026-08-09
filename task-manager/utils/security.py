"""日志和诊断输出的敏感信息保护工具。"""

import re
from collections.abc import Iterable


_BEARER_PATTERN = re.compile(r"(?i)(\bBearer\s+)([^\s,;]+)")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|password|secret|token)\b\s*[:=]\s*[\"']?)([^\"'\s,;]+)"
)
_URL_CREDENTIAL_PATTERN = re.compile(r"(?i)(https?://[^/\s:@]+:)([^@\s]+)(@)")


def redact_sensitive_text(value: object, secrets: Iterable[str] | None = None) -> str:
    """替换显式凭据和常见认证格式，避免诊断文本泄露原始值。"""
    text = str(value)
    for secret in sorted((item for item in (secrets or []) if item), key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    text = _BEARER_PATTERN.sub(r"\1[REDACTED]", text)
    text = _SECRET_ASSIGNMENT_PATTERN.sub(r"\1[REDACTED]", text)
    text = _URL_CREDENTIAL_PATTERN.sub(r"\1[REDACTED]\3", text)
    return text
