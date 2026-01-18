"""File hashing utilities."""

import hashlib
from typing import Union, BinaryIO


def calculate_file_hash(file_content: Union[bytes, BinaryIO], algorithm: str = "sha256") -> str:
    """
    Calculate hash of file content.

    Args:
        file_content: File content as bytes or file-like object
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string

    Example:
        >>> content = b"Hello, World!"
        >>> calculate_file_hash(content)
        'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """
    if isinstance(file_content, bytes):
        hasher = hashlib.new(algorithm)
        hasher.update(file_content)
        return hasher.hexdigest()
    else:
        # For file-like objects, read in chunks to handle large files
        hasher = hashlib.new(algorithm)
        file_content.seek(0)

        while chunk := file_content.read(8192):
            hasher.update(chunk)

        file_content.seek(0)  # Reset position for potential re-reading
        return hasher.hexdigest()


def calculate_text_hash(text: str, algorithm: str = "sha256") -> str:
    """
    Calculate hash of text content.

    Args:
        text: Text content as string
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string

    Example:
        >>> calculate_text_hash("Hello, World!")
        'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    """
    return calculate_file_hash(text.encode('utf-8'), algorithm)
