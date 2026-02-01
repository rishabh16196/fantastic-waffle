"""
File parser to extract text content from uploaded files.
Supports PDF, CSV, and plain text files.
"""

import csv
import io
from typing import Optional
import pdfplumber


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file, preserving table structure where possible."""
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            # Try to extract tables first (better for leveling guides)
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        # Filter out None values and join cells
                        cells = [str(cell).strip() if cell else "" for cell in row]
                        text_parts.append(" | ".join(cells))
            else:
                # Fall back to regular text extraction
                text = page.extract_text()
                if text:
                    text_parts.append(text)
    
    return "\n".join(text_parts)


def extract_text_from_csv(file_content: bytes) -> str:
    """Extract text from a CSV file, preserving structure."""
    text_parts = []
    
    # Try to decode as UTF-8, fall back to latin-1
    try:
        content = file_content.decode("utf-8")
    except UnicodeDecodeError:
        content = file_content.decode("latin-1")
    
    reader = csv.reader(io.StringIO(content))
    for row in reader:
        text_parts.append(" | ".join(row))
    
    return "\n".join(text_parts)


def extract_text_from_plain(file_content: bytes) -> str:
    """Extract text from a plain text or markdown file."""
    try:
        return file_content.decode("utf-8")
    except UnicodeDecodeError:
        return file_content.decode("latin-1")


def extract_text(file_content: bytes, filename: str) -> str:
    """
    Extract text from an uploaded file based on its extension.
    
    Args:
        file_content: The raw bytes of the uploaded file
        filename: The original filename (used to determine file type)
    
    Returns:
        The extracted text content
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_content)
    elif filename_lower.endswith(".csv"):
        return extract_text_from_csv(file_content)
    elif filename_lower.endswith((".txt", ".md", ".markdown")):
        return extract_text_from_plain(file_content)
    else:
        # Default to plain text extraction
        return extract_text_from_plain(file_content)
