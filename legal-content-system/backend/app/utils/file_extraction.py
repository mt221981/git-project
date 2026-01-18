"""File text extraction utilities."""

import io
from pathlib import Path
from typing import Union, BinaryIO
import PyPDF2
from docx import Document


class TextExtractionError(Exception):
    """Exception raised when text extraction fails."""
    pass


def extract_text_from_pdf(file_content: Union[bytes, BinaryIO]) -> str:
    """
    Extract text from a PDF file.

    Args:
        file_content: PDF file content as bytes or file-like object

    Returns:
        Extracted text as string

    Raises:
        TextExtractionError: If extraction fails
    """
    try:
        if isinstance(file_content, bytes):
            file_content = io.BytesIO(file_content)

        pdf_reader = PyPDF2.PdfReader(file_content)
        text_parts = []

        for page_num, page in enumerate(pdf_reader.pages, start=1):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            except Exception as e:
                print(f"Warning: Failed to extract text from page {page_num}: {e}")
                continue

        if not text_parts:
            raise TextExtractionError("No text could be extracted from PDF")

        return "\n\n".join(text_parts)

    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_content: Union[bytes, BinaryIO]) -> str:
    """
    Extract text from a DOCX file.

    Args:
        file_content: DOCX file content as bytes or file-like object

    Returns:
        Extracted text as string

    Raises:
        TextExtractionError: If extraction fails
    """
    try:
        if isinstance(file_content, bytes):
            file_content = io.BytesIO(file_content)

        doc = Document(file_content)
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        if not text_parts:
            raise TextExtractionError("No text could be extracted from DOCX")

        return "\n\n".join(text_parts)

    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_txt(file_content: Union[bytes, BinaryIO]) -> str:
    """
    Extract text from a TXT file.

    Args:
        file_content: TXT file content as bytes or file-like object

    Returns:
        Extracted text as string

    Raises:
        TextExtractionError: If extraction fails
    """
    try:
        if isinstance(file_content, bytes):
            # Try different encodings
            encodings = ['utf-8', 'windows-1255', 'iso-8859-8', 'cp1252']

            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    if text.strip():
                        return text
                except (UnicodeDecodeError, AttributeError):
                    continue

            raise TextExtractionError("Could not decode text file with any known encoding")
        else:
            text = file_content.read()
            if isinstance(text, bytes):
                return extract_text_from_txt(text)
            return text

    except Exception as e:
        raise TextExtractionError(f"Failed to extract text from TXT: {str(e)}")


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        file_content: File content as bytes
        filename: Original filename with extension

    Returns:
        Extracted text as string

    Raises:
        TextExtractionError: If extraction fails or file type is unsupported
    """
    file_extension = Path(filename).suffix.lower()

    extractors = {
        '.pdf': extract_text_from_pdf,
        '.txt': extract_text_from_txt,
        '.docx': extract_text_from_docx,
        '.doc': extract_text_from_docx,  # Will attempt to read as docx
    }

    extractor = extractors.get(file_extension)
    if not extractor:
        raise TextExtractionError(
            f"Unsupported file type: {file_extension}. "
            f"Supported types: {', '.join(extractors.keys())}"
        )

    return extractor(file_content)
