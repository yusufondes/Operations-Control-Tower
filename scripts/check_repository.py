from __future__ import annotations

import csv
import sys
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".csv",
    ".example",
    ".md",
    ".ps1",
    ".py",
    ".xml",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
TURKISH_CHARACTERS = {
    chr(code_point)
    for code_point in (199, 214, 220, 231, 246, 252, 286, 287, 304, 305, 350, 351)
}


def repository_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {
            ".editorconfig",
            ".gitattributes",
            ".gitignore",
            "LICENSE",
        }:
            yield path


def main() -> int:
    errors: list[str] = []
    files = list(repository_files())

    for path in files:
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            errors.append(f"{relative}: not valid UTF-8 ({error})")
            continue

        found = sorted(TURKISH_CHARACTERS.intersection(text))
        if found:
            errors.append(
                f"{relative}: Turkish characters found: {''.join(found)}"
            )

        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                errors.append(f"{relative}:{line_number}: trailing whitespace")

        if path.suffix.lower() == ".xml":
            try:
                ElementTree.parse(path)
            except ElementTree.ParseError as error:
                errors.append(f"{relative}: invalid XML ({error})")

        if path.suffix.lower() == ".csv":
            rows = [row for row in csv.reader(text.splitlines()) if row]
            if rows:
                width = len(rows[0])
                for row_number, row in enumerate(rows[1:], start=2):
                    if len(row) != width:
                        errors.append(
                            f"{relative}:{row_number}: expected {width} columns, found {len(row)}"
                        )

    if errors:
        print("Repository checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Repository checks passed for {len(files)} text files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
