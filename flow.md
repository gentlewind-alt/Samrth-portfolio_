Your problem is not primarily “resume parsing.”

It is:

> building a deterministic resume-CMS pipeline with controlled AI extraction.

That distinction matters because most AI resume parsers fail due to:

* uncontrolled generation
* schema drift
* hallucinated summaries
* inconsistent mappings
* loss of formatting intent

Your requirement is much stronger:

> Preserve the structure and semantics of the existing portfolio/resume template while replacing only mapped fields.

That is the correct architecture direction.

---

# Recommended System Architecture

## Core Principle

Do NOT let AI generate the resume.

AI should ONLY:

* classify
* extract
* map
* normalize

The frontend template remains the source of truth.

---

# High-Level Architecture

```txt id="56lk8v"
Frontend Resume Website
        ↓
Resume CMS Backend
        ↓
Structured Resume Schema
        ↓
Parser Layer
(OCR + PDF extraction + AI mapping)
        ↓
Validation Layer
        ↓
Database
        ↓
Resume Renderer
(HTML template replacement)
```

---

# Recommended Stack

## Frontend

* Next.js
* Tailwind
* Static resume template

---

## Backend

Best options:

### Option A (Recommended)

* FastAPI
* PostgreSQL
* Redis
* Celery/RQ queue

Why:

* async-friendly
* strong AI ecosystem
* easy PDF tooling
* scalable extraction pipeline

---

### Option B

* Node.js + NestJS

Good if:

* frontend-heavy ecosystem
* TypeScript-first team

But Python has far better OCR/PDF tooling.

---

# Database Design

You should NOT store resumes as blobs only.

Store:

## 1. Raw Resume File

```txt id="xewukd"
resume.pdf
```

---

## 2. Structured Resume JSON

This is the important part.

Example:

```json id="sdbfya"
{
  "personal": {
    "name": "Samarth Rawat",
    "email": "..."
  },
  "summary": "...",
  "education": [],
  "projects": [],
  "skills": [],
  "experience": []
}
```

This becomes:

* editable
* versionable
* renderable
* AI-compatible

---

# CRITICAL ARCHITECTURE DECISION

## DO NOT PARSE DIRECTLY INTO HTML

Wrong:

```txt id="6yzq26"
PDF → AI → HTML
```

Correct:

```txt id="pql5ma"
PDF → Structured Schema → Template Renderer
```

This prevents:

* hallucinated formatting
* broken layouts
* inconsistent rendering

---

# Recommended Resume Schema

You need strict typing.

Example:

```ts id="od40e4"
type ResumeSchema = {
  personal: {
    name: string
    email: string
    phone: string
    location: string
    github?: string
    linkedin?: string
  }

  summary: string

  education: Education[]

  projects: Project[]

  skills: {
    languages: string[]
    frameworks: string[]
    tools: string[]
  }

  interests: string[]
}
```

---

# Resume Upload Pipeline

# STEP 1 — Upload PDF

Store:

* original PDF
* metadata
* checksum/hash

---

# STEP 2 — Text Extraction

Use:

## Primary

### `PyMuPDF`

Best for:

* structured PDFs
* modern resumes

---

## OCR Fallback

### `Tesseract`

ONLY if:

* scanned PDFs
* image resumes

Do not OCR every PDF.

That wastes resources.

---

# STEP 3 — Layout Segmentation

Extract:

* headings
* sections
* lists
* paragraphs

You want:

```txt id="q07byq"
"Projects"
"Education"
"Skills"
```

before AI mapping.

This dramatically reduces token usage.

---

# STEP 4 — AI Mapping Layer

THIS is where AI should be used.

NOT for rewriting.

Only for:

* section classification
* field mapping
* ambiguity resolution

---

# VERY IMPORTANT AI RULE

Your system prompt must enforce:

```txt id="7n8pbv"
NEVER rewrite content.
NEVER summarize.
NEVER improve grammar.
ONLY extract exact semantic information.
Maintain original phrasing.
```

---

# Best AI Strategy

## Hybrid Extraction

Use:

* regex
* deterministic parsing
* embeddings
* AI fallback

NOT:

```txt id="exk0wr"
send full PDF to GPT
```

That is:

* expensive
* unreliable
* slow

---

# Better Pipeline

```txt id="4y8c50"
PDF
↓
Text Extraction
↓
Section Detection
↓
Rule-based parsing
↓
AI fallback for unknown sections
↓
Schema validation
```

---

# Example

## Deterministic Parsing

```txt id="0y4l56"
Skills:
Python, C++, TensorFlow
```

No AI needed.

---

## AI Needed

```txt id="y82bdw"
Built a distributed low-latency embedded interaction system...
```

AI maps this to:

```json id="xtm9vd"
{
  "project_type": "embedded_system",
  "technologies": [...]
}
```

---

# Token Optimization Strategy

This is where most systems fail badly.

---

# NEVER Send Full Resume

Bad:

```txt id="rf7s8z"
12 pages → GPT
```

Good:

```txt id="z2br6k"
Extract only ambiguous sections
```

---

# Use Chunking

Chunk by:

* section
* heading
* paragraph

NOT arbitrary token chunks.

---

# Use Deterministic Extraction First

You can extract:

* emails
* phones
* dates
* URLs
* skills

without AI.

This can reduce AI usage by:

```txt id="z9ldj7"
70–90%
```

---

# Use Small Models First

Recommended hierarchy:

## Tier 1

Regex + parser

## Tier 2

Mini model

* GPT-4.1 Mini
* Claude Haiku
* Gemini Flash

## Tier 3

Full model ONLY if ambiguity exists

---

# Cache Parsed Results

Hash:

```txt id="4hr0st"
SHA256(pdf)
```

If same file uploaded:

* reuse extraction
* reuse embeddings
* skip AI

Huge savings.

---

# Use Embeddings For Matching

Store section embeddings.

Example:

```txt id="w2rb5n"
"Professional Experience"
≈
"Work History"
≈
"Employment"
```

This avoids expensive classification prompts.

---

# User Verification Layer

VERY important.

AI extraction must NEVER directly publish.

Pipeline:

```txt id="o67yfk"
AI Extraction
↓
Draft Resume
↓
Editable Review UI
↓
Approve
↓
Publish
```

---

# UI Recommendation

Show:

| Original Resume | Extracted Fields |
| --------------- | ---------------- |
| left            | right            |

Allow:

* inline edits
* confidence indicators
* field locking

---

# Resume Rendering System

DO NOT use string replace.

Use:

* template engine
* component renderer

Example:

```txt id="n7hrm7"
resumeData.projects.map(...)
```

This keeps:

* design integrity
* predictable rendering

---

# Recommended AI Prompt Strategy

## Bad Prompt

```txt id="d4ev4e"
Extract resume info
```

---

## Good Prompt

```txt id="bfb3wl"
You are a resume extraction engine.

Rules:
- Never rewrite content.
- Preserve exact wording.
- Return valid JSON only.
- Follow schema exactly.
- Missing fields must be null.
- Never infer information not present.
```

---

# Biggest Risk In Your System

## Hallucinated Resume Data

AI may:

* invent skills
* rewrite summaries
* alter dates
* merge projects

You MUST validate.

---

# Validation Layer

Use:

* Pydantic
* Zod
* JSON schema validation

Reject:

* malformed structures
* impossible dates
* invented fields

---

# Production-Level Upgrade

## Resume Versioning

Store:

```txt id="f8qzba"
resume_v1
resume_v2
resume_v3
```

This enables:

* rollback
* diffing
* history

---

# Best Long-Term Architecture

Eventually your system becomes:

```txt id="s3wn61"
Resume CMS
+
Portfolio Generator
+
Structured Career Database
+
AI-assisted Editing Pipeline
```

That is much more scalable than:

> “resume uploader.”

---

# Recommended MVP

## Phase 1

* upload PDF
* extract text
* manual mapping UI

NO AI yet.

---

## Phase 2

* AI section detection
* schema filling
* verification UI

---

## Phase 3

* multi-template rendering
* versioning
* export systems
* AI optimization

---

# Best Overall Approach

The strongest architecture is:

```txt id="0sd8gv"
Deterministic extraction first
AI only for ambiguity
Strict schema validation
Human verification before publish
Template-driven rendering
```

That gives:

* low token cost
* predictable output
* scalable architecture
* maintainable system
* production reliability

instead of:

> “LLM magic parser.”
