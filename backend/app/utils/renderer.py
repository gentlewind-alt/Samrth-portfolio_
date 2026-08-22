"""HTML portfolio renderer from resume data."""
from typing import Dict, Any


def render_portfolio_html(resume_data: Dict[str, Any], resume_id: int) -> str:
    """Render complete portfolio HTML from resume data."""
    name = resume_data.get("name", "Portfolio")
    email = resume_data.get("email", "contact@example.com")
    phone = resume_data.get("number", "")
    address = resume_data.get("address", "")
    links = resume_data.get("links", [])

    # Extract sections
    desc = resume_data.get("description", {})
    exp = resume_data.get("experience", {})
    proj = resume_data.get("project", {})
    edu = resume_data.get("education", {})
    skills = resume_data.get("skills", {})
    hobbies_data = resume_data.get("hobbies", {})
    strengths_data = resume_data.get("strengths", {})

    # Build skill rows
    skills_html = ""
    if skills.get("body"):
        for idx, line in enumerate(skills["body"].split("\n")):
            if line.strip():
                skills_html += f'''              <div class="stack-row">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#8a8d8d">{line.split(":")[0].strip()}</span>
                <span style="font-size:14px;line-height:1.5;color:#1a1c19">{line.split(":", 1)[1].strip() if ":" in line else line}</span>
              </div>\n'''

    # Build education timeline
    edu_html = '<div style="position:absolute;left:3px;top:6px;bottom:6px;width:1px;background:#c4c7c7"></div>\n'
    if edu.get("body"):
        edu_lines = [l.strip() for l in edu["body"].split("\n") if l.strip()]
        for idx, line in enumerate(edu_lines):
            pad_style = 'style="position:relative"' if idx == len(edu_lines) - 1 else 'style="position:relative;padding-bottom:26px"'
            accent = "var(--accent)" if idx == 0 else "#c4c7c7"
            edu_html += f'''            <div {pad_style}>
              <div style="position:absolute;left:-26px;top:5px;width:7px;height:7px;border-radius:9999px;background:{accent}"></div>
              <p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;color:#8a8d8d;margin:0 0 5px 0">{line}</p>
            </div>\n'''

    # Build hobbies
    hobbies_html = ""
    if hobbies_data.get("body"):
        for hobby in hobbies_data["body"].split(","):
            hobby = hobby.strip()
            if hobby:
                hobbies_html += f'            <span class="hobby-badge"><span class="material-symbols-outlined" style="font-size:18px;">star</span>{hobby}</span>\n'

    # Build strengths
    strengths_html = ""
    if strengths_data.get("body"):
        for strength in strengths_data["body"].split("\n"):
            strength = strength.strip()
            if strength:
                strengths_html += f'            <p style="font-size:13px;line-height:1.65;color:#444748;margin:0;text-wrap:pretty">{strength}</p>\n'

    html = f"""<!DOCTYPE html>
<html class="light" lang="en" style="scroll-behavior: smooth;">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — Applied AI Systems</title>

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
  <link href="https://fonts.googleapis.com/css2?family=Bitter:wght@300;400;500;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0&display=swap" rel="stylesheet">

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background-color: #fafaf5;
      color: #1a1c19;
      font-family: "IBM Plex Sans", sans-serif;
      --accent: #22c55e;
      overflow-x: hidden;
    }}
    a {{ color: inherit; text-decoration: none; }}

    /* Hero Section */
    .hero {{ padding: 80px 40px; text-align: center; }}
    .hero h1 {{
      font-family: Bitter, serif;
      font-size: clamp(48px, 8vw, 96px);
      font-weight: 300;
      letter-spacing: -0.02em;
      margin-bottom: 20px;
    }}
    .hero p {{ font-size: 18px; line-height: 1.6; color: #444748; max-width: 600px; margin: 20px auto; }}

    /* About Section */
    .section {{ padding: 60px 40px; max-width: 1000px; margin: 0 auto; }}
    .section h2 {{
      font-family: Bitter, serif;
      font-size: 32px;
      margin-bottom: 30px;
      border-bottom: 1px solid #c4c7c7;
      padding-bottom: 15px;
    }}
    .section p {{ font-size: 14px; line-height: 1.8; margin-bottom: 15px; }}

    /* Skills */
    .stack-row {{
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 20px;
      padding: 14px 0;
      border-top: 1px solid #c4c7c7;
    }}

    /* Education */
    .timeline {{ position: relative; padding-left: 30px; }}
    .timeline-item {{ margin-bottom: 30px; }}
    .timeline-item h4 {{ font-size: 16px; margin-bottom: 5px; }}
    .timeline-item p {{ font-size: 12px; color: #747878; }}

    /* Hobbies */
    .hobby-badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-right: 15px;
      margin-bottom: 10px;
      font-size: 12px;
    }}

    /* Contact */
    .contact {{
      background: #f0f0eb;
      padding: 40px;
      margin: 40px 0;
      border-radius: 8px;
      text-align: center;
    }}
    .contact a {{
      display: inline-block;
      margin: 10px 15px;
      padding: 10px 20px;
      background: #111;
      color: #fafaf5;
      border-radius: 6px;
      font-weight: 600;
      transition: background 0.3s;
    }}
    .contact a:hover {{ background: #000; }}

    /* Chiyo Toggle */
    .chiyo-toggle-container {{
      position: fixed;
      bottom: 20px;
      left: 20px;
      z-index: 9999;
    }}
    .chiyo-toggle-btn {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: #111;
      color: #fafaf5;
      border: 1px solid #747878;
      cursor: pointer;
      font-size: 22px;
      transition: all 0.3s;
    }}
    .chiyo-toggle-btn:hover {{
      background: #000;
      transform: scale(1.1);
    }}
    .chiyo-active-override {{
      background: transparent !important;
    }}
    .chiyo-active-override body {{
      background: transparent !important;
    }}

    @media (max-width: 768px) {{
      .section {{ padding: 40px 20px; }}
      .hero {{ padding: 60px 20px; }}
      .stack-row {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<!-- Chiyo Toggle -->
<div class="chiyo-toggle-container">
  <button class="chiyo-toggle-btn" id="chiyoToggle" title="Toggle Chiyo">🐱</button>
</div>

<!-- Hero -->
<section class="hero">
  <h1>{name}</h1>
  <p>{desc.get("body", "Welcome to my portfolio")}</p>
  <div style="margin-top: 30px;">
    <a href="mailto:{email}" style="display: inline-block; padding: 12px 24px; background: #111; color: white; border-radius: 6px; margin: 0 10px; font-weight: 600;">Contact Me</a>
    <a href="/api/resumes/{resume_id}/pdf" style="display: inline-block; padding: 12px 24px; background: #f0f0eb; color: #111; border-radius: 6px; margin: 0 10px; font-weight: 600;">Download Resume</a>
  </div>
</section>

<!-- About -->
<section class="section">
  <h2>About</h2>
  <p>{desc.get("body", "")}</p>
</section>

<!-- Skills -->
{f'''<section class="section">
  <h2>{skills.get("headline", "Skills")}</h2>
  <div style="margin-top: 20px;">
    {skills_html}
  </div>
</section>''' if skills_html else ''}

<!-- Experience -->
{f'''<section class="section">
  <h2>{exp.get("headline", "Experience")}</h2>
  <p>{exp.get("body", "")}</p>
</section>''' if exp.get("body") else ''}

<!-- Projects -->
{f'''<section class="section">
  <h2>{proj.get("headline", "Projects")}</h2>
  <p>{proj.get("body", "")}</p>
</section>''' if proj.get("body") else ''}

<!-- Education -->
{f'''<section class="section">
  <h2>{edu.get("headline", "Education")}</h2>
  <div class="timeline">
    {edu_html}
  </div>
</section>''' if edu.get("body") else ''}

<!-- Contact -->
<section class="contact">
  <h2>Get in Touch</h2>
  <p style="margin: 15px 0;">
    {address}<br>
    <a href="mailto:{email}">{email}</a><br>
    {phone}
  </p>
  <div style="margin-top: 20px;">
    {' '.join([f'<a href="{link}" target="_blank">{link.split("/")[-1]}</a>' for link in links if link])}
  </div>
</section>

<script>
  // Chiyo Toggle
  const toggleBtn = document.getElementById('chiyoToggle');
  let enabled = localStorage.getItem('chiyo-enabled') === 'true';

  if (enabled) {{
    toggleBtn.style.background = '#22c55e';
    toggleBtn.style.color = '#111';
    document.documentElement.classList.add('chiyo-active-override');
  }}

  toggleBtn.addEventListener('click', () => {{
    enabled = !enabled;
    localStorage.setItem('chiyo-enabled', enabled);
    if (enabled) {{
      toggleBtn.style.background = '#22c55e';
      toggleBtn.style.color = '#111';
      document.documentElement.classList.add('chiyo-active-override');
    }} else {{
      toggleBtn.style.background = '#111';
      toggleBtn.style.color = '#fafaf5';
      document.documentElement.classList.remove('chiyo-active-override');
    }}
  }});
</script>

</body>
</html>"""
    return html
