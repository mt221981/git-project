"""
JSON Repair Utility for LLM Responses.

Handles common JSON parsing issues from Claude and other LLM responses:
- Markdown code blocks
- Missing/trailing commas
- Unescaped newlines in strings
- Incomplete JSON with missing closing braces

Updated: 2026-01-17
"""

import re
import json
from typing import Any, Optional, Dict


def repair_json(text: str) -> str:
    """
    Attempt to repair common JSON issues from LLM responses.

    Args:
        text: Raw text that should contain JSON

    Returns:
        Repaired JSON string
    """
    # 1. Extract JSON from markdown blocks
    text = extract_from_markdown(text)

    # 2. Find JSON boundaries using brace matching
    text = extract_json_object(text)

    # 3. Fix common issues
    text = fix_trailing_commas(text)
    text = fix_missing_commas(text)
    text = fix_newlines_in_strings(text)

    return text


def extract_from_markdown(text: str) -> str:
    """
    Remove markdown code blocks from text.

    Handles both ```json ... ``` and ``` ... ``` blocks.
    Also handles cases where closing ``` is missing (truncated response).
    """
    text = text.strip()

    # Handle ```json ... ``` blocks (complete)
    pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(pattern, text)
    if matches:
        # Return the first match (usually the JSON block)
        return matches[0].strip()

    # If text starts with ``` but no closing (truncated response), extract anyway
    if text.startswith('```'):
        lines = text.split('\n')
        # Skip first line (```json or ```)
        json_lines = []
        for line in lines[1:]:
            if line.strip().startswith('```'):
                break
            json_lines.append(line)
        if json_lines:
            return '\n'.join(json_lines).strip()

    # Also check for ``` anywhere in the text (in case of leading text)
    if '```json' in text or '```\n{' in text:
        # Find start of code block
        start_patterns = ['```json\n', '```json\r\n', '```\n', '```\r\n']
        for pattern in start_patterns:
            if pattern in text:
                start_idx = text.find(pattern) + len(pattern)
                remaining = text[start_idx:]
                # Find end of code block
                end_idx = remaining.find('```')
                if end_idx != -1:
                    return remaining[:end_idx].strip()
                else:
                    # No closing ```, return everything after opening
                    return remaining.strip()

    return text


def extract_json_object(text: str) -> str:
    """
    Extract JSON object using proper brace matching.

    Handles nested objects/arrays and strings with braces.
    Also handles truncated responses with unterminated strings.
    """
    start = text.find('{')
    if start == -1:
        return text

    # Count braces to find matching end
    depth = 0
    in_string = False
    escape_next = False
    in_array = 0  # Track array depth for proper closing

    for i, char in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start:i+1]
        elif char == '[':
            in_array += 1
        elif char == ']':
            in_array -= 1

    # If we're still in a string (truncated response), close it
    result = text[start:]
    if in_string:
        result += '"'

    # Close any open arrays
    if in_array > 0:
        result += ']' * in_array

    # Add missing closing braces
    if depth > 0:
        result += '}' * depth

    return result


def fix_trailing_commas(text: str) -> str:
    """
    Remove trailing commas before } or ].

    Example: {"a": 1,} -> {"a": 1}
    """
    return re.sub(r',\s*([}\]])', r'\1', text)


def fix_missing_commas(text: str) -> str:
    """
    Add missing commas between JSON elements.

    Common patterns:
    - "value"\n"key" -> "value",\n"key"
    - }\n" -> },\n"
    - ]\n" -> ],\n"
    - true\n" -> true,\n"
    - false\n" -> false,\n"
    - null\n" -> null,\n"
    - number\n" -> number,\n"
    """
    # String followed by string (allow multiple newlines/spaces between)
    text = re.sub(r'"\s*\n[\s\n]*"', '",\n"', text)

    # Object/array close followed by string (allow multiple newlines)
    text = re.sub(r'}\s*\n[\s\n]*"', '},\n"', text)
    text = re.sub(r']\s*\n[\s\n]*"', '],\n"', text)

    # Boolean/null followed by string
    text = re.sub(r'(true|false|null)\s*\n[\s\n]*"', r'\1,\n"', text)

    # Number followed by string (careful not to match decimals)
    text = re.sub(r'(\d)\s*\n[\s\n]*"', r'\1,\n"', text)

    # Object/array close followed by object/array start
    text = re.sub(r'}\s*\n[\s\n]*\{', '},\n{', text)
    text = re.sub(r']\s*\n[\s\n]*\[', '],\n[', text)
    text = re.sub(r'}\s*\n[\s\n]*\[', '},\n[', text)
    text = re.sub(r']\s*\n[\s\n]*\{', '],\n{', text)

    return text


def fix_newlines_in_strings(text: str) -> str:
    """
    Escape literal newlines inside JSON strings.

    JSON strings cannot contain literal newlines - they must be escaped as \\n.
    """
    result = []
    in_string = False
    escape_next = False

    for char in text:
        if escape_next:
            result.append(char)
            escape_next = False
            continue

        if char == '\\':
            result.append(char)
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            result.append(char)
            continue

        if in_string and char == '\n':
            # Replace literal newline with escaped newline
            result.append('\\n')
            continue

        if in_string and char == '\r':
            # Skip carriage returns inside strings
            continue

        if in_string and char == '\t':
            # Replace literal tab with escaped tab
            result.append('\\t')
            continue

        result.append(char)

    return ''.join(result)


def safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON with multiple repair attempts.

    Args:
        text: Raw text that should contain JSON

    Returns:
        Parsed dict on success, None on failure
    """
    if not text or not text.strip():
        return None

    # First try: direct parse (maybe it's already valid)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[json_repair] Direct parse failed: {e}")

    # Second try: repair and parse
    try:
        repaired = repair_json(text)
        print(f"[json_repair] After repair, first 200 chars: {repaired[:200]}")
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        print(f"[json_repair] Repair attempt 1 failed: {e}")

    # Third try: aggressive cleanup - remove control characters
    try:
        # Remove all control characters except newlines and tabs
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        repaired = repair_json(cleaned)
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        print(f"[json_repair] Repair attempt 2 (control chars removed) failed: {e}")

    # Fourth try: even more aggressive - strip everything before first {
    try:
        start = text.find('{')
        if start > 0:
            cleaned = text[start:]
            repaired = repair_json(cleaned)
            return json.loads(repaired)
    except json.JSONDecodeError as e:
        print(f"[json_repair] Repair attempt 3 (strip prefix) failed: {e}")

    return None


def parse_json_with_fallback(text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse JSON with a fallback value if parsing fails.

    Args:
        text: Raw text that should contain JSON
        fallback: Value to return if parsing fails

    Returns:
        Parsed dict or fallback value
    """
    result = safe_parse_json(text)
    return result if result is not None else fallback
