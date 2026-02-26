"""Helpers for global name replacement table and replacement logic."""

import os
import re
from dataclasses import dataclass
from typing import Any

GLOBAL_NAME_REPLACEMENT_FILENAME = "__global_name_replacement__.csv"
GLOBAL_NAME_REPLACEMENT_FILE_TYPE = "name_replacement"
GLOBAL_NAME_REPLACEMENT_DISPLAY_NAME = "[Global Name Replacement]"
GLOBAL_NAME_REPLACEMENT_SCRIPT_PATH = "__global_name_replacement__"


@dataclass(frozen=True)
class NameReplacementRow:
    """Canonical row model for global name replacement."""

    source_name: str
    replacement_name: str
    source_count: str = ""


def global_name_replacement_path(text_directory: str) -> str:
    """Return the managed global name replacement table path."""
    return os.path.join(text_directory, GLOBAL_NAME_REPLACEMENT_FILENAME)


def is_global_name_replacement_file(file_path: str) -> bool:
    """Return True if file_path points to the managed replacement table file."""
    return os.path.basename(file_path).lower() == GLOBAL_NAME_REPLACEMENT_FILENAME.lower()


def _field_from_row(row: Any, *names: str) -> Any:
    if isinstance(row, dict):
        for name in names:
            if name in row:
                return row[name]
        return ""

    for name in names:
        if hasattr(row, name):
            return getattr(row, name)
    return ""


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_name_replacement_row(row: Any) -> NameReplacementRow | None:
    """
    Parse one row from dict/block object into canonical row model.
    Empty source rows are ignored.
    """
    source_name = _normalize_text(_field_from_row(row, "source_name", "speaker_original"))
    if source_name == "":
        return None

    replacement_name = _normalize_text(_field_from_row(row, "replacement_name", "speaker_translated"))
    source_count = _normalize_text(_field_from_row(row, "source_count", "text_original"))
    return NameReplacementRow(
        source_name=source_name,
        replacement_name=replacement_name,
        source_count=source_count,
    )


def _count_to_int(value: Any) -> int:
    """Parse source_count values safely for sorting."""
    try:
        return max(int(str(value).strip()), 0)
    except (TypeError, ValueError):
        return 0


def sort_name_replacement_rows_by_appearance(rows: list[NameReplacementRow]) -> list[NameReplacementRow]:
    """
    Sort rows by appearance count descending.
    Rows with equal count keep their original relative order.
    """
    return sorted(rows, key=lambda row: -_count_to_int(row.source_count))


def normalize_name_replacement_rows(rows: list[Any]) -> list[NameReplacementRow]:
    """
    Normalize raw rows into canonical unique rows.

    Rules:
    - Trim source/replacement/count text.
    - Ignore rows with empty source names.
    - Duplicate sources keep the last occurrence.
    - Stable ordering follows the kept (last) rows' original positions.
    """
    parsed_rows: list[NameReplacementRow] = []
    for row in rows:
        parsed = parse_name_replacement_row(row)
        if parsed is None:
            continue
        parsed_rows.append(parsed)

    last_index_by_source: dict[str, int] = {}
    for index, row in enumerate(parsed_rows):
        last_index_by_source[row.source_name] = index

    normalized_rows: list[NameReplacementRow] = []
    for index, row in enumerate(parsed_rows):
        if last_index_by_source[row.source_name] != index:
            continue
        normalized_rows.append(row)

    return normalized_rows


def build_name_replacement_mapping(rows: list[Any]) -> dict[str, str]:
    """
    Build mapping from canonical rows.

    Empty replacement text means "no replacement" and is skipped.
    """
    mapping: dict[str, str] = {}
    normalized_rows = normalize_name_replacement_rows(rows)
    for row in normalized_rows:
        if row.replacement_name == "":
            continue
        mapping[row.source_name] = row.replacement_name
    return mapping


def compile_name_replacement_pattern(mapping: dict[str, str]) -> re.Pattern | None:
    """Compile deterministic replacement pattern from mapping keys."""
    if not mapping:
        return None

    ordered_keys = sorted(mapping.keys(), key=lambda item: (-len(item), item))
    escaped = [re.escape(key) for key in ordered_keys]
    if not escaped:
        return None
    return re.compile("|".join(escaped))


def apply_name_replacement_to_text(text: str, mapping: dict[str, str], pattern: re.Pattern | None = None) -> str:
    """
    Apply one-pass deterministic replacements to text.
    """
    if text == "" or not mapping:
        return text

    working_pattern = pattern or compile_name_replacement_pattern(mapping)
    if working_pattern is None:
        return text
    return working_pattern.sub(lambda matched: mapping[matched.group(0)], text)
