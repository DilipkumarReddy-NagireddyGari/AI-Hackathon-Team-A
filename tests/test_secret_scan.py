from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".ini", ".ipynb", ".md", ".py", ".toml", ".txt", ".yaml", ".yml", ".example"}
SECRET_PATTERNS = {
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    "assigned credential": re.compile(
        r"(?i)(api[_-]?key|virtual[_-]?key|token|password)\s*=\s*[\"'][A-Za-z0-9_./+-]{16,}[\"']"
    ),
}


def tracked_text_files() -> list[Path]:
    ignored_parts = {".git", ".pytest_cache", ".venv", "__pycache__", "data"}
    return [
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file()
        and not ignored_parts.intersection(path.parts)
        and (path.suffix in TEXT_SUFFIXES or path.name == ".env.example")
    ]


def test_repository_contains_no_secret_patterns() -> None:
    findings: list[str] = []
    for path in tracked_text_files():
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern_name, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{path.relative_to(PROJECT_ROOT)}: {pattern_name}")

    assert not findings, "Potential credentials found:\n" + "\n".join(findings)
