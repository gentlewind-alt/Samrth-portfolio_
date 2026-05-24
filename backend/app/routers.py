"""FastAPI router exposing resume endpoints.

Endpoints:
- POST /resumes/          -> upload PDF (stores file, creates DB entry with empty JSON)
- GET  /resumes/          -> list all resumes (id, filename, timestamps)
- GET  /resumes/{id}       -> retrieve a single resume's JSON data

Future: POST /resumes/{id}/parse to trigger OCR/AI mapping.
"""

import os
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
    
    # 1. Short and hero details
    short_name = s.get("short_name", "S. RAWAT")
    short_title = s.get("short_title", "AI SYSTEMS ENG.")
    hero_tracking = s.get("hero_tracking", "APPLIED AI SYSTEMS ENGINEER")
    first_name = s.get("first_name", "SAMARTH")
    last_name = s.get("last_name", "RAWAT")
    
    # 2. Hero taglines list
    hero_taglines = [t.strip() for t in s.get("hero_taglines", []) if t and t.strip()]
    taglines_html = '<div class="max-w-xs mt-4">\n'
    for i, tagline in enumerate(hero_taglines):
        border_class = " mb-1" if i < len(hero_taglines) - 1 else ""
        taglines_html += f"""<div class="flex items-center gap-3 border-b border-outline-variant/30 pb-1{border_class}">
<span class="w-1.5 h-1.5 bg-primary rounded-none"></span>
<span class="font-['Inter_Tight'] text-[10px] font-medium uppercase tracking-[0.15em] text-on-surface-variant">{tagline}</span>
</div>\n"""
    taglines_html += '</div>'
    
    # 3. System Dashboard
    status_text = s.get("status_text") or ""
    loc = s.get("location") or ""
    curr_focus = s.get("current_focus") or ""
    avail = s.get("availability") or ""
    dashboard_html = f"""<div class="col-span-12 lg:col-span-4 border border-outline-variant p-4 bg-surface-container-low flex flex-col rounded-xl">
<div class="flex justify-between items-center mb-4 border-b border-outline-variant pb-2">
<h3 class="font-label-caps text-label-caps font-bold">SYSTEM DASHBOARD</h3>
<div class="flex items-center gap-2">
<div class="w-2 h-2 bg-green-500 rounded-full status-dot-pulse"></div>
</div>
</div>
<div class="space-y-3">
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="fiber_manual_record">fiber_manual_record</span>
<p class="font-label-caps text-[9px] uppercase">Status</p>
</div>
<p class="font-body-md text-sm text-on-surface">{status_text}</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="location_on">location_on</span>
<p class="font-label-caps text-[9px] uppercase">Location</p>
</div>
<p class="font-body-md text-sm text-on-surface">{loc}</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="architecture">architecture</span>
<p class="font-label-caps text-[9px] uppercase">Current Focus</p>
</div>
<p class="font-body-md text-sm text-on-surface">{curr_focus}</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="lock_open">lock_open</span>
<p class="font-label-caps text-[9px] uppercase">Availability</p>
</div>
<p class="font-body-md text-sm text-on-surface flex items-center gap-2">{avail} <span class="w-1.5 h-1.5 bg-primary rounded-full"></span></p>
</div>
</div>
</div>"""

    # 4. Stack Overview
    stack_overview = [item for item in s.get("stack_overview", []) if item and item.get("title") and item.get("title").strip()]
    stack_overview_html = '<section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-0 border border-outline-variant divide-y md:divide-y-0 md:divide-x divide-outline-variant mt-4 reveal visible">\n'
    for item in stack_overview:
        icon = item.get('icon', 'terminal')
        stack_overview_html += f"""<div class="space-y-2 hover:bg-surface-container-low transition-colors p-4">
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[24px]" data-icon="{icon}">{icon}</span>
<h4 class="font-label-caps text-[10px] font-bold">{item.get('title', '')}</h4>
</div>
<p class="font-body-md text-on-surface-variant text-xs">{item.get('description', '')}</p>
</div>\n"""
    stack_overview_html += '</section>'

    # 5. Projects
    projects = [p for p in s.get("projects", []) if p and p.get("title") and p.get("title").strip()]
    proj_headline = resume.content_json.get("project", {}).get("headline") or "PROJECTS / ENGINEERING SYSTEMS"
    projects_grid_html = '<div class="grid grid-cols-1 md:grid-cols-3 gap-4">\n'
    for idx, proj in enumerate(projects):
        tags_html = "".join([f'<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">{tag}</span>\n' for tag in proj.get('tags', [])])
        status = proj.get('status', 'Completed')
        icon = proj.get('icon', 'terminal')
        projects_grid_html += f"""<!-- Project {idx+1} -->
<div class="reveal border border-outline-variant p-4 space-y-4 flex flex-col group cursor-pointer project-card bg-background visible rounded-xl" style="--i:{idx+1};">
<div class="flex justify-between items-start">
<span class="material-symbols-outlined text-[24px] text-primary" data-icon="{icon}">{icon}</span>
<div class="flex items-center gap-1">
<span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
<span class="font-label-caps text-[9px] uppercase">{status}</span>
</div>
</div>
<div>
<h3 class="font-label-caps text-sm font-bold mb-1">{proj.get('title', '')}</h3>
<p class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-wider">{proj.get('subtitle', '')}</p>
</div>
<div class="flex flex-wrap gap-1">
{tags_html}</div>
<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">
{proj.get('description', '')}
</p>
<div class="mt-auto pt-3 border-t border-outline-variant flex justify-between items-center group-hover:text-primary text-secondary">
<span class="font-label-caps text-[9px]">VIEW CASE STUDY</span>
<span class="material-symbols-outlined text-[20px]" data-icon="arrow_forward">arrow_forward</span>
</div>
</div>\n"""
    projects_grid_html += '</div>'

    # 6. About Me / Metrics
    about_headline = resume.content_json.get("description", {}).get("headline") or "About Me"
    about_me = s.get("about_me", "")
    metrics = [m for m in s.get("metrics", []) if m and m.get("label") and m.get("label").strip() and m.get("value") and m.get("value").strip()]
    metrics_grid_html = '<div class="grid grid-cols-2 gap-3 pt-2">\n'
    for item in metrics:
        metrics_grid_html += f"""<div class="space-y-1">
<span class="font-label-caps text-[9px] text-on-surface-variant opacity-60 uppercase">{item.get('label', '')}</span>
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[20px]">{item.get('icon', 'star')}</span>
<span class="font-bold text-sm">{item.get('value', '')}</span>
</div>
</div>\n"""
    metrics_grid_html += '</div>'

    # 7. Skills
    skills_headline = resume.content_json.get("skills", {}).get("headline") or "Technical Skills"
    skills_raw = s.get("skills", [])
    skills = []
    for item in skills_raw:
        cat = item.get("category", "")
        s_list = [sk.strip() for sk in item.get("skills", []) if sk and sk.strip()]
        if cat and cat.strip() and s_list:
            skills.append({"category": cat, "skills": s_list})
            
    skills_cols_html = '<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">\n'
    mid = (len(skills) + 1) // 2
    col1_categories = skills[:mid]
    col2_categories = skills[mid:]

    skills_cols_html += '<div class="space-y-3">\n'
    for item in col1_categories:
        skills_str = ", ".join(item.get('skills', []))
        skills_cols_html += f"""<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">{item.get('category', '')}</h4>
<p class="font-body-md text-xs">{skills_str}</p>
</div>\n"""
    skills_cols_html += '</div>\n'

    skills_cols_html += '<div class="space-y-3">\n'
    for item in col2_categories:
        skills_str = ", ".join(item.get('skills', []))
        skills_cols_html += f"""<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">{item.get('category', '')}</h4>
<p class="font-body-md text-xs">{skills_str}</p>
</div>\n"""
    skills_cols_html += '</div>\n'
    skills_cols_html += '</div>'

    # 8. Education & Experience Timeline
    edu_headline = resume.content_json.get("education", {}).get("headline") or "Education"
    education_and_experience = [item for item in s.get("education_and_experience", []) if item and item.get("school") and item.get("school").strip()]
    edu_timeline_html = f"""<div class="space-y-4 border-r border-outline-variant p-4 rounded-bl-xl" id="education">
<h2 class="font-label-caps text-[11px] font-bold uppercase">{edu_headline}</h2>
<div class="relative pl-4 space-y-4">
<div class="absolute left-1 top-0 bottom-0 w-px bg-outline-variant/30"></div>"""
    for idx, item in enumerate(education_and_experience):
        opacity_class = "" if idx == 0 else " opacity-40"
        edu_timeline_html += f"""\n<div class="relative">
<div class="absolute -left-[15px] top-1 w-2 h-2 bg-primary rounded-full{opacity_class}"></div>
<p class="font-label-caps text-[8px] text-on-surface-variant mb-0.5">{item.get('years', '')}</p>
<h4 class="font-bold text-[11px] leading-tight">{item.get('school', '')}</h4>
<p class="text-[10px] text-on-surface-variant">{item.get('degree_gpa', '')}</p>
</div>"""
    edu_timeline_html += '\n</div>\n</div>'

    # 9. Hobbies
    hobbies_headline = resume.content_json.get("hobbies", {}).get("headline") or "Hobbies"
    hobbies = [item for item in s.get("hobbies", []) if item and item.get("label") and item.get("label").strip()]
    hobbies_grid_html = f"""<div class="space-y-4 border-r border-outline-variant p-4 rounded-none"><h2 class="font-label-caps text-[11px] font-bold uppercase">{hobbies_headline}</h2><div class="grid grid-cols-5 gap-2">"""
    for item in hobbies:
        icon = item.get('icon', 'star')
        label = item.get('label', '')
        hobbies_grid_html += f"""\n <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: 'wght' 300, 'opsz' 24;">{icon}</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">{label}</span> </div>"""
    hobbies_grid_html += '\n</div>\n</div>'

    # 10. Interests & Strengths
    interests_headline = resume.content_json.get("interests", {}).get("headline") or "Interests & Strengths"
    interests = [i.strip() for i in s.get("interests", []) if i and i.strip()]
    strengths = [st.strip() for st in s.get("strengths", []) if st and st.strip()]
    interests_and_strengths_html = f"""<div class="space-y-3 p-4 rounded-br-xl" id="interests">
<h2 class="font-label-caps text-[11px] font-bold uppercase">{interests_headline}</h2>
<ul class="space-y-1">"""
    for interest in interests:
        interests_and_strengths_html += f"""\n<li class="flex items-center gap-2 text-[11px]"><span class="material-symbols-outlined text-[20px] text-secondary">arrow_right_alt</span> {interest}</li>"""
    interests_and_strengths_html += """\n</ul>
<div class="pt-2 border-t border-outline-variant/30">
<ul class="space-y-1 text-[10px] text-on-surface-variant italic">"""
    for strength in strengths:
        interests_and_strengths_html += f"""\n<li class="">• {strength}</li>"""
    interests_and_strengths_html += '\n</ul>\n</div>\n</div>'

    # 11. Footer details
    email = s.get("email", "samarthrawat10@email.com")
    phone = s.get("phone", "+91 8984100922")
    address = s.get("address", "")
    github_url = s.get("github_url", "#")
    linkedin_url = s.get("linkedin_url", "#")
    quote = s.get("quote", "Building systems that understand, adapt and connect.")
    footer_html = f"""<footer class="border-t border-outline-variant mt-8 pb-12 pt-6 grid grid-cols-1 md:grid-cols-12 gap-6" id="contact">
<div class="md:col-span-4 space-y-4">
<div class="space-y-1">
<h2 class="font-label-caps text-[11px] font-bold">LET'S CONNECT</h2>
</div>
<ul class="space-y-2 text-xs">
<li class="flex items-center gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary" data-icon="mail">mail</span>
<a class="hover:underline" href="mailto:{email}">{email}</a>
</li>
<li class="flex items-center gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary" data-icon="call">call</span>
<span class="">{phone}</span>
</li>
<li class="flex items-start gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary mt-0.5" data-icon="location_on">location_on</span>
<span class="">{address}</span>
</li>
</ul>
</div>
<div class="md:col-span-3 space-y-4">
<div class="space-y-1">
<h2 class="font-label-caps text-[11px] font-bold uppercase">Find me online</h2>
</div>
<div class="flex flex-col gap-2">
<a class="flex items-center gap-2 text-xs hover:text-primary transition-colors text-secondary" href="{github_url}">
<span class="material-symbols-outlined text-[20px]" data-icon="code">code</span> GitHub
                    </a>
<a class="flex items-center gap-2 text-xs hover:text-primary transition-colors text-secondary" href="{linkedin_url}">
<span class="material-symbols-outlined text-[20px]" data-icon="link">link</span> LinkedIn
                    </a>
</div>
</div>
<div class="md:col-span-5 space-y-4 flex flex-col justify-between items-end text-right">
<div class="max-w-xs space-y-2">
<span class="material-symbols-outlined text-[32px] opacity-20 text-secondary" data-icon="format_quote">format_quote</span>
<p class="font-body-md text-xs text-on-surface-variant italic leading-relaxed">
                        {quote}
                    </p>
</div>
<div class="w-16 h-px bg-outline-variant mt-2"></div>
<div class="space-y-1">
<p class="font-label-caps text-[9px] opacity-40 uppercase">© 2026 {first_name} {last_name}. All rights reserved.</p>
<p class="font-label-caps text-[9px] opacity-60 tracking-wider">&gt; designed &amp; built with purpose</p>
</div>
</div>
</footer>"""

    # Perform final string replacements to inject the AI/user content into the locked template
    # Replace S. RAWAT occurrences
    html_content = html_content.replace("<title>S. RAWAT</title>", f"<title>{short_name}</title>")
    html_content = html_content.replace('<h1 class="font-label-caps text-label-caps tracking-widest text-primary mb-1">S. RAWAT</h1>', f'<h1 class="font-label-caps text-label-caps tracking-widest text-primary mb-1">{short_name}</h1>')
    
    # Replace AI SYSTEMS ENG.
    html_content = html_content.replace('<p class="font-label-caps text-label-caps text-on-surface-variant opacity-60">AI SYSTEMS ENG.</p>', f'<p class="font-label-caps text-label-caps text-on-surface-variant opacity-60">{short_title}</p>')
    
    # Replace Tracking title
    html_content = html_content.replace('<p class="font-label-caps text-label-caps text-on-surface-variant tracking-[0.2em]">APPLIED AI SYSTEMS ENGINEER</p>', f'<p class="font-label-caps text-label-caps text-on-surface-variant tracking-[0.2em]">{hero_tracking}</p>')
    
    # Replace Full Name
    html_content = html_content.replace('<h1 class="font-hero-lg text-6xl lg:text-7xl leading-none uppercase -ml-1">SAMARTH<br>RAWAT</h1>', f'<h1 class="font-hero-lg text-6xl lg:text-7xl leading-none uppercase -ml-1">{first_name}<br>{last_name}</h1>')
    
    # Replace Taglines block
    original_taglines_block = """<div class="max-w-xs mt-4">
<div class="flex items-center gap-3 border-b border-outline-variant/30 pb-1 mb-1">
<span class="w-1.5 h-1.5 bg-primary rounded-none"></span>
<span class="font-['Inter_Tight'] text-[10px] font-medium uppercase tracking-[0.15em] text-on-surface-variant">Embedded Intelligence</span>
</div>
<div class="flex items-center gap-3 border-b border-outline-variant/30 pb-1 mb-1">
<span class="w-1.5 h-1.5 bg-primary rounded-none"></span>
<span class="font-['Inter_Tight'] text-[10px] font-medium uppercase tracking-[0.15em] text-on-surface-variant">Behavioral Interfaces</span>
</div>
<div class="flex items-center gap-3 border-b border-outline-variant/30 pb-1 mb-1">
<span class="w-1.5 h-1.5 bg-primary rounded-none"></span>
<span class="font-['Inter_Tight'] text-[10px] font-medium uppercase tracking-[0.15em] text-on-surface-variant">Agentic Systems</span>
</div>
<div class="flex items-center gap-3 border-b border-outline-variant/30 pb-1">
<span class="w-1.5 h-1.5 bg-primary rounded-none"></span>
<span class="font-['Inter_Tight'] text-[10px] font-medium uppercase tracking-[0.15em] text-on-surface-variant">Human-Machine Interaction</span>
</div>
</div>"""
    html_content = html_content.replace(original_taglines_block, taglines_html)
    
    # Replace Dashboard
    original_dashboard_block = """<div class="col-span-12 lg:col-span-4 border border-outline-variant p-4 bg-surface-container-low flex flex-col rounded-xl">
<div class="flex justify-between items-center mb-4 border-b border-outline-variant pb-2">
<h3 class="font-label-caps text-label-caps font-bold">SYSTEM DASHBOARD</h3>
<div class="flex items-center gap-2">
<div class="w-2 h-2 bg-green-500 rounded-full status-dot-pulse"></div>
</div>
</div>
<div class="space-y-3">
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="fiber_manual_record">fiber_manual_record</span>
<p class="font-label-caps text-[9px] uppercase">Status</p>
</div>
<p class="font-body-md text-sm text-on-surface">Building intelligent systems that feel expressive.</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="location_on">location_on</span>
<p class="font-label-caps text-[9px] uppercase">Location</p>
</div>
<p class="font-body-md text-sm text-on-surface">Bhubaneswar, Odisha, India</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="architecture">architecture</span>
<p class="font-label-caps text-[9px] uppercase">Current Focus</p>
</div>
<p class="font-body-md text-sm text-on-surface">Agentic AI • Embedded Systems Behavioral Architectures</p>
</div>
<div class="space-y-1">
<div class="flex items-center gap-2 text-on-surface-variant">
<span class="material-symbols-outlined text-[20px]" data-icon="lock_open">lock_open</span>
<p class="font-label-caps text-[9px] uppercase">Availability</p>
</div>
<p class="font-body-md text-sm text-on-surface flex items-center gap-2">Open to Opportunities <span class="w-1.5 h-1.5 bg-primary rounded-full"></span></p>
</div>
</div>
</div>"""
    html_content = html_content.replace(original_dashboard_block, dashboard_html)
    
    # Replace Stack Overview
    original_stack_overview_block = """<section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-0 border border-outline-variant divide-y md:divide-y-0 md:divide-x divide-outline-variant mt-4 reveal visible">
<div class="space-y-2 hover:bg-surface-container-low transition-colors p-4">
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[24px]" data-icon="neurology">neurology</span>
<h4 class="font-label-caps text-[10px] font-bold">AI/ML STACK</h4>
</div>
<p class="font-body-md text-on-surface-variant text-xs">LLMs, Deep Learning, Machine Learning, Data Visualization</p>
</div>
<div class="space-y-2 hover:bg-surface-container-low transition-colors p-4">
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[24px]" data-icon="memory">memory</span>
<h4 class="font-label-caps text-[10px] font-bold">EMBEDDED STACK</h4>
</div>
<p class="font-body-md text-on-surface-variant text-xs">ESP32, FreeRTOS, Sensors, IoT Systems, Real-time Interfaces</p>
</div>
<div class="space-y-2 hover:bg-surface-container-low transition-colors p-4">
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[24px]" data-icon="terminal">terminal</span>
<h4 class="font-label-caps text-[10px] font-bold">TOOLS &amp; PLATFORMS</h4>
</div>
<p class="font-body-md text-on-surface-variant text-xs">Python, Git, VS Code, TensorFlow, Arduino, Power BI, MySQL</p>
</div>
<div class="space-y-2 hover:bg-surface-container-low transition-colors p-4">
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[24px]" data-icon="webhook">webhook</span>
<h4 class="font-label-caps text-[10px] font-bold">SYSTEMS PHILOSOPHY</h4>
</div>
<p class="font-body-md text-on-surface-variant text-xs">Designing constrained systems that are performative, reliable and human-centered.</p>
</div>
</section>"""
    html_content = html_content.replace(original_stack_overview_block, stack_overview_html)
    
    # Replace Projects Block
    original_projects_headline = '<h2 class="font-headline-md text-2xl uppercase">PROJECTS / ENGINEERING SYSTEMS</h2>'
    html_content = html_content.replace(original_projects_headline, f'<h2 class="font-headline-md text-2xl uppercase">{proj_headline}</h2>')
    
    original_projects_grid_block = """<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
<!-- Project 1 -->
<div class="reveal border border-outline-variant p-4 space-y-4 flex flex-col group cursor-pointer project-card bg-background visible rounded-xl">
<div class="flex justify-between items-start">
<span class="material-symbols-outlined text-[24px] text-primary" data-icon="terminal">terminal</span>
<div class="flex items-center gap-1">
<span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
<span class="font-label-caps text-[9px] uppercase">Completed</span>
</div>
</div>
<div>
<h3 class="font-label-caps text-sm font-bold mb-1">CRITIC-OS</h3>
<p class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-wider">AI Music Critique System</p>
</div>
<div class="flex flex-wrap gap-1">
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Python</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Flask</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Groq</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Redis</span>
</div>
<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">
                        AI-driven web app that generates satirical music critiques using 6 unique AI personas. Integrates Spotify API and emotion analysis.
                    </p>
<div class="mt-auto pt-3 border-t border-outline-variant flex justify-between items-center group-hover:text-primary text-secondary">
<span class="font-label-caps text-[9px]">VIEW CASE STUDY</span>
<span class="material-symbols-outlined text-[20px]" data-icon="arrow_forward">arrow_forward</span>
</div>
</div>
<!-- Project 2 -->
<div class="reveal border border-outline-variant p-4 space-y-4 flex flex-col group cursor-pointer project-card bg-background visible rounded-xl">
<div class="flex justify-between items-start">
<span class="material-symbols-outlined text-[24px] text-primary" data-icon="alarm">alarm</span>
<div class="flex items-center gap-1">
<span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
<span class="font-label-caps text-[9px] uppercase">Completed</span>
</div>
</div>
<div>
<h3 class="font-label-caps text-sm font-bold mb-1">IOT SMART ALARM CLOCK</h3>
<p class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-wider">Embedded Interaction System</p>
</div>
<div class="flex flex-wrap gap-1">
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">ESP32-C3</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">C++</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">FreeRTOS</span>
</div>
<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">
                        Gesture-controlled smart alarm with custom animation engine, multi-sensor fusion (PIR, IMU) and dual-source timekeeping.
                    </p>
<div class="mt-auto pt-3 border-t border-outline-variant flex justify-between items-center group-hover:text-primary text-secondary">
<span class="font-label-caps text-[9px]">VIEW CASE STUDY</span>
<span class="material-symbols-outlined text-[20px]" data-icon="arrow_forward">arrow_forward</span>
</div>
</div>
<!-- Project 3 -->
<div class="reveal border border-outline-variant p-4 space-y-4 flex flex-col group cursor-pointer project-card bg-background visible rounded-xl">
<div class="flex justify-between items-start">
<span class="material-symbols-outlined text-[24px] text-primary" data-icon="front_hand">front_hand</span>
<div class="flex items-center gap-1">
<span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
<span class="font-label-caps text-[9px] uppercase">Completed</span>
</div>
</div>
<div>
<h3 class="font-label-caps text-sm font-bold mb-1">ISL GESTURE RECOGNITION</h3>
<p class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-wider">ML Classification System</p>
</div>
<div class="flex flex-wrap gap-1">
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Python</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Scikit-learn</span>
<span class="px-1.5 py-0.5 border border-outline-variant text-[9px] font-label-caps uppercase text-secondary">Pandas</span>
</div>
<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">
                        Processed ISL hand gesture datasets and trained a Random Forest model to classify Indian Sign Language gestures with high accuracy.
                    </p>
<div class="mt-auto pt-3 border-t border-outline-variant flex justify-between items-center group-hover:text-primary text-secondary">
<span class="font-label-caps text-[9px]">VIEW CASE STUDY</span>
<span class="material-symbols-outlined text-[20px]" data-icon="arrow_forward">arrow_forward</span>
</div>
</div>
</div>"""
    html_content = html_content.replace(original_projects_grid_block, projects_grid_html)
    
    # Replace About Me Headline and Description
    html_content = html_content.replace('<h2 class="font-label-caps text-[11px] font-bold uppercase">About Me</h2>', f'<h2 class="font-label-caps text-[11px] font-bold uppercase">{about_headline}</h2>')
    
    original_about_me_text_block = """<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">
            Applied AI developer and B.Tech IT student at KIIT Bhubaneswar, specializing in interactive systems, behavioral architectures, and AI-enhanced user experiences. Experienced in integrating embedded systems, real-time interfaces, and intelligent workflow automation.
        </p>"""
    html_content = html_content.replace(original_about_me_text_block, f'<p class="font-body-md text-xs text-on-surface-variant leading-relaxed">\n            {about_me}\n        </p>')
    
    # Replace Metrics Grid
    original_metrics_grid_block = """<div class="grid grid-cols-2 gap-3 pt-2">
<div class="space-y-1">
<span class="font-label-caps text-[9px] text-on-surface-variant opacity-60 uppercase">CGPA (8th Sem)</span>
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[20px]">school</span>
<span class="font-bold text-sm">8.24</span>
</div>
</div>
<div class="space-y-1">
<span class="font-label-caps text-[9px] text-on-surface-variant opacity-60 uppercase">Major Projects</span>
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[20px]">rocket_launch</span>
<span class="font-bold text-sm">3+</span>
</div>
</div>
<div class="space-y-1">
<span class="font-label-caps text-[9px] text-on-surface-variant opacity-60 uppercase">Tech Domains</span>
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[20px]">dataset</span>
<span class="font-bold text-sm">5+</span>
</div>
</div>
<div class="space-y-1">
<span class="font-label-caps text-[9px] text-on-surface-variant opacity-60 uppercase">Hours Building</span>
<div class="flex items-center gap-2 text-primary">
<span class="material-symbols-outlined text-[20px]">speed</span>
<span class="font-bold text-sm">1200+</span>
</div>
</div>
</div>"""
    html_content = html_content.replace(original_metrics_grid_block, metrics_grid_html)
    
    # Replace Skills Block
    original_skills_block = """<div class="space-y-4 p-4" id="skills">
<div class="flex items-baseline justify-between">
<h2 class="font-label-caps text-[11px] font-bold uppercase">Technical Skills</h2>   
</div>
<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
<div class="space-y-3">
<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">Programming</h4>
<p class="font-body-md text-xs">Python, Java, C, HTML/CSS</p>
</div>
<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">Databases</h4>
<p class="font-body-md text-xs">MySQL</p>
</div>
<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">Tools</h4>
<p class="font-body-md text-xs">Git, VS Code, MS Office, Power BI, Arduino, LATEX</p>
</div>
</div>
<div class="space-y-3">
<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">Frameworks / Libs</h4>
<p class="font-body-md text-xs">TensorFlow, Scikit-learn, NumPy, Pandas, Matplotlib</p>
</div>
<div class="space-y-1">
<h4 class="font-label-caps text-[9px] text-on-surface-variant uppercase tracking-widest">Platforms / APIs</h4>
<p class="font-body-md text-xs">Spotify API, OpenAI/Groq, Redis, FreeRTOS</p>
</div>
</div>
</div>
</div>"""
    html_content = html_content.replace(original_skills_block, f"""<div class="space-y-4 p-4" id="skills">
<div class="flex items-baseline justify-between">
<h2 class="font-label-caps text-[11px] font-bold uppercase">{skills_headline}</h2>   
</div>
{skills_cols_html}
</div>""")

    # Replace Education Block
    original_education_block = """<div class="space-y-4 border-r border-outline-variant p-4 rounded-bl-xl" id="education">
<h2 class="font-label-caps text-[11px] font-bold uppercase">Education</h2>
<div class="relative pl-4 space-y-4">
<div class="absolute left-1 top-0 bottom-0 w-px bg-outline-variant/30"></div>
<div class="relative">
<div class="absolute -left-[15px] top-1 w-2 h-2 bg-primary rounded-full"></div>
<p class="font-label-caps text-[8px] text-on-surface-variant mb-0.5">2022 — 2026</p>
<h4 class="font-bold text-[11px] leading-tight">KIIT, Bhubaneswar</h4>
<p class="text-[10px] text-on-surface-variant">B.Tech IT • CGPA: 8.24</p>
</div>
<div class="relative">
<div class="absolute -left-[15px] top-1 w-2 h-2 bg-primary rounded-full opacity-40"></div>
<p class="font-label-caps text-[8px] text-on-surface-variant mb-0.5">2022</p>
<h4 class="font-bold text-[11px] leading-tight">LBS Public School, Kota</h4>
<p class="text-[10px] text-on-surface-variant">12th CBSE • 79.4%</p>
</div>
<div class="relative">
<div class="absolute -left-[15px] top-1 w-2 h-2 bg-primary rounded-full opacity-40"></div>
<p class="font-label-caps text-[8px] text-on-surface-variant mb-0.5">2022</p>
<h4 class="font-bold text-[11px] leading-tight">GMR VARALAKSHMI DAV PUBLIC SCHOOL, DHENKANAL</h4>
<p class="text-[10px] text-on-surface-variant">10th CBSE • 90.0%</p>
</div>
</div>
</div>"""
    html_content = html_content.replace(original_education_block, edu_timeline_html)
    
    # Replace Hobbies Block
    original_hobbies_block = """<div class="space-y-4 border-r border-outline-variant p-4 rounded-none"><h2 class="font-label-caps text-[11px] font-bold uppercase">Hobbies</h2><div class="grid grid-cols-5 gap-2"> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: &quot;wght&quot; 300, &quot;opsz&quot; 24;">menu_book</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Reading</span> </div> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: &quot;wght&quot; 300, &quot;opsz&quot; 24;">movie_filter</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Movies</span> </div> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: &quot;wght&quot; 300, &quot;opsz&quot; 24;">psychology</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Learning</span> </div> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: &quot;wght&quot; 300, &quot;opsz&quot; 24;">precision_manufacturing</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Building</span> </div> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: &quot;wght&quot; 300, &quot;opsz&quot; 24;">podcasts</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Podcasts</span> </div><div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: 'wght' 300, 'opsz' 24;">headset</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Music</span> </div> <div class="flex flex-col items-center gap-1.5 p-2 border border-outline-variant/30 hover:bg-surface-container-high transition-all cursor-pointer group">  <span class="material-symbols-outlined text-[24px] text-secondary group-hover:text-primary" style="font-variation-settings: 'wght' 300, 'opsz' 24;">restaurant</span>  <span class="font-label-caps text-[8px] uppercase tracking-wider text-on-surface-variant group-hover:text-primary">Cooking</span> </div></div></div>"""
    html_content = html_content.replace(original_hobbies_block, hobbies_grid_html)
    
    # Replace Interests & Strengths Block
    original_interests_block = """<div class="space-y-3 p-4 rounded-br-xl" id="interests">
<h2 class="font-label-caps text-[11px] font-bold uppercase">Interests &amp; Strengths</h2>
<ul class="space-y-1">
<li class="flex items-center gap-2 text-[11px]"><span class="material-symbols-outlined text-[20px] text-secondary">arrow_right_alt</span> LLMs &amp; Fine Tuning</li>
<li class="flex items-center gap-2 text-[11px]"><span class="material-symbols-outlined text-[20px] text-secondary">arrow_right_alt</span> Agentic AI</li>
<li class="flex items-center gap-2 text-[11px]"><span class="material-symbols-outlined text-[20px] text-secondary">arrow_right_alt</span> Human-Computer Interaction</li>
</ul>
<div class="pt-2 border-t border-outline-variant/30">
<ul class="space-y-1 text-[10px] text-on-surface-variant italic">
<li class="">• Architecture integration expert.</li>
<li class="">• Scalable system design.</li>
<li class="">• Cross-domain exposure: Embedded, AI, UX.</li>
</ul>
</div>
</div>"""
    html_content = html_content.replace(original_interests_block, interests_and_strengths_html)
    
    # Replace Footer Block
    original_footer_block = """<footer class="border-t border-outline-variant mt-8 pb-12 pt-6 grid grid-cols-1 md:grid-cols-12 gap-6" id="contact">
<div class="md:col-span-4 space-y-4">
<div class="space-y-1">
<h2 class="font-label-caps text-[11px] font-bold">LET'S CONNECT</h2>
</div>
<ul class="space-y-2 text-xs">
<li class="flex items-center gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary" data-icon="mail">mail</span>
<a class="hover:underline" href="mailto:samarthrawat10@email.com">samarthrawat10@email.com</a>
</li>
<li class="flex items-center gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary" data-icon="call">call</span>
<span class="">+91 8984100922</span>
</li>
<li class="flex items-start gap-2">
<span class="material-symbols-outlined text-[20px] text-secondary mt-0.5" data-icon="location_on">location_on</span>
<span class="">DGM-2 201, TATA Steel Meramandali Colony, Meramandali, Narendrapur, Odisha — 759121, India</span>
</li>
</ul>
</div>
<div class="md:col-span-3 space-y-4">
<div class="space-y-1">
<h2 class="font-label-caps text-[11px] font-bold uppercase">Find me online</h2>
</div>
<div class="flex flex-col gap-2">
<a class="flex items-center gap-2 text-xs hover:text-primary transition-colors text-secondary" href="#">
<span class="material-symbols-outlined text-[20px]" data-icon="code">code</span> GitHub
                    </a>
<a class="flex items-center gap-2 text-xs hover:text-primary transition-colors text-secondary" href="#">
<span class="material-symbols-outlined text-[20px]" data-icon="link">link</span> LinkedIn
                    </a>
</div>
</div>
<div class="md:col-span-5 space-y-4 flex flex-col justify-between items-end text-right">
<div class="max-w-xs space-y-2">
<span class="material-symbols-outlined text-[32px] opacity-20 text-secondary" data-icon="format_quote">format_quote</span>
<p class="font-body-md text-xs text-on-surface-variant italic leading-relaxed">
                        Building systems that understand, adapt and connect.
                    </p>
</div>
<div class="w-16 h-px bg-outline-variant mt-2"></div>
<div class="space-y-1">
<p class="font-label-caps text-[9px] opacity-40 uppercase">© 2024 Samarth Rawat. All rights reserved.</p>
<p class="font-label-caps text-[9px] opacity-60 tracking-wider">&gt; designed &amp; built with purpose</p>
</div>
</div>
</footer>"""
    html_content = html_content.replace(original_footer_block, footer_html)
    
    # Replace Download Button with dynamic link to actual PDF
    original_download_button = """<button class="border border-outline px-6 py-2 font-label-caps text-[10px] flex items-center gap-2 hover:bg-surface-container transition-colors text-primary">
                        DOWNLOAD RESUME <span class="material-symbols-outlined text-[16px]" data-icon="download">download</span>
</button>"""
    dynamic_download_link = f"""<a href="/api/resumes/{resume_id}/pdf" download class="border border-outline px-6 py-2 font-label-caps text-[10px] flex items-center gap-2 hover:bg-surface-container transition-colors text-primary no-underline inline-flex">
                        DOWNLOAD RESUME <span class="material-symbols-outlined text-[16px]" data-icon="download">download</span>
</a>"""
    html_content = html_content.replace(original_download_button, dynamic_download_link)
    
    # Global replace of vectorizer SVGs relative path to root-relative path
    html_content = html_content.replace("url('vectorizer/", "url('/vectorizer/")
    html_content = html_content.replace('url("vectorizer/', 'url("/vectorizer/')
    html_content = html_content.replace('src="vectorizer/', 'src="/vectorizer/')

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content, status_code=200)

