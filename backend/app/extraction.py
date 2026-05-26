"""PDF extraction utilities with Groq AI Mapping layer and deterministic fallbacks.

- Uses ``PyMuPDF`` (``fitz``) to extract raw text from a PDF.
- Loads the ``GROQ_API_KEY`` from the ``.env`` file.
- Sends the raw text to the Groq API (using llama-3.3-70b-versatile) to parse it semantically into the structured schema.
- Falls back to a deterministic section-split parsing helper if the Groq API call fails or is unconfigured.
"""

import os
import json
import urllib.request
from typing import Dict, List

# Load .env file manually on import to populate environment variables.
env_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# PyMuPDF (fitz) is the preferred PDF text extractor.
try:
    import fitz  # type: ignore
except ImportError:  # pragma: no cover
    fitz = None


def _extract_raw_text(pdf_path: str) -> str:
    """Extract plain text and embedded hyperlinks from a PDF file using PyMuPDF."""
    if not fitz:
        raise RuntimeError("PyMuPDF (fitz) is required for PDF extraction")
    doc = fitz.open(pdf_path)
    text = []
    hyperlinks = []
    for page in doc:
        text.append(page.get_text())
        links = page.get_links()
        for link in links:
            if link.get("kind") == fitz.LINK_URI:
                uri = link.get("uri")
                rect = fitz.Rect(link.get("from"))
                txt = page.get_text("text", clip=rect).strip().replace("\n", " ")
                if uri:
                    if txt:
                        hyperlinks.append(f'- Link Text "{txt}" points to URL "{uri}"')
                    else:
                        hyperlinks.append(f'- URL "{uri}"')
                        
    full_text = "\n".join(text)
    if hyperlinks:
        full_text += "\n\n[Hyperlinks embedded in PDF document]:\n" + "\n".join(hyperlinks)
    return full_text


def _split_sections_fallback(raw_text: str) -> Dict[str, str]:
    """Fallback section splitter if the AI layer fails.

    Looks for lines that are uppercase as headings.
    """
    sections: Dict[str, List[str]] = {}
    current_heading = "misc"
    sections[current_heading] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.isupper() and len(stripped.split()) <= 3:
            current_heading = stripped.lower()
            sections.setdefault(current_heading, [])
        else:
            sections[current_heading].append(stripped)
    return {k: " ".join(v).strip() for k, v in sections.items()}


def _clean_json_string(s: str) -> str:
    """Removes potential markdown block formatting from JSON responses."""
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _run_groq_extraction(raw_text: str, api_key: str) -> Dict:
    """Invokes the Groq API to convert raw resume text into the structured JSON schema."""
    system_prompt = (
        "You are a precise resume semantic extraction engine.\n"
        "Your task is to extract information from the raw resume text and map it to the requested JSON schema.\n\n"
        "Requested JSON Schema:\n"
        "{\n"
        '  "name": "Full name of the candidate, or null if not found",\n'
        '  "address": "Postal address or location of the candidate, or null if not found",\n'
        '  "email": "Email address, or null if not found",\n'
        '  "number": "Phone number, or null if not found",\n'
        '  "links": ["List of URLs, social profiles, websites, github, linkedin, or empty array"],\n'
        '  "description": {\n'
        '    "headline": "The original heading of the summary/profile section in the resume, or \'Summary\'",\n'
        '    "body": "The text content of the summary/profile section, preserving exact wording"\n'
        "  },\n"
        '  "experience": {\n'
        '    "headline": "The original heading of the experience/employment section, or \'Experience\'",\n'
        '    "body": "The text content of the experience section, preserving exact wording"\n'
        "  },\n"
        '  "project": {\n'
        '    "headline": "The original heading of the projects section, or \'Projects\'",\n'
        '    "body": "The text content of the projects section, preserving exact wording"\n'
        "  },\n"
        '  "education": {\n'
        '    "headline": "The original heading of the education section, or \'Education\'",\n'
        '    "body": "The text content of the education section, preserving exact wording"\n'
        "  },\n"
        '  "skills": {\n'
        '    "headline": "The original heading of the skills section, or \'Skills\'",\n'
        '    "body": "The text content of the skills section, preserving exact wording"\n'
        "  },\n"
        '  "strengths": {\n'
        '    "headline": "The original heading of the strengths/competencies section, or \'Strengths\'",\n'
        '    "body": "The text content of the strengths section, preserving exact wording"\n'
        "  },\n"
        '  "hobbies": {\n'
        '    "headline": "The original heading of the hobbies/interests section, or \'Hobbies\'",\n'
        '    "body": "The text content of the hobbies section, preserving exact wording"\n'
        "  },\n"
        '  "status": {\n'
        '    "headline": "The original heading of any job status/employment status, or \'Employment Status\'",\n'
        '    "body": "The text content of the status details, preserving exact wording"\n'
        "  },\n"
        '  "focus": {\n'
        '    "headline": "The original heading of any focus/specialization details, or \'Career Focus\'",\n'
        '    "body": "The text content of the focus details, preserving exact wording"\n'
        "  },\n"
        '  "availability": {\n'
        '    "headline": "The original heading of any notice period/availability details, or \'Availability\'",\n'
        '    "body": "The text content of availability details, preserving exact wording"\n'
        "  }\n"
        "}\n\n"
        "Strict Extraction Rules:\n"
        "1. NEVER rewrite, paraphrase, summarize, or improve the text.\n"
        "2. Preserve the exact wording, original phrasing, and structure from the resume.\n"
        "3. Return valid JSON only. Do not wrap the JSON in markdown code blocks or add conversational padding.\n"
        "4. If a section or field is missing, set its body to null and headline to the default value. Do not invent info.\n"
        "5. Only extract information that is explicitly present in the provided text.\n"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract raw resume text:\n\n{raw_text}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0
    }

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        data=json.dumps(data).encode("utf-8"),
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=20) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        content = res_data["choices"][0]["message"]["content"]
        cleaned_content = _clean_json_string(content)
        return json.loads(cleaned_content)


def extract_resume(pdf_path: str) -> Dict:
    """Public helper that extracts a resume into the structured JSON schema.

    Triggers Groq AI extraction if GROQ_API_KEY is defined in environment;
    otherwise falls back to deterministic section splitting.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    raw = _extract_raw_text(pdf_path)
    
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            return _run_groq_extraction(raw, api_key)
        except Exception as e:
            print(f"[Warning] Groq AI extraction failed: {e}. Falling back to rule-based parser.")
    
    # Fallback to rule-based split
    sections = _split_sections_fallback(raw)
    return {
        "name": sections.get("name", sections.get("misc", "")[:50].strip()),
        "address": sections.get("location", ""),
        "email": sections.get("email", ""),
        "number": sections.get("phone", ""),
        "links": [sections.get("links", "")] if sections.get("links") else [],
        "description": {"headline": "Profile Summary", "body": sections.get("summary", "")},
        "experience": {"headline": "Experience", "body": sections.get("experience", "")},
        "project": {"headline": "Projects", "body": sections.get("projects", "")},
        "education": {"headline": "Education", "body": sections.get("education", "")},
        "skills": {"headline": "Skills", "body": sections.get("skills", "")},
        "strengths": {"headline": "Strengths", "body": sections.get("strengths", "")},
        "hobbies": {"headline": "Hobbies & Interests", "body": sections.get("hobbies", "")},
        "status": {"headline": "Employment Status", "body": sections.get("status", "")},
        "focus": {"headline": "Career Focus", "body": sections.get("focus", "")},
        "availability": {"headline": "Availability", "body": sections.get("availability", "")}
    }

