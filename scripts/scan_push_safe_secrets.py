#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXCLUDED_DIRS = {".git", ".venv", ".pytest_cache", "__pycache__", "dist"}
EXCLUDED_SUFFIXES = {".zip", ".pyc", ".db", ".sqlite", ".sqlite3", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}

SECRET_PATTERNS = (
    ("openai_key", re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("github_token", re.compile(r"gh[opusr]_[A-Za-z0-9_]{20,}")),
    ("bearer_token", re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9._-]{24,}", re.I)),
    ("service_token", re.compile(r"X-SC-Service-Token:\s*[A-Za-z0-9._-]{20,}", re.I)),
    ("federation_trust_json", re.compile(r"^\s*#?\s*SC_CORE_FEDERATION_TRUST_SECRETS_JSON\s*=\s*\S+")),
)

ALLOWED_FEDERATION_PLACEHOLDERS = {
    "replace-with-long-random-secret",
    "replace-me",
    "change-me",
    "shared-federation-secret",
    "test-secret",
    "secret-token",
}


def _federation_assignment_is_documented_placeholder(line: str) -> bool:
    candidate = line.strip()
    if candidate.startswith("#"):
        candidate = candidate[1:].strip()
    prefix = "SC_CORE_FEDERATION_TRUST_SECRETS_JSON="
    if not candidate.startswith(prefix):
        return False
    raw = candidate[len(prefix):].strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return False
    if not isinstance(parsed, dict) or not parsed:
        return False
    return all(
        isinstance(value, str) and value in ALLOWED_FEDERATION_PLACEHOLDERS
        for value in parsed.values()
    )


def scan_text(path: Path, text: str) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS:
            if not pattern.search(line):
                continue
            if kind == "federation_trust_json" and _federation_assignment_is_documented_placeholder(line):
                continue
            hits.append((lineno, kind, line.strip()))
    return hits


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        yield path


def scan_repository(root: Path) -> list[tuple[str, int, str, str]]:
    hits: list[tuple[str, int, str, str]] = []
    for path in iter_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, kind, line in scan_text(path, text):
            hits.append((path.relative_to(root).as_posix(), lineno, kind, line))
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    hits = scan_repository(root)
    if hits:
        for path, lineno, kind, line in hits:
            print(f"{path}:{lineno}:{kind}:{line}")
        print("ERROR: Potential secret found. Nothing was pushed.", file=sys.stderr)
        return 1
    print("PASS - push-safe secret scan; documented placeholders allowed, live-looking credentials rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
