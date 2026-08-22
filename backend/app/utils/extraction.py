"""PDF extraction and resume parsing utilities."""
import os
import json
from typing import Dict
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
        text = []
        for page in doc:
            text.append(page.get_text())
        doc.close()
        return "\n".join(text)
    except Exception as e:
        raise Exception(f"Failed to extract PDF: {str(e)}")


def normalize_spacing(text: str) -> str:
    """Normalize spacing: remove excess whitespace."""
    if not text:
        return ""
    # Replace multiple spaces with single space
    text = " ".join(text.split())
    return text.strip()


def parse_resume_sections(text: str) -> Dict[str, str]:
    """Parse resume text into sections using rule-based approach."""
    sections: Dict[str, list] = {}
    current_section = "introduction"
    sections[current_section] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line is a section header (uppercase, short)
        if stripped.isupper() and 2 <= len(stripped.split()) <= 4:
            current_section = stripped.lower().replace(" ", "_")
            sections[current_section] = []
        else:
            sections[current_section].append(stripped)

    # Join and normalize
    result = {}
    for section, lines in sections.items():
        if lines:
            # Join lines, preserve paragraph breaks
            content = "\n\n".join([normalize_spacing(" ".join(chunk)) for chunk in
                                   [lines[i:i + 5] for i in range(0, len(lines), 5)] if chunk])
            result[section] = content
        else:
            result[section] = ""

    return result


def create_default_resume() -> Dict:
    """Create a default resume structure."""
    return {
        "name": "Your Name",
        "address": "City, Country",
        "email": "your.email@example.com",
        "number": "+1 (000) 000-0000",
        "links": [],
        "description": {"headline": "Profile Summary", "body": ""},
        "experience": {"headline": "Work Experience", "body": ""},
        "project": {"headline": "Key Projects", "body": ""},
        "education": {"headline": "Academic Education", "body": ""},
        "skills": {"headline": "Core Skills", "body": ""},
        "strengths": {"headline": "Strengths", "body": ""},
        "hobbies": {"headline": "Hobbies & Interests", "body": ""},
        "status": {"headline": "Employment Status", "body": ""},
        "focus": {"headline": "Career Focus", "body": ""},
        "availability": {"headline": "Availability", "body": ""}
    }
