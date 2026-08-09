"""扫描仓库中的常见硬编码凭据，只输出位置和规则名，不输出匹配内容。"""

import argparse
import re
from pathlib import Path


_TEXT_SUFFIXES = {".md", ".py", ".ps1", ".txt", ".html", ".js", ".css", ".yml", ".yaml"}
_SKIP_NAMES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
_SKIP_PREFIXES = (".env",)
_SKIP_SUFFIXES = (".json", ".db", ".sqlite", ".sqlite3", ".log")
_PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_TOKEN_PATTERN = re.compile(
    r"(?i)\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"
)
_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:api[_-]?(?:key|token)|access[_-]?token|refresh[_-]?token|auth[_-]?token|password|secret|token)\b\s*[:=]\s*[\"'`]?([A-Za-z0-9._~+/=-]{12,})"
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]{12,})")
_GENERATED_VALUE_PATTERN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\s*\(")


def _is_placeholder(value: str) -> bool:
    normalized = value.strip("\"'`").strip()
    upper = normalized.upper()
    return (
        upper.startswith(("YOUR_", "PLACEHOLDER", "REPLACE_ME", "EXAMPLE_"))
        or normalized.startswith("<")
        or normalized.lower() in {"changeme", "dummy-token", "test-only-token"}
        or normalized.lower().startswith(("test-", "test_"))
    )


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_NAMES for part in path.parts):
            continue
        if any(path.name.startswith(prefix) for prefix in _SKIP_PREFIXES):
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES or path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        yield path


def scan_tree(root: Path) -> list[dict[str, object]]:
    """返回扫描问题的位置和规则，不返回匹配文本。"""
    issues: list[dict[str, object]] = []
    for path in _iter_text_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            rules = []
            if _PRIVATE_KEY_PATTERN.search(line):
                rules.append("private-key-header")
            if _TOKEN_PATTERN.search(line):
                rules.append("known-token-format")
            assignment = _ASSIGNMENT_PATTERN.search(line)
            if (
                assignment
                and not _is_placeholder(assignment.group(1))
                and not _GENERATED_VALUE_PATTERN.search(line)
            ):
                rules.append("secret-assignment")
            bearer = _BEARER_PATTERN.search(line)
            if bearer and not _is_placeholder(bearer.group(1)):
                rules.append("bearer-token")
            for rule in rules:
                issues.append(
                    {
                        "path": str(path.relative_to(root)),
                        "line": line_number,
                        "rule": rule,
                    }
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.root.resolve()
    issues = scan_tree(root)
    if issues:
        for issue in issues:
            print(f"sensitive scan failed: {issue['path']}:{issue['line']} ({issue['rule']})")
        return 1
    print(f"sensitive scan passed: checked {sum(1 for _ in _iter_text_files(root))} text files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
