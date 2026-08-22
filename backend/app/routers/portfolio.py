"""Portfolio serving and rendering routes."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Resume
from ..utils import render_portfolio_html

router = APIRouter(prefix="", tags=["portfolio"])


@router.get("/", response_class=HTMLResponse)
def get_portfolio(db: Session = Depends(get_db)):
    """Serve the main portfolio page with latest resume."""
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).first()

    if not resumes:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Portfolio - No Resume</title>
            <style>
                body { font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #f0f0f0; }
                .container { text-align: center; background: white; padding: 40px; border-radius: 8px; }
                h1 { color: #333; }
                p { color: #666; margin: 20px 0; }
                a { display: inline-block; padding: 12px 24px; background: #111; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 No Portfolio Yet</h1>
                <p>Upload a resume to get started</p>
                <a href="/admin">Go to Admin</a>
            </div>
        </body>
        </html>
        """

    html = render_portfolio_html(resumes.content_json, resumes.id)
    return html


@router.get("/resume/{resume_id}", response_class=HTMLResponse)
def get_resume_portfolio(resume_id: int, db: Session = Depends(get_db)):
    """Serve portfolio for specific resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    html = render_portfolio_html(resume.content_json, resume.id)
    return html
