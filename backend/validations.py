"""
Validation module for file uploads and parsed leveling guides.

Contains:
- Text extraction validation
- Parsed structure validation
- Error message sanitization
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas import ParsedLevelingGuide


class ValidationError(Exception):
    """Custom exception for validation failures with user-friendly messages."""
    pass


# Minimum text length for a valid leveling guide
MIN_TEXT_LENGTH = 100

# Minimum required structure
MIN_LEVELS = 1
MIN_COMPETENCIES = 1
MIN_CELLS = 1


def validate_extracted_text(text: str) -> None:
    """
    Validate extracted text from a file.
    
    Args:
        text: The extracted text content
        
    Raises:
        ValidationError: If text is empty or too short
    """
    if not text or not text.strip():
        raise ValidationError("Could not extract text from file. Please ensure the file contains readable text.")
    
    stripped = text.strip()
    if len(stripped) < MIN_TEXT_LENGTH:
        raise ValidationError(
            f"File content too short to be a leveling guide (found {len(stripped)} characters, "
            f"minimum {MIN_TEXT_LENGTH} required)."
        )


def validate_parsed_guide(parsed: "ParsedLevelingGuide") -> None:
    """
    Validate the structure of a parsed leveling guide.
    
    Args:
        parsed: The parsed leveling guide from GPT
        
    Raises:
        ValidationError: If structure is invalid
    """
    levels_count = len(parsed.levels)
    competencies_count = len(parsed.competencies)
    cells_count = len(parsed.cells)
    
    if levels_count < MIN_LEVELS:
        raise ValidationError(
            f"Could not find at least {MIN_LEVELS} levels in the document. "
            f"Found {levels_count}. Please upload a valid leveling guide with multiple levels."
        )
    
    if competencies_count < MIN_COMPETENCIES:
        raise ValidationError(
            f"Could not find any competencies in the document. "
            "Please upload a valid leveling guide with competency columns."
        )
    
    if cells_count < MIN_CELLS:
        raise ValidationError(
            "Could not extract any level/competency content from the document. "
            "Please ensure the file contains a structured leveling guide table."
        )
    
    # Check for completeness (optional warning-level check)
    expected_cells = levels_count * competencies_count
    if cells_count < expected_cells * 0.5:  # Less than 50% coverage
        # This is a warning, not an error - parsing may have missed some cells
        print(
            f"Warning: Parsing may be incomplete. Expected ~{expected_cells} cells, "
            f"found {cells_count}."
        )


def sanitize_error(exception: Exception) -> str:
    """
    Convert an exception to a user-friendly error message.
    
    Args:
        exception: The caught exception
        
    Returns:
        A user-friendly error message string
    """
    error_str = str(exception).lower()
    
    # Pass through ValidationError messages as-is (they're already user-friendly)
    if isinstance(exception, ValidationError):
        return str(exception)
    
    # OpenAI rate limiting
    if "rate limit" in error_str or "rate_limit" in error_str:
        return "Service temporarily busy. Please try again in a few moments."
    
    # OpenAI quota exceeded
    if "quota" in error_str or "insufficient_quota" in error_str:
        return "Service quota exceeded. Please contact support."
    
    # OpenAI API errors
    if "openai" in error_str or "api" in error_str:
        if "timeout" in error_str:
            return "Request timed out. Please try again."
        if "connection" in error_str:
            return "Could not connect to AI service. Please try again."
        return "AI service error. Please try again later."
    
    # JSON parsing errors
    if isinstance(exception, json.JSONDecodeError) or "json" in error_str:
        return "Failed to process file structure. Please try a different file format."
    
    # Database errors
    if "database" in error_str or "sqlalchemy" in error_str or "db" in error_str:
        return "Failed to save results. Please try again."
    
    # File parsing errors
    if "pdf" in error_str or "pdfplumber" in error_str:
        return "Could not read PDF file. Please ensure it's not corrupted or password-protected."
    
    if "csv" in error_str:
        return "Could not read CSV file. Please ensure it's properly formatted."
    
    if "unicode" in error_str or "decode" in error_str:
        return "Could not read file encoding. Please save the file as UTF-8 and try again."
    
    # Generic fallback
    return "An unexpected error occurred. Please try again or contact support."
