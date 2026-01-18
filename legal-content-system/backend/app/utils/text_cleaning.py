"""Text cleaning and normalization utilities."""

import re
from typing import Optional


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.

    - Replace multiple spaces with single space
    - Replace tabs with spaces
    - Remove leading/trailing whitespace from lines
    - Remove excessive blank lines (max 2 consecutive)

    Args:
        text: Input text

    Returns:
        Text with normalized whitespace
    """
    # Replace tabs with spaces
    text = text.replace('\t', ' ')

    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]

    # Remove excessive blank lines (keep max 2 consecutive)
    result_lines = []
    blank_count = 0

    for line in lines:
        if line:
            result_lines.append(line)
            blank_count = 0
        else:
            blank_count += 1
            if blank_count <= 2:
                result_lines.append(line)

    return '\n'.join(result_lines).strip()


def remove_page_numbers(text: str) -> str:
    """
    Remove common page number patterns from text.

    Args:
        text: Input text

    Returns:
        Text with page numbers removed
    """
    # Remove lines that are just page numbers
    # Patterns: "Page 1", "- 1 -", "1", etc.
    patterns = [
        r'^\s*-?\s*\d+\s*-?\s*$',  # Lines with just numbers
        r'^\s*עמוד\s*\d+\s*$',      # Hebrew "page N"
        r'^\s*Page\s*\d+\s*$',      # English "Page N"
        r'^\s*\d+\s*/\s*\d+\s*$',  # "1/10" format
    ]

    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        is_page_number = any(re.match(pattern, line, re.IGNORECASE) for pattern in patterns)
        if not is_page_number:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def remove_headers_footers(text: str) -> str:
    """
    Remove common header and footer patterns from legal documents.

    Args:
        text: Input text

    Returns:
        Text with headers/footers removed
    """
    lines = text.split('\n')
    cleaned_lines = []

    # Common patterns in Hebrew legal documents
    footer_patterns = [
        r'^\s*בית\s+משפט',         # Court name at bottom
        r'^\s*נוסח\s+מעודכן',       # Updated version
        r'^\s*הודפס\s+ב',          # Printed on
        r'^\s*www\.',              # URLs
        r'^\s*http[s]?://',        # URLs
    ]

    for line in lines:
        is_header_footer = any(re.match(pattern, line, re.IGNORECASE) for pattern in footer_patterns)
        if not is_header_footer:
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def normalize_hebrew_text(text: str) -> str:
    """
    Normalize Hebrew text formatting.

    - Fix common OCR errors with Hebrew characters
    - Normalize Hebrew punctuation
    - Remove nikud (vowel marks) if present

    Args:
        text: Input text

    Returns:
        Normalized Hebrew text
    """
    # Remove nikud (Hebrew vowel marks)
    # Unicode range: U+0591 to U+05C7
    text = re.sub(r'[\u0591-\u05C7]', '', text)

    # Normalize Hebrew quotes
    text = text.replace('״', '"').replace('׳', "'")

    return text


def clean_text(text: str, aggressive: bool = False) -> str:
    """
    Clean and normalize text from legal documents.

    Args:
        text: Raw extracted text
        aggressive: If True, apply more aggressive cleaning (may remove useful info)

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Basic normalization
    text = normalize_whitespace(text)
    text = normalize_hebrew_text(text)

    if aggressive:
        # More aggressive cleaning
        text = remove_page_numbers(text)
        text = remove_headers_footers(text)
        text = normalize_whitespace(text)  # Re-normalize after removals

    return text.strip()


def normalize_text(text: str) -> str:
    """
    Light normalization of text (alias for clean_text with aggressive=False).

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    return clean_text(text, aggressive=False)


def extract_metadata_patterns(text: str) -> dict:
    """
    Extract common metadata patterns from legal text.

    Looks for patterns like:
    - Case numbers
    - Dates
    - Court names
    - Judge names

    Args:
        text: Legal document text

    Returns:
        Dictionary with extracted metadata (may be empty if not found)
    """
    metadata = {}

    # Extract case number patterns (common in Israeli courts)
    case_number_patterns = [
        r'תיק\s+(?:מס\'?|מספר|ת"פ|ת"א|ע"א)[\s:]*(\d+[-/]\d+[-/]?\d*)',
        r'(?:ת"פ|ת"א|ע"א)\s*(\d+[-/]\d+[-/]?\d*)',
    ]

    for pattern in case_number_patterns:
        match = re.search(pattern, text)
        if match:
            metadata['case_number'] = match.group(1)
            break

    # Extract date patterns
    date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'
    dates = re.findall(date_pattern, text[:1000])  # Look in first 1000 chars
    if dates:
        metadata['potential_dates'] = dates[:5]  # Keep first 5 dates found

    # Extract court name
    court_patterns = [
        r'בית\s+(?:המשפט|משפט)\s+([\u0590-\u05FF\s]+?)(?=\n|בפני|התובע)',
    ]

    for pattern in court_patterns:
        match = re.search(pattern, text[:500])
        if match:
            metadata['court_name'] = match.group(1).strip()
            break

    # Extract judge name
    judge_patterns = [
        r'בפני\s+(?:כבוד\s+)?(?:השופט|השופטת|ה?שופט\s+ה?כבוד)\s+([\u0590-\u05FF\s.]+?)(?=\n)',
        r'השופט[ת]?\s+([\u0590-\u05FF\s.]+?)(?=\n)',
    ]

    for pattern in judge_patterns:
        match = re.search(pattern, text[:800])
        if match:
            metadata['judge_name'] = match.group(1).strip()
            break

    return metadata
