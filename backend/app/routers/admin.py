"""Admin API for resume management."""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
import os
from ..database import get_db, UPLOAD_DIR
from ..models import Resume, SlapCount
from ..schemas import ResumeOut, ResumeList, AdminRequest
from ..utils import extract_pdf_text, normalize_spacing, parse_resume_sections, create_default_resume

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/resumes", response_model=ResumeList)
def list_resumes(db: Session = Depends(get_db)):
    """List all resumes."""
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    return ResumeList(resumes=[ResumeOut.from_orm(r) for r in resumes], total=len(resumes))


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get specific resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeOut.from_orm(resume)


@router.post("/resumes")
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a resume PDF."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    try:
        # Save file
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filepath, "wb") as f:
            f.write(file.file.read())

        # Extract text
        raw_text = extract_pdf_text(filepath)

        # Parse sections
        sections = parse_resume_sections(raw_text)

        # Create default structure
        content = create_default_resume()

        # Update with extracted data
        if "introduction" in sections:
            content["description"]["body"] = normalize_spacing(sections["introduction"])
        if "experience" in sections or "work" in sections:
            body = sections.get("experience") or sections.get("work")
            content["experience"]["body"] = normalize_spacing(body)
        if "project" in sections or "projects" in sections:
            body = sections.get("project") or sections.get("projects")
            content["project"]["body"] = normalize_spacing(body)
        if "education" in sections:
            content["education"]["body"] = normalize_spacing(sections["education"])
        if "skill" in sections or "skills" in sections:
            body = sections.get("skill") or sections.get("skills")
            content["skills"]["body"] = normalize_spacing(body)

        # Save to database
        resume = Resume(filename=file.filename, filepath=filepath, content_json=content)
        db.add(resume)
        db.commit()
        db.refresh(resume)

        return ResumeOut.from_orm(resume)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.put("/resumes/{resume_id}")
def update_resume(resume_id: int, request: AdminRequest, db: Session = Depends(get_db)):
    """Update resume content."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume.content_json = request.content_json
    db.commit()
    db.refresh(resume)

    return ResumeOut.from_orm(resume)


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete file
    try:
        if os.path.exists(resume.filepath):
            os.remove(resume.filepath)
    except Exception as e:
        print(f"Warning: Could not delete file: {e}")

    # Delete from DB
    db.delete(resume)
    db.commit()

    return {"message": "Resume deleted"}


@router.get("/resumes/{resume_id}/pdf")
def download_pdf(resume_id: int, db: Session = Depends(get_db)):
    """Download resume PDF."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not os.path.exists(resume.filepath):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(resume.filepath, media_type="application/pdf", filename=resume.filename)


@router.get("/slaps")
def get_slap_count(db: Session = Depends(get_db)):
    """Get Chiyo slap count."""
    count = db.query(SlapCount).first()
    return {"count": count.count if count else 0}


@router.post("/slaps")
def increment_slap(db: Session = Depends(get_db)):
    """Increment slap count."""
    count = db.query(SlapCount).first()
    if not count:
        count = SlapCount(count=1)
        db.add(count)
    else:
        count.count += 1
    db.commit()
    return {"count": count.count}
