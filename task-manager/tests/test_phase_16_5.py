"""阶段 16.5：日志脱敏与敏感信息扫描。"""

from pathlib import Path

from scripts.security_scan import scan_tree
from utils.security import redact_sensitive_text


def test_redact_sensitive_text_removes_explicit_and_common_credentials():
    raw = (
        "Authorization: Bearer test-secret-value "
        "TASK_MANAGER_API_TOKEN=test-secret-value "
        "https://deploy:test-password-value@example.com"
    )

    redacted = redact_sensitive_text(raw, secrets=["test-secret-value", "test-password-value"])

    assert "test-secret-value" not in redacted
    assert "test-password-value" not in redacted
    assert redacted.count("[REDACTED]") >= 3


def test_security_scan_ignores_safe_placeholders_and_reports_only_location(tmp_path):
    safe = tmp_path / "safe.md"
    safe.write_text("Bearer YOUR_API_TOKEN\nTOKEN = test-only-token\n", encoding="utf-8")
    unsafe = tmp_path / "unsafe.py"
    unsafe.write_text(
        "API_" + "TOKEN = " + chr(34) + "live-value-123456" + chr(34) + "\n",
        encoding="utf-8",
    )

    issues = scan_tree(Path(tmp_path))

    assert len(issues) == 1
    assert issues[0]["path"] == "unsafe.py"
    assert issues[0]["line"] == 1
    assert issues[0]["rule"] == "secret-assignment"
    assert "live-value" not in str(issues)


def test_repository_security_scan_passes_without_printing_matching_content():
    root = Path(__file__).resolve().parents[1]
    assert scan_tree(root) == []
