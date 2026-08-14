"""FastAPI router exposing resume endpoints.

Endpoints:
- POST /resumes/          -> upload PDF (stores file, creates DB entry with empty JSON)
- GET  /resumes/          -> list all resumes (id, filename, timestamps)
- GET  /resumes/{id}       -> retrieve a single resume's JSON data

Future: POST /resumes/{id}/parse to trigger OCR/AI mapping.
"""

import os
import re
import shutil
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from . import models, schemas, dependencies

router = APIRouter()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))

@router.post("/resumes/", response_model=schemas.ResumeOut)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(dependencies.get_db)):
    # Save uploaded file securely
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Extract structured data from the PDF (stub implementation)
    from . import extraction
    try:
        extracted = extraction.extract_resume(file_location)
    except Exception as e:
        # If extraction fails, store an empty dict and continue – the API remains usable
        extracted = {}
    # Create DB entry with the extracted JSON (or empty if extraction failed)
    db_resume = models.Resume(filename=file.filename, content_json=extracted)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return schemas.ResumeOut.from_orm(db_resume)

@router.get("/resumes/", response_model=list[schemas.ResumeOut])
def list_resumes(db: Session = Depends(dependencies.get_db)):
    resumes = db.query(models.Resume).all()
    return [schemas.ResumeOut.from_orm(r) for r in resumes]

@router.get("/resumes/{resume_id}", response_model=schemas.ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(dependencies.get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return schemas.ResumeOut.from_orm(resume)

@router.get("/resumes/{resume_id}/pdf")
@router.get("/api/resumes/{resume_id}/pdf")
def get_resume_pdf(resume_id: int, db: Session = Depends(dependencies.get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    file_path = os.path.join(UPLOAD_DIR, resume.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    from fastapi.responses import FileResponse
    return FileResponse(file_path, media_type="application/pdf")

def run_auto_deploy(resume_id: int):
    import shutil
    import subprocess
    import urllib.request
    
    try:
        from .dependencies import SessionLocal
        db = SessionLocal()
        try:
            from .models import Resume
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                print(f"[Auto-Deploy] Resume {resume_id} not found in database.")
                return
            pdf_filename = resume.filename
            
            # Render the HTML using the backend router function directly
            response = render_resume_html(resume_id, db)
            html_content = response.body.decode("utf-8")
        finally:
            db.close()
            
        # Create output directory
        dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist"))
        os.makedirs(dist_dir, exist_ok=True)
        
        # Packaging actual PDF resume
        pdf_src = os.path.join(UPLOAD_DIR, pdf_filename)
        if os.path.exists(pdf_src):
            shutil.copy(pdf_src, os.path.join(dist_dir, pdf_filename))
            # Replace the link in index.html to point to local PDF
            html_content = html_content.replace(f"/api/resumes/{resume_id}/pdf", pdf_filename)
            print(f"[Auto-Deploy] Copied PDF resume and linked download button to: {pdf_filename}")
        else:
            print("[Auto-Deploy] Warning: Raw PDF resume file not found on disk, skipping copy.")
            
        # Write index.html
        with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        print("[Auto-Deploy] Created dist/index.html")
        
        # Copy vectorizer assets
        vectorizer_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "vectorizer"))
        vectorizer_dst = os.path.join(dist_dir, "vectorizer")
        if os.path.exists(vectorizer_src):
            if os.path.exists(vectorizer_dst):
                shutil.rmtree(vectorizer_dst)
            shutil.copytree(vectorizer_src, vectorizer_dst)
            print("[Auto-Deploy] Copied vectorizer SVG background assets to dist/vectorizer/")
            
        # Check for Git Auto Push
        auto_git = os.environ.get("AUTO_GIT_PUSH", "false").lower() == "true"
        if auto_git:
            print("[Auto-Deploy] Triggering Git push...")
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
            # Staging and committing static files
            subprocess.run(["git", "add", "dist/"], cwd=root_dir)
            subprocess.run(["git", "commit", "-m", "CMS: Auto-update resume static assets"], cwd=root_dir)
            
            # Dynamically determine the active branch name (main or master)
            branch_result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root_dir, capture_output=True, text=True)
            active_branch = branch_result.stdout.strip() or "main"
            
            # Explicitly push the active branch
            subprocess.run(["git", "push", "origin", active_branch], cwd=root_dir)
            print(f"[Auto-Deploy] Git push to {active_branch} completed.")
            
        # Check for Vercel Deploy Hook
        deploy_hook = os.environ.get("VERCEL_DEPLOY_HOOK_URL")
        if deploy_hook:
            print("[Auto-Deploy] Triggering Vercel Deploy Hook...")
            req = urllib.request.Request(deploy_hook, method="POST")
            with urllib.request.urlopen(req) as resp:
                print(f"[Auto-Deploy] Vercel Deploy Hook triggered: {resp.status}")
                
    except Exception as e:
        print(f"[Auto-Deploy] Error during background rebuild/deploy: {e}")

@router.put("/resumes/{resume_id}", response_model=schemas.ResumeOut)
def update_resume(resume_id: int, updated_content: dict, background_tasks: BackgroundTasks, db: Session = Depends(dependencies.get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    resume.content_json = updated_content
    db.commit()
    db.refresh(resume)
    
    # Trigger auto-deploy and static build in the background
    background_tasks.add_task(run_auto_deploy, resume.id)
    
    return schemas.ResumeOut.from_orm(resume)

@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(dependencies.get_db)):
    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    file_path = os.path.join(UPLOAD_DIR, resume.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[Warning] Failed to delete file {file_path}: {e}")
    db.delete(resume)
    db.commit()
    return {"message": "Resume successfully deleted"}


def get_hobby_icon(label: str) -> str:
    label_lower = label.lower()
    if any(w in label_lower for w in ["read", "book", "novel", "literature"]):
        return "menu_book"
    if any(w in label_lower for w in ["movie", "film", "cinema", "show", "watch"]):
        return "movie_filter"
    if any(w in label_lower for w in ["podcast", "story", "stories", "listen", "audio"]):
        return "podcasts"
    if any(w in label_lower for w in ["build", "innovat", "invent", "creat", "maker", "embed"]):
        return "precision_manufacturing"
    if any(w in label_lower for w in ["music", "song", "singing", "headset", "headphone"]):
        return "headset"
    if any(w in label_lower for w in ["cook", "restaurant", "food", "chef", "bake"]):
        return "restaurant"
    if any(w in label_lower for w in ["sport", "basketball", "football", "cricket", "game", "gaming"]):
        return "sports_basketball"
    if any(w in label_lower for w in ["code", "program", "develop", "tech"]):
        return "code"
    if any(w in label_lower for w in ["travel", "explore", "hike", "hiking"]):
        return "explore"
    if any(w in label_lower for w in ["paint", "art", "draw", "palette", "design"]):
        return "palette"
    if any(w in label_lower for w in ["fit", "gym", "work", "exercise", "run"]):
        return "fitness_center"
    if any(w in label_lower for w in ["learn", "study", "psychology", "think"]):
        return "psychology"
    return "star"

def bullet_description(desc: str) -> str:
    if not desc:
        return ""
    
    # Standardize whitespace and remove any existing HTML line breaks
    desc_clean = desc.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    
    raw_lines = []
    lines = [l.strip() for l in desc_clean.split("\n") if l.strip()]
    is_bullet_list = len(lines) > 1 or any(l.startswith(("•", "-", "*")) for l in lines)
    
    if is_bullet_list:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove any leading bullet points/markers (•, -, *)
            if line.startswith("•") or line.startswith("-") or line.startswith("*"):
                line = line[1:].strip()
            if line:
                raw_lines.append(line)
    else:
        # If it is a single block, split it into sentences
        for s in desc_clean.split(". "):
            s = s.strip()
            if not s:
                continue
            if not s.endswith((".", "!", "?")):
                s += "."
            # If sentence is very short, merge it with the last sentence
            if len(s) < 15 and raw_lines:
                raw_lines[-1] += " " + s
            else:
                raw_lines.append(s)
                
    # Restrict to maximum of 2 bullets to ensure they take up the same pixel space
    final_lines = raw_lines[:2]
    
    bulleted = []
    for s in final_lines:
        s = s.strip()
        if s:
            # Truncate to a max of 95 characters to keep it compact and single/double-line
            max_len = 95
            if len(s) > max_len:
                truncated = s[:max_len-3].rsplit(" ", 1)[0]
                if len(truncated) > 0:
                    s = truncated + "..."
                else:
                    s = s[:max_len-3] + "..."
            bulleted.append(f"• {s}")
            
    return "<br>".join(bulleted)

def process_hobbies(hobbies_list: list) -> list:
    new_hobbies = []
    seen = set()
    for h in hobbies_list:
        label = h.get("label") or ""
        # If label contains a comma, split it!
        if "," in label:
            parts = [p.strip() for p in label.split(",") if p.strip()]
            for part in parts:
                if part.lower() not in seen:
                    icon = get_hobby_icon(part)
                    new_hobbies.append({"icon": icon, "label": part})
                    seen.add(part.lower())
        else:
            if label.strip() and label.strip().lower() not in seen:
                icon = h.get("icon") or get_hobby_icon(label)
                if icon == "star":
                    icon = get_hobby_icon(label)
                new_hobbies.append({"icon": icon, "label": label.strip()})
                seen.add(label.strip().lower())
    return new_hobbies


@router.get("/resumes/{resume_id}/render")
@router.get("/api/resumes/{resume_id}/render")
def render_resume_html(resume_id: int, db: Session = Depends(dependencies.get_db)):
    # Load .env file manually
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    if not os.path.exists(env_path):
        env_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

    resume = db.query(models.Resume).filter(models.Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    template_path = os.path.abspath(os.path.join(UPLOAD_DIR, "..", "..", "Samarthrawat_resume.html"))
    if not os.path.exists(template_path):
        template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Samarthrawat_resume.html"))
        
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="HTML template file Samarthrawat_resume.html not found.")
        
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    api_key = os.environ.get("GROQ_API_KEY")
    structured_data = None
    
    # If API key is available, use Groq to map content to structured JSON
    if api_key:
        import urllib.request
        import json
        system_prompt = (
            "You are a professional resume details structuring assistant.\n"
            "Your task is to take the candidate's JSON resume details and map them to a structured JSON schema. This schema will be used to inject the content into a locked visual portfolio template.\n\n"
            "Strict rules:\n"
            "1. Preserve the exact content, technologies, and achievements from the candidate data.\n"
            "2. Map section headlines to the appropriate keys.\n"
            "3. For the 'hobbies' list, choose a relevant Google Material Icon name from: 'menu_book', 'movie_filter', 'psychology', 'precision_manufacturing', 'podcasts', 'headset', 'restaurant', 'sports_basketball', 'code', 'explore', 'palette', 'fitness_center'.\n"
            "4. For the 'stack_overview', create exactly 4 items summarizing their skillset, choosing a relevant icon from the list above or 'psychology', 'memory', 'terminal', 'webhook'.\n"
            "5. Return ONLY a valid JSON object matching the schema. Do not include markdown code block formatting or explanation.\n"
            "6. For each project in the 'projects' list, you MUST summarize and rewrite the description into exactly 2 extremely concise, short bullet points (maximum 10-12 words per bullet point). Each bullet point must start with a bullet character '•' and a space, and be separated by a newline character (\\n). Keep the descriptions uniform and brief to fit identical card sizes.\n"
            "7. For the 'hobbies' list, if any hobby label or category contains a comma (e.g. 'Listening to stories, podcasts' or 'Building, innovating'), you MUST split it by the comma into separate, individual hobby items. Each resulting item must have its own separate JSON object in the list with a relevant Material Icon (do not group them in a single string with a comma).\n\n"
            "JSON Schema Requirements:\n"
            "{\n"
            '  "short_name": "First initial + last name uppercase (e.g. \'S. RAWAT\')",\n'
            '  "short_title": "Short title uppercase (e.g. \'AI SYSTEMS ENG.\')",\n'
            '  "hero_tracking": "Professional role/field uppercase (e.g. \'APPLIED AI SYSTEMS ENGINEER\')",\n'
            '  "first_name": "First name uppercase (e.g. \'SAMARTH\')",\n'
            '  "last_name": "Last name uppercase (e.g. \'RAWAT\')",\n'
            '  "hero_taglines": ["Up to 4 short taglines/focus areas (e.g. \'Embedded Intelligence\')"],\n'
            '  "status_text": "A brief, inspiring sentence about what they build/do.",\n'
            '  "location": "Location (e.g. \'Bhubaneswar, India\')",\n'
            '  "current_focus": "Current focus areas (e.g. \'Agentic AI • Embedded Systems\')",\n'
            '  "availability": "Notice period or availability (e.g. \'Open to Opportunities\')",\n'
            '  "stack_overview": [\n'
            '     {"icon": "Material icon name", "title": "Stack title", "description": "Short tools/details string"}\n'
            '  ], (exactly 4 items)\n'
            '  "projects": [\n'
            '     {"title": "Project title uppercase", "subtitle": "Category", "status": "Completed/Prototype", "tags": ["Tech1", "Tech2"], "description": "Brief description"}\n'
            '  ],\n'
            '  "about_me": "Summary paragraph",\n'
            '  "metrics": [\n'
            '     {"icon": "Icon name", "label": "Metric name (e.g. CGPA, Projects)", "value": "Value string"}\n'
            '  ], (exactly 4 items)\n'
            '  "skills": [\n'
            '     {"category": "Category", "skills": ["Skill1", "Skill2"]}\n'
            '  ],\n'
            '  "education_and_experience": [\n'
            '     {"years": "Years active", "school": "Institution / Employer", "degree_gpa": "Degree or Role details"}\n'
            '  ],\n'
            '  "hobbies": [\n'
            '     {"icon": "Icon name", "label": "Hobby label"}\n'
            '  ],\n'
            '  "interests": ["Up to 4 interests"],\n'
            '  "strengths": ["Up to 4 strengths"],\n'
            '  "email": "Email address",\n'
            '  "phone": "Phone number",\n'
            '  "address": "Full address location",\n'
            '  "github_url": "GitHub URL or \'#\'",\n'
            '  "linkedin_url": "LinkedIn URL or \'#\'",\n'
            '  "quote": "Inspiring personal quote/philosophy"\n'
            "}"
        )
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Candidate details:\n{json.dumps(resume.content_json, indent=2)}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps(data).encode("utf-8"),
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"].strip()
                structured_data = json.loads(content)
        except Exception as e:
            print(f"[Warning] Groq structuring call failed: {e}. Using deterministic fallback.")
            
    # Deterministic fallback parser
    if not structured_data:
        import json
        content = resume.content_json or {}
        name = content.get("name") or "Samarth Rawat"
        email = content.get("email") or "samarthrawat10@email.com"
        phone = content.get("number") or "+91 8984100922"
        address = content.get("address") or "Odisha, India"
        
        # Split names
        name_parts = name.split()
        first_name = name_parts[0].upper() if name_parts else "SAMARTH"
        last_name = " ".join(name_parts[1:]).upper() if len(name_parts) > 1 else "RAWAT"
        short_name = f"{first_name[0]}. {last_name}" if first_name else last_name
        
        # Links
        links = content.get("links") or []
        github_url = "#"
        linkedin_url = "#"
        for link in links:
            if "github.com" in link.lower():
                github_url = link
            elif "linkedin.com" in link.lower():
                linkedin_url = link
                
        # Description
        desc_headline = content.get("description", {}).get("headline") or "About Me"
        desc_body = content.get("description", {}).get("body") or "Applied AI developer specializing in building intelligent systems."
        
        # Skills
        skills_headline = content.get("skills", {}).get("headline") or "Technical Skills"
        skills_body = content.get("skills", {}).get("body") or ""
        skills_list = []
        if skills_body:
            lines = [l.strip() for l in skills_body.split("\n") if l.strip()]
            for line in lines:
                if ":" in line:
                    cat, items = line.split(":", 1)
                    skills_list.append({
                        "category": cat.strip(),
                        "skills": [i.strip() for i in items.split(",") if i.strip()]
                    })
                else:
                    skills_list.append({
                        "category": "Skills",
                        "skills": [i.strip() for i in line.split(",") if i.strip()]
                    })
        else:
            skills_list = [
                {"category": "Programming", "skills": ["Python", "Java", "C", "HTML/CSS"]},
                {"category": "Databases", "skills": ["MySQL"]},
                {"category": "Tools", "skills": ["Git", "VS Code", "Power BI"]}
            ]
            
        # Projects
        proj_headline = content.get("project", {}).get("headline") or "Projects"
        proj_body = content.get("project", {}).get("body") or ""
        projects_list = []
        if proj_body:
            blocks = [b.strip() for b in proj_body.split("\n\n") if b.strip()]
            for block in blocks:
                lines = [l.strip() for l in block.split("\n") if l.strip()]
                title_line = lines[0] if lines else "Project Title"
                title = title_line
                subtitle = "Engineering System"
                if "(" in title_line and title_line.endswith(")"):
                    title, tech_part = title_line.split("(", 1)
                    title = title.strip()
                    subtitle = tech_part.rstrip(")").strip()
                description = " ".join([l.lstrip("•- ").strip() for l in lines[1:]]) if len(lines) > 1 else ""
                projects_list.append({
                    "title": title.upper(),
                    "subtitle": subtitle,
                    "status": "Completed",
                    "tags": [t.strip() for t in subtitle.split(",") if t.strip()][:4],
                    "description": description
                })
        else:
            projects_list = [
                {
                    "title": "CRITIC-OS",
                    "subtitle": "AI Music Critique System",
                    "status": "Completed",
                    "tags": ["Python", "Flask", "Groq", "Redis"],
                    "description": "AI-driven web app that generates satirical music critiques using Spotify API."
                }
            ]
            
        # Education & Experience
        edu_headline = content.get("education", {}).get("headline") or "Education"
        edu_body = content.get("education", {}).get("body") or ""
        timeline_list = []
        if edu_body:
            lines = [l.strip() for l in edu_body.split("\n") if l.strip()]
            i = 0
            while i < len(lines):
                school = lines[i]
                years = "2022 — 2026"
                degree = "B.Tech"
                if i + 1 < len(lines):
                    if "-" in lines[i+1] or "20" in lines[i+1] or "–" in lines[i+1]:
                        years = lines[i+1]
                        if i + 2 < len(lines):
                            degree = lines[i+2]
                            i += 3
                        else:
                            i += 2
                    else:
                        degree = lines[i+1]
                        i += 2
                else:
                    i += 1
                timeline_list.append({
                    "years": years,
                    "school": school,
                    "degree_gpa": degree
                })
        else:
            timeline_list = [
                {"years": "2022 — 2026", "school": "KIIT, Bhubaneswar", "degree_gpa": "B.Tech IT • CGPA: 8.24"}
            ]
            
        # Hobbies
        hobbies_headline = content.get("hobbies", {}).get("headline") or "Hobbies"
        hobbies_body = content.get("hobbies", {}).get("body") or ""
        hobbies_list = []
        if hobbies_body:
            items = [i.strip() for i in hobbies_body.split(",") if i.strip()]
            for item in items:
                hobbies_list.append({"icon": "star", "label": item})
        else:
            hobbies_list = [{"icon": "menu_book", "label": "Reading"}, {"icon": "movie_filter", "label": "Movies"}]
            
        # Interests / Strengths
        int_headline = content.get("interests", {}).get("headline") or "Interests"
        int_body = content.get("interests", {}).get("body") or ""
        interests_list = [i.strip() for i in int_body.split(",") if i.strip()] if int_body else ["Agentic AI", "HCI"]
        
        str_headline = content.get("strengths", {}).get("headline") or "Strengths"
        str_body = content.get("strengths", {}).get("body") or ""
        strengths_list = [s.strip() for s in str_body.split("\n") if s.strip()] if str_body else ["Scalable system design"]
        
        structured_data = {
            "short_name": short_name,
            "short_title": content.get("focus", {}).get("body", "SOFTWARE ENGINEER")[:20].upper(),
            "hero_tracking": content.get("focus", {}).get("body", "SOFTWARE ENGINEER").upper(),
            "first_name": first_name,
            "last_name": last_name,
            "hero_taglines": ["Embedded Intelligence", "Agentic Systems"],
            "status_text": content.get("status", {}).get("body") or "Building solutions using technology.",
            "location": address,
            "current_focus": content.get("focus", {}).get("body") or "Software Engineering",
            "availability": content.get("availability", {}).get("body") or "Open to Opportunities",
            "stack_overview": [
                {"icon": "terminal", "title": "DEVELOPMENT", "description": "Full-stack development tools"},
                {"icon": "neurology", "title": "INTELLIGENCE", "description": "Machine Learning and AI integration"},
                {"icon": "memory", "title": "SYSTEMS", "description": "Embedded and real-time systems"},
                {"icon": "webhook", "title": "PHILOSOPHY", "description": "Scalable design principles"}
            ],
            "projects": projects_list,
            "about_me": desc_body,
            "metrics": [
                {"icon": "school", "label": "Education", "value": "B.Tech"},
                {"icon": "rocket_launch", "label": "Projects", "value": f"{len(projects_list)}+"},
                {"icon": "dataset", "label": "Skills", "value": f"{len(skills_list)} Domains"},
                {"icon": "speed", "label": "Availability", "value": "Active"}
            ],
            "skills": skills_list,
            "education_and_experience": timeline_list,
            "hobbies": hobbies_list,
            "interests": interests_list,
            "strengths": strengths_list,
            "email": email,
            "phone": phone,
            "address": address,
            "github_url": github_url,
            "linkedin_url": linkedin_url,
            "quote": "Building systems that understand, adapt and connect."
        }

    # Clean and process projects and hobbies
    if structured_data:
        if "projects" in structured_data and isinstance(structured_data["projects"], list):
            for p in structured_data["projects"]:
                if isinstance(p, dict) and "description" in p:
                    p["description"] = bullet_description(p["description"])
                    
        if "hobbies" in structured_data and isinstance(structured_data["hobbies"], list):
            structured_data["hobbies"] = process_hobbies(structured_data["hobbies"])

    def clean_none_values(obj):
        if isinstance(obj, dict):
            return {k: clean_none_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_none_values(x) for x in obj]
        elif obj is None or obj == "None" or obj == "null":
            return ""
        elif isinstance(obj, str) and obj.strip().upper() in ["N/A", "NA", "N.A.", "NOT APPLICABLE", "N / A"]:
            return ""
        else:
            return obj

    structured_data = clean_none_values(structured_data)

    # Extract all structured fields to build component HTMLs
    s = structured_data
    
    # 1. Candidate names and titles
    raw_name = resume.content_json.get("name") if (resume.content_json and isinstance(resume.content_json, dict)) else ""
    if raw_name:
        parts = raw_name.strip().split()
        first_name = parts[0] if parts else "SAMARTH"
        last_name = " ".join(parts[1:]) if len(parts) > 1 else "RAWAT"
    else:
        first_name = s.get("first_name", "SAMARTH")
        last_name = s.get("last_name", "RAWAT")

    first_letter = first_name[0].upper() if first_name else "S"
    last_upper = last_name.split()[-1].upper() if last_name else "RAWAT"
    short_name = s.get("short_name") or f"{first_letter}. {last_upper}"
    short_title = s.get("short_title", "APPLIED AI · EMBEDDED")
    hero_tracking = s.get("hero_tracking", "APPLIED AI SYSTEMS ENGINEER")
    
    # 2. Hero and Profile descriptions
    desc_content = resume.content_json.get("description", {}) if (resume.content_json and isinstance(resume.content_json, dict)) else {}
    if isinstance(desc_content, dict):
        raw_desc = desc_content.get("body") or ""
    elif isinstance(desc_content, str):
        raw_desc = desc_content
    else:
        raw_desc = ""

    about_me = raw_desc or s.get("about_me") or "I build AI-driven applications and embedded systems — from real-time LLM products to firmware running on 400KB of RAM. Available for freelance work."
    
    # Split about me into two paragraphs if possible
    about_paragraphs = [p.strip() for p in about_me.split("\n\n") if p.strip()]
    if not about_paragraphs:
        about_paragraphs = [p.strip() for p in about_me.split("\n") if p.strip()]
    if len(about_paragraphs) == 1 and len(about_paragraphs[0]) > 140:
        # Split roughly by sentence
        sentences = [sent.strip() + "." for sent in about_paragraphs[0].split(". ") if sent.strip()]
        mid_idx = max(1, len(sentences) // 2)
        p1 = " ".join(sentences[:mid_idx]).rstrip(".") + "."
        p2 = " ".join(sentences[mid_idx:]).rstrip(".") + "." if len(sentences) > mid_idx else ""
    elif len(about_paragraphs) >= 2:
        p1 = about_paragraphs[0]
        p2 = " ".join(about_paragraphs[1:])
    else:
        p1 = about_me
        p2 = ""

    # 3. Location, focus, status
    loc = s.get("location") or (resume.content_json.get("address") if isinstance(resume.content_json, dict) else "") or "Bhubaneswar, Odisha, India"
    curr_focus = s.get("current_focus") or "Agentic AI · Embedded Systems"
    
    # 4. Contact details
    email = s.get("email") or (resume.content_json.get("email") if isinstance(resume.content_json, dict) else "") or "samarthrawat18@email.com"
    phone = s.get("phone") or (resume.content_json.get("number") if isinstance(resume.content_json, dict) else "") or "+91 8984100922"
    address = s.get("address") or loc
    github_url = s.get("github_url", "#")
    linkedin_url = s.get("linkedin_url", "#")
    
    if isinstance(resume.content_json, dict) and "links" in resume.content_json:
        raw_links = resume.content_json["links"]
        if isinstance(raw_links, str):
            raw_links = [l.strip() for l in raw_links.split(",") if l.strip()]
        if isinstance(raw_links, list):
            for link in raw_links:
                if "github.com" in link.lower():
                    github_url = link
                elif "linkedin.com" in link.lower():
                    linkedin_url = link

    # 5. Build Technical Stack Rows HTML
    skills_raw = s.get("skills", [])
    if skills_raw:
        skills_html = ""
        for idx, item in enumerate(skills_raw):
            cat = item.get("category", "Skills")
            s_list = item.get("skills", [])
            skills_str = ", ".join(s_list) if isinstance(s_list, list) else str(s_list)
            border_style = ' style="border-bottom:1px solid #c4c7c7"' if idx == len(skills_raw) - 1 else ''
            skills_html += f"""              <div class="stack-row"{border_style}>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#8a8d8d">{cat}</span>
                <span style="font-size:14px;line-height:1.5;color:#1a1c19">{skills_str}</span>
              </div>\n"""
    else:
        skills_html = None

    # 6. Build Education Timeline HTML
    edu_raw = s.get("education_and_experience", [])
    if edu_raw:
        edu_html = '<div style="position:absolute;left:3px;top:6px;bottom:6px;width:1px;background:#c4c7c7"></div>\n'
        for idx, item in enumerate(edu_raw):
            accent_color = "var(--accent)" if idx == 0 else "#c4c7c7"
            years = item.get("years", "")
            school = item.get("school", "")
            degree = item.get("degree_gpa", "")
            pad_style = ' style="position:relative"' if idx == len(edu_raw) - 1 else ' style="position:relative;padding-bottom:26px"'
            edu_html += f"""            <div{pad_style}>
              <div style="position:absolute;left:-26px;top:5px;width:7px;height:7px;border-radius:9999px;background:{accent_color}"></div>
              <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;color:#8a8d8d;margin:0 0 5px 0">{years}</p>
              <h4 style="font-family:Bitter,serif;font-size:17px;font-weight:500;line-height:1.3;margin:0 0 3px 0">{school}</h4>
              <p style="font-size:13px;color:#444748;margin:0">{degree}</p>
            </div>\n"""
    else:
        edu_html = None

    # 7. Build Interests Pills HTML
    interests_raw = s.get("interests", [])
    if interests_raw:
        interests_html = "".join([f'            <span class="interest-tag">{interest.strip()}</span>\n' for interest in interests_raw if interest and interest.strip()])
    else:
        interests_html = None

    # 8. Build Strengths HTML
    strengths_raw = s.get("strengths", [])
    if strengths_raw:
        strengths_html = "".join([f'            <p style="font-size:13px;line-height:1.65;color:#444748;margin:0;text-wrap:pretty">{st.lstrip("•- ").strip()}</p>\n' for st in strengths_raw if st and st.strip()])
    else:
        strengths_html = None

    # 9. Build Hobbies Badges HTML
    hobbies_raw = s.get("hobbies", [])
    if hobbies_raw:
        hobbies_html = ""
        for h in hobbies_raw:
            icon = h.get("icon", "star") if isinstance(h, dict) else "star"
            label = h.get("label", str(h)) if isinstance(h, dict) else str(h)
            hobbies_html += f'            <span class="hobby-badge"><span class="material-symbols-outlined" style="font-size:18px;">{icon}</span>{label}</span>\n'
    else:
        hobbies_html = None

    # 10. Perform string replacements in the template
    # Replace Titles & Headers
    html_content = re.sub(r'<title>.*?</title>', f'<title>{short_name} — Applied AI Systems</title>', html_content, count=1)
    html_content = re.sub(r'<h1 id="sidebarName"[^>]*>.*?</h1>', f'<h1 id="sidebarName" style="font-size:12px;line-height:16px;font-weight:600;letter-spacing:.18em;color:#000;margin:0 0 5px 0">{short_name}</h1>', html_content)
    html_content = re.sub(r'<p id="sidebarTitle"[^>]*>.*?</p>', f'<p id="sidebarTitle" style="font-size:10px;line-height:14px;font-weight:500;letter-spacing:.16em;color:#444748;margin:0">{short_title}</p>', html_content)
    html_content = re.sub(r'<span id="heroTracking"[^>]*>.*?</span>', f'<span id="heroTracking" style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#747878;animation:fadeUp .7s ease-out both;animation-delay:.05s">{hero_tracking}</span>', html_content)
    html_content = re.sub(r'<span id="heroFirstName"[^>]*>.*?</span>', f'<span id="heroFirstName" style="display:block;animation:maskUp .95s cubic-bezier(.16,1,.3,1) both;animation-delay:.1s">{first_name}</span>', html_content)
    html_content = re.sub(r'<span id="heroLastName"[^>]*>.*?</span>', f'<span id="heroLastName" style="display:block;animation:maskUp .95s cubic-bezier(.16,1,.3,1) both;animation-delay:.22s">{last_name}</span>', html_content)
    
    # Hero Intro & Contact Buttons
    html_content = re.sub(r'<p id="heroIntro"[^>]*>.*?</p>', f'<p id="heroIntro" style="font-family:Bitter,serif;font-size:21px;line-height:1.5;color:#1a1c19;margin:0 0 26px 0;max-width:44ch;text-wrap:pretty">{p1}</p>', html_content)
    html_content = re.sub(r'<a id="heroContactBtn"[^>]*href="[^"]*"', f'<a id="heroContactBtn" href="mailto:{email}"', html_content)
    html_content = re.sub(r'<a id="heroDownloadBtn"[^>]*href="[^"]*"', f'<a id="heroDownloadBtn" href="/api/resumes/{resume_id}/pdf"', html_content)
    
    # Dashboard Fields
    html_content = re.sub(r'<span id="dashboardLocation"[^>]*>.*?</span>', f'<span id="dashboardLocation" style="font-size:13px;line-height:1.45;color:#1a1c19">{loc}</span>', html_content)
    html_content = re.sub(r'<span id="dashboardFocus"[^>]*>.*?</span>', f'<span id="dashboardFocus" style="font-size:13px;line-height:1.45;color:#1a1c19">{curr_focus}</span>', html_content)

    # About Paragraphs
    html_content = re.sub(r'<p id="aboutParagraph1"[^>]*>.*?</p>', f'<p id="aboutParagraph1" style="font-family:Bitter,serif;font-size:19px;line-height:1.6;color:#1a1c19;margin:0 0 22px 0;text-wrap:pretty">{p1}</p>', html_content)
    if p2:
        html_content = re.sub(r'<p id="aboutParagraph2"[^>]*>.*?</p>', f'<p id="aboutParagraph2" style="font-size:14px;line-height:1.7;color:#444748;margin:0 0 28px 0;text-wrap:pretty">{p2}</p>', html_content)

    # Skills Table
    if skills_html:
        html_content = re.sub(r'<div id="skillsListContainer"[^>]*>[\s\S]*?</div>\s*</div>\s*</div>\s*</section>', f'<div id="skillsListContainer" style="display:flex;flex-direction:column">\n{skills_html}            </div>\n          </div>\n        </div>\n      </section>', html_content)

    # Education Timeline
    if edu_html:
        html_content = re.sub(r'<div id="educationTimelineContainer"[^>]*>[\s\S]*?</div>\s*</div>\s*<!-- Interests', f'<div id="educationTimelineContainer" style="position:relative;padding-left:26px">\n{edu_html}          </div>\n        </div>\n\n        <!-- Interests', html_content)

    # Interests, Strengths, Hobbies
    if interests_html:
        html_content = re.sub(r'<div id="interestsPillsContainer"[^>]*>[\s\S]*?</div>', f'<div id="interestsPillsContainer" style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:26px">\n{interests_html}          </div>', html_content)
    if strengths_html:
        html_content = re.sub(r'<div id="strengthsListContainer"[^>]*>[\s\S]*?</div>', f'<div id="strengthsListContainer" style="display:flex;flex-direction:column;gap:14px;padding-top:22px;border-top:1px solid #c4c7c7">\n{strengths_html}          </div>', html_content)
    if hobbies_html:
        html_content = re.sub(r'<div id="hobbiesBadgesContainer"[^>]*>[\s\S]*?</div>', f'<div id="hobbiesBadgesContainer" style="display:flex;flex-wrap:wrap;gap:18px;margin-top:26px;padding-top:20px;border-top:1px solid #c4c7c7">\n{hobbies_html}          </div>', html_content)

    # Contact Info & Footer
    html_content = re.sub(r'<a id="contactEmailLink"[^>]*>.*?</a>', f'<a id="contactEmailLink" href="mailto:{email}" class="contact-email">{email} <span class="material-symbols-outlined" style="font-size:22px;">arrow_outward</span></a>', html_content)
    html_content = re.sub(r'<span id="contactPhone"[^>]*>.*?</span>', f'<span id="contactPhone" style="font-size:13px;color:#1a1c19">{phone}</span>', html_content)
    html_content = re.sub(r'<span id="contactLocation"[^>]*>.*?</span>', f'<span id="contactLocation" style="font-size:13px;line-height:1.55;color:#1a1c19">{address}</span>', html_content)
    html_content = re.sub(r'<a id="contactGithubLink"[^>]*href="[^"]*"', f'<a id="contactGithubLink" href="{github_url}"', html_content)
    html_content = re.sub(r'<a id="contactLinkedinLink"[^>]*href="[^"]*"', f'<a id="contactLinkedinLink" href="{linkedin_url}"', html_content)
    html_content = re.sub(r'<p id="footerCopyright"[^>]*>.*?</p>', f'<p id="footerCopyright" style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;letter-spacing:.1em;color:#8a8d8d;margin:0">© 2026 {first_name} {last_name}</p>', html_content)
    html_content = re.sub(r'<a id="drawerContactBtn"[^>]*href="[^"]*"', f'<a id="drawerContactBtn" href="mailto:{email}"', html_content)

    # Global replace of vectorizer SVGs relative path to root-relative path
    html_content = html_content.replace("url('vectorizer/", "url('/vectorizer/")
    html_content = html_content.replace('url("vectorizer/', 'url("/vectorizer/')
    html_content = html_content.replace('src="vectorizer/', 'src="/vectorizer/')

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content, status_code=200)

