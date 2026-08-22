import os
import shutil
import sys

def export_portfolio():
    print("Exporting static portfolio website...")
    
    # Locate database path. The app writes backend/portfolio.db (see
    # database.py, which resolves ./portfolio.db against uvicorn's cwd of
    # backend/); the resume.db names are older and may exist as empty stubs,
    # so skip any candidate that has no resumes table.
    def _has_resumes(path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        import sqlite3
        try:
            with sqlite3.connect(path) as conn:
                return conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='resumes'"
                ).fetchone() is not None
        except sqlite3.Error:
            return False

    candidates = [
        os.path.join("backend", "portfolio.db"),
        "portfolio.db",
        os.path.join("backend", "resume.db"),
        os.path.join("backend", "app", "resume.db"),
        "resume.db",
    ]
    db_path = next((p for p in candidates if _has_resumes(p)), None)
    if db_path is None:
        print("Error: no database with a 'resumes' table found. Tried: " + ", ".join(candidates))
        return
    print(f"Using database: {db_path}")

    # Add backend directory to system path
    backend_dir = os.path.abspath("backend")
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
        
    try:
        from app.utils import render_portfolio_html
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Connect to Database
        engine = create_engine(f"sqlite:///{db_path}")
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        from app.models import Resume
        # Prioritize primary resume or latest resume
        resume = db.query(Resume).filter(Resume.filename.ilike("%samarth%")).first() or db.query(Resume).order_by(Resume.id.desc()).first()
        if not resume:
            print("No resumes found in the database. Please upload a resume first.")
            db.close()
            return
            
        print(f"Found latest resume: ID {resume.id} | File: {resume.filename}")
        print("Rendering static HTML...")
        
        # Render the HTML using the backend renderer
        html_content = render_portfolio_html(resume.content_json, resume.id)
        db.close()
        
        # Create output directory
        dist_dir = "dist"
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        os.makedirs(dist_dir)
        
        # Adjust links inside the exported HTML (e.g. replace '/api/' paths if needed, or keep them)
        # The download link in exported site points to '/api/resumes/{resume_id}/pdf'.
        # Since this is a static build, they might want the PDF file to be downloaded locally!
        # We can copy the PDF to the dist folder too, and map the link to download the local PDF!
        # This is incredibly smart!
        print("Packaging actual PDF resume...")
        pdf_filename = resume.filename
        pdf_src = os.path.join("backend", "app", "uploads", pdf_filename)
        if not os.path.exists(pdf_src):
            pdf_src = os.path.join("backend", "uploads", pdf_filename)
            
        if os.path.exists(pdf_src):
            shutil.copy(pdf_src, os.path.join(dist_dir, pdf_filename))
            # Replace the link in HTML to point directly to the static PDF file!
            html_content = html_content.replace(f"/api/resumes/{resume.id}/pdf", pdf_filename)
            print(f"Copied PDF resume and linked download button to: {pdf_filename}")
        else:
            print("Warning: Raw PDF resume file not found on disk, skipping copy.")
            
        # Write index.html
        with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Created dist/index.html")
        
        # Copy vectorizer assets
        vectorizer_src = "vectorizer"
        if not os.path.exists(vectorizer_src):
            vectorizer_src = os.path.join("backend", "vectorizer")
            
        if os.path.exists(vectorizer_src):
            shutil.copytree(vectorizer_src, os.path.join(dist_dir, "vectorizer"))
            print("Copied vectorizer SVG background assets to dist/vectorizer/")
        else:
            print("Warning: vectorizer directory not found, background assets might be missing.")

        # Copy Chiyo frames
        chiyo_src = os.path.join("assets", "chiyo")
        if os.path.exists(chiyo_src):
            shutil.copytree(chiyo_src, os.path.join(dist_dir, "assets", "chiyo"))
            print("Copied Chiyo animation frames to dist/assets/chiyo/")
        else:
            print("Warning: assets/chiyo directory not found, Chiyo mode will have no frames.")

        print("\n" + "="*50)
        print("SUCCESS: Static portfolio website generated successfully!")
        print("Output Folder: dist/")
        print("Contents:")
        print("  - dist/index.html (Fully rendered portfolio page)")
        print(f"  - dist/{pdf_filename} (Your actual downloadable PDF resume)")
        print("  - dist/vectorizer/ (SVG graphic background assets)")
        print("="*50)
        print("Deployment Instructions:")
        print("1. Drag and drop the 'dist' folder directly into Netlify Drop (templates.netlify.com/drop) or Vercel.")
        print("2. Or upload 'dist' to GitHub Pages.")
        print("No server or database is required to run the public site!")
        
    except Exception as e:
        print("Error during export process:", e)

if __name__ == "__main__":
    export_portfolio()
