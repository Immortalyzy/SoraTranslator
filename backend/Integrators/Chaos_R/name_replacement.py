"""Chaos_R-specific name replacement helpers."""

import re

from global_name_replacement import apply_name_replacement_to_text, compile_name_replacement_pattern
from .parser import find_command_span_end

PROTECTED_COMMAND_PREFIXES = ("std_alt", "std_yui")
PROTECTED_COMMAND_NAMES = {"img_c"}


def command_name(command_text: str) -> str:
    """Return the lower-case command name from a bracketed command span."""
    return command_text[1:].lstrip().split(maxsplit=1)[0].rstrip("]").lower()


def is_protected_command(command_text: str) -> bool:
    """Return whether a command payload should stay literal during name replacement."""
    name = command_name(command_text)
    return name in PROTECTED_COMMAND_NAMES or name.startswith(PROTECTED_COMMAND_PREFIXES)


def find_protected_command_spans(text: str) -> list[tuple[int, int]]:
    """Return spans for bracketed commands whose payloads must stay literal."""
    spans = []
    cursor = 0
    while cursor < len(text):
        if text[cursor] != "[":
            cursor += 1
            continue

        command_end = find_command_span_end(text, cursor)
        if command_end is None:
            cursor += 1
            continue

        command_text = text[cursor:command_end]
        if is_protected_command(command_text):
            spans.append((cursor, command_end))
        cursor = command_end

    return spans


def apply_chaosr_name_replacement_to_text(
    text: str,
    mapping: dict[str, str],
    pattern: re.Pattern | None = None,
) -> str:
    """Apply global name replacement except inside img_c commands."""
    if text == "" or not mapping:
        return text

    working_pattern = pattern or compile_name_replacement_pattern(mapping)
    if working_pattern is None:
        return text

    protected_spans = find_protected_command_spans(text)
    if not protected_spans:
        return apply_name_replacement_to_text(text, mapping, working_pattern)

    parts = []
    cursor = 0
    for start, end in protected_spans:
        if cursor < start:
            parts.append(apply_name_replacement_to_text(text[cursor:start], mapping, working_pattern))
        parts.append(text[start:end])
        cursor = end

    if cursor < len(text):
        parts.append(apply_name_replacement_to_text(text[cursor:], mapping, working_pattern))

    return "".join(parts)
