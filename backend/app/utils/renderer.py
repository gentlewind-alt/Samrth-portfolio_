"""HTML portfolio renderer — "S. RAWAT" portfolio design.

Drop-in replacement for backend/app/utils/renderer.py.
render_portfolio_html(resume_data, resume_id) keeps the original signature, so
routers.py, the Next.js preview and export.py all keep working unchanged.

Static assets the page expects next to index.html when exported:
    vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg
    assets/chiyo/s-01.jpg ... s-23.jpg          (Chiyo mode frames)
"""
from typing import Any, Dict, List, Tuple
import datetime
import html as _html
import re

MONO = "font-family:'IBM Plex Mono',monospace"
ICON = "font-family:'Material Symbols Outlined';font-variation-settings:'wght' 300,'opsz' 24;font-size:18px;line-height:1"

HOBBY_ICONS = [
    (("movie", "film", "cinema"), "movie_filter"),
    (("podcast",), "podcasts"),
    (("music", "song", "listen"), "headset"),
    (("read", "book", "story"), "menu_book"),
    (("build", "making", "tinker", "innovat"), "build"),
    (("learn", "explor", "travel"), "explore"),
    (("game", "gaming"), "sports_esports"),
    (("write", "blog"), "edit_note"),
]


def _esc(value: Any) -> str:
    return _html.escape(str(value or ""), quote=True)


def _lines(text: Any) -> List[str]:
    if not text:
        return []
    raw = re.split(r"[\r\n]+|<br\s*/?>", str(text))
    return [l.strip(" \u2022-\t") for l in raw if l.strip(" \u2022-\t")]


def _split_title(line: str) -> Tuple[str, str]:
    for sep in (" — ", " – ", ": ", " - "):
        if sep in line:
            head, tail = line.split(sep, 1)
            return head.strip(), tail.strip()
    return line.strip(), ""


def _hobby_icon(name: str) -> str:
    low = name.lower()
    for keys, icon in HOBBY_ICONS:
        if any(k in low for k in keys):
            return icon
    return "star"


def _skills_html(skills: Dict[str, Any]) -> str:
    rows = _lines(skills.get("body"))
    if not rows:
        return ""
    out = []
    for idx, line in enumerate(rows):
        label, values = (line.split(":", 1) + [""])[:2] if ":" in line else (line, "")
        bottom = ";border-bottom:1px solid #c4c7c7" if idx == len(rows) - 1 else ""
        out.append(
            f'<div class="row-hv" style="display:grid;grid-template-columns:150px 1fr;gap:20px;'
            f'padding:14px 0;border-top:1px solid #c4c7c7{bottom};'
            f'transition:padding-left .35s cubic-bezier(.16,1,.3,1)">'
            f'<span style="{MONO};font-size:10px;letter-spacing:.12em;text-transform:uppercase;'
            f'color:#8a8d8d">{_esc(label.strip())}</span>'
            f'<span style="font-size:14px;line-height:1.5;color:#1a1c19">{_esc(values.strip())}</span></div>'
        )
    return "\n".join(out)


def _tags_html(raw: str, small: bool = False) -> str:
    pad = "4px 9px" if small else "3px 8px"
    hover = "" if small else ' class="tag-hv"'
    trans = "" if small else ";transition:background-color .25s ease,border-color .25s ease,color .25s ease"
    tags = [t.strip() for t in re.split(r"[,/|]", raw) if t.strip()]
    return "\n".join(
        f'<span{hover} style="{MONO};font-size:10px;color:#5e5e5e;border:1px solid #d6d6d0;'
        f'padding:{pad}{trans}">{_esc(t)}</span>'
        for t in tags
    )


def _projects_html(proj: Dict[str, Any]) -> Tuple[str, str, int]:
    """Returns (list rows, case-study panels, project count)."""
    entries = _lines(proj.get("body"))
    rows, cases = [], []
    for idx, line in enumerate(entries):
        title, rest = _split_title(line)
        tech = ""
        match = re.search(r"\(([^)]*)\)\s*$", rest)
        if match:
            tech = match.group(1)
            rest = rest[: match.start()].strip()
        num = f"/{idx + 1:02d}"
        rows.append(
            f'<div data-act="open" data-open="{idx}" data-reveal="1" class="proj-hv" '
            f'style="display:grid;grid-template-columns:40px minmax(0,1.25fr) minmax(0,1fr) 138px;gap:22px;'
            f'align-items:start;padding:26px 8px;border-bottom:1px solid #c4c7c7;cursor:pointer;'
            f'transition:background-color .4s ease, padding-left .4s cubic-bezier(.16,1,.3,1)">'
            f'<span style="{MONO};font-size:11px;color:#8a8d8d;padding-top:5px">{num}</span>'
            f'<div><h3 style="font-family:Bitter,serif;font-weight:400;font-size:clamp(20px,1.75vw,27px);'
            f'line-height:1.15;margin:0 0 6px 0;letter-spacing:-.01em;overflow-wrap:break-word;hyphens:auto">'
            f'{_esc(title)}</h3></div>'
            f'<div style="display:flex;flex-direction:column;gap:12px">'
            f'<p style="font-size:13px;line-height:1.62;color:#444748;margin:0;text-wrap:pretty">{_esc(rest)}</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px">{_tags_html(tech)}</div></div>'
            f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:12px;padding-top:4px">'
            f'<span style="display:inline-flex;align-items:center;gap:6px;{MONO};font-size:10px;'
            f'letter-spacing:.1em;text-transform:uppercase;color:#747878">'
            f'<span style="width:6px;height:6px;border-radius:9999px;background:var(--accent)"></span>Completed</span>'
            f'<span style="display:inline-flex;align-items:center;gap:7px;font-size:10px;font-weight:600;'
            f'letter-spacing:.14em;text-transform:uppercase;color:#111">Case study '
            f'<span style="{ICON};font-size:17px">arrow_forward</span></span></div></div>'
        )
        cases.append(
            f'<div class="case" data-case="{idx}" style="display:none">'
            f'<span style="{MONO};font-size:11px;color:#8a8d8d">{num}</span>'
            f'<h2 style="font-family:Bitter,serif;font-weight:300;font-size:48px;line-height:1.05;'
            f'letter-spacing:-.02em;margin:10px 0 8px 0">{_esc(title)}</h2>'
            f'<p style="font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#747878;'
            f'margin:0 0 30px 0">Completed</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:34px">{_tags_html(tech, True)}</div>'
            f'<div style="display:flex;flex-direction:column;gap:26px"><div>'
            f'<h4 style="{MONO};font-size:10px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;'
            f'color:#444748;margin:0 0 10px 0">Overview</h4>'
            f'<p style="font-size:15px;line-height:1.7;color:#1a1c19;margin:0;text-wrap:pretty">{_esc(rest)}</p>'
            f'</div></div></div>'
        )
    return "\n".join(rows), "\n".join(cases), len(entries)


def _edu_html(edu: Dict[str, Any]) -> str:
    entries = _lines(edu.get("body"))
    out = []
    for idx, line in enumerate(entries):
        title, rest = _split_title(line)
        year = (re.search(r"(19|20)\d{2}", line) or [""])[0] if re.search(r"(19|20)\d{2}", line) else ""
        accent = "var(--accent)" if idx == 0 else "#c4c7c7"
        pad = "" if idx == len(entries) - 1 else ";padding-bottom:26px"
        out.append(
            f'<div style="position:relative{pad}">'
            f'<div style="position:absolute;left:-26px;top:5px;width:7px;height:7px;border-radius:9999px;'
            f'background:{accent}"></div>'
            f'<p style="{MONO};font-size:10px;letter-spacing:.14em;color:#8a8d8d;margin:0 0 5px 0">{_esc(year)}</p>'
            f'<h4 style="font-family:Bitter,serif;font-size:17px;font-weight:500;line-height:1.3;'
            f'margin:0 0 3px 0">{_esc(title)}</h4>'
            f'<p style="font-size:13px;color:#444748;margin:0">{_esc(rest)}</p></div>'
        )
    return "\n".join(out)


def _interests_html(values: List[str]) -> str:
    return "\n".join(
        f'<span class="chip-hv" style="font-size:12px;letter-spacing:.02em;border:1px solid #c4c7c7;'
        f'padding:6px 12px;transition:background-color .3s ease, border-color .3s ease">{_esc(v)}</span>'
        for v in values
    )


def _strengths_html(strengths: Dict[str, Any]) -> str:
    return "\n".join(
        f'<p style="font-size:13px;line-height:1.65;color:#444748;margin:0;text-wrap:pretty">{_esc(s)}</p>'
        for s in _lines(strengths.get("body"))
    )


def _hobbies_html(hobbies: Dict[str, Any]) -> str:
    items: List[str] = []
    for line in _lines(hobbies.get("body")):
        items.extend([p.strip() for p in line.split(",") if p.strip()])
    return "\n".join(
        f'<span style="display:inline-flex;align-items:center;gap:7px;font-size:11px;letter-spacing:.1em;'
        f'text-transform:uppercase;color:#747878">'
        f'<span style="{ICON}">{_hobby_icon(item)}</span>{_esc(item)}</span>'
        for item in items
    )


def _links_html(links: List[str]) -> str:
    out = []
    for link in [l for l in (links or []) if l]:
        label = "GitHub" if "github" in link else "LinkedIn" if "linkedin" in link else link.split("/")[-1] or link
        out.append(
            f'<a class="link-hv" href="{_esc(link)}" target="_blank" rel="noopener noreferrer" '
            f'style="font-size:13px;color:#1a1c19;border-bottom:1px solid #c4c7c7;padding-bottom:2px;'
            f'transition:border-color .3s ease">{_esc(label)}</a>'
        )
    return "\n".join(out)


def _about_html(desc: Dict[str, Any]) -> Tuple[str, str]:
    paras = _lines(desc.get("body"))
    lead = paras[0] if paras else ""
    rest = paras[1:] if len(paras) > 1 else []
    lead_html = (
        f'<p style="font-family:Bitter,serif;font-size:19px;line-height:1.6;color:#1a1c19;'
        f'margin:0 0 22px 0;text-wrap:pretty">{_esc(lead)}</p>'
    )
    for para in rest:
        lead_html += (
            f'\n<p style="font-size:14px;line-height:1.7;color:#444748;margin:0 0 28px 0;'
            f'text-wrap:pretty">{_esc(para)}</p>'
        )
    return lead_html, lead


def render_portfolio_html(resume_data: Dict[str, Any], resume_id: int) -> str:
    """Render the complete portfolio HTML from parsed resume data."""
    name = str(resume_data.get("name") or "Portfolio").strip()
    parts = name.split()
    first = parts[0] if parts else name
    last = " ".join(parts[1:]) if len(parts) > 1 else ""
    short = f"{first[0]}. {parts[-1]}".upper() if len(parts) > 1 else name.upper()

    desc = resume_data.get("description", {}) or {}
    proj = resume_data.get("project", {}) or {}
    edu = resume_data.get("education", {}) or {}
    skills = resume_data.get("skills", {}) or {}
    hobbies = resume_data.get("hobbies", {}) or {}
    strengths = resume_data.get("strengths", {}) or {}
    address = str(resume_data.get("address") or "")

    about_html, summary = _about_html(desc)
    project_rows, case_panels, project_count = _projects_html(proj)
    edu_body = str(edu.get("body") or "")
    cgpa = (re.search(r"CGPA\s*:?\s*([\d.]+)", edu_body, re.I) or [None, "—"])[1]
    years = re.findall(r"(?:19|20)\d{2}", edu_body)
    grad_year = max(years) if years else str(datetime.date.today().year)
    location = address.split(",")[-2].strip() if address.count(",") >= 2 else address

    interests = [i.strip() for i in re.split(r"[,\n]", str(resume_data.get("interests") or "")) if i.strip()]
    if not interests:
        interests = ["LLMs", "Agentic AI", "Deep Learning", "IoT Systems", "Embedded Systems", "Data Visualization"]

    values = {
        "%%NAME%%": _esc(name),
        "%%SHORTNAME%%": _esc(short),
        "%%FIRSTNAME%%": _esc(first),
        "%%LASTNAME%%": _esc(last),
        "%%SUMMARY%%": _esc(summary),
        "%%EMAIL%%": _esc(resume_data.get("email") or ""),
        "%%PHONE%%": _esc(resume_data.get("number") or ""),
        "%%ADDRESS%%": _esc(address),
        "%%LOCATION%%": _esc(location),
        "%%RESUME_URL%%": f"/api/resumes/{resume_id}/pdf",
        "%%YEAR%%": str(datetime.date.today().year),
        "%%CGPA%%": _esc(cgpa),
        "%%NPROJECTS%%": f"{project_count:02d}",
        "%%GRADYEAR%%": _esc(grad_year),
        "%%ABOUT%%": about_html,
        "%%SKILLS%%": _skills_html(skills),
        "%%PROJECTS%%": project_rows,
        "%%CASES%%": case_panels,
        "%%EDU%%": _edu_html(edu),
        "%%INTERESTS%%": _interests_html(interests),
        "%%STRENGTHS%%": _strengths_html(strengths),
        "%%HOBBIES%%": _hobbies_html(hobbies),
        "%%LINKS%%": _links_html(resume_data.get("links", [])),
    }

    html = TEMPLATE
    for token, value in values.items():
        html = html.replace(token, value)
    return html


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%%NAME%% — Applied AI Systems</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@300;400;500;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0&display=swap" rel="stylesheet" />
<style>

  html { scroll-behavior: smooth; }
  body { margin: 0; background-color: #fafaf5; color: #1a1c19; font-family: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif; --accent: #22c55e; }
  body, body * { -webkit-user-select: none; user-select: none; }
  a { color: inherit; text-decoration: none; }
  a:hover { color: #000000; }
  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-track { background: #f1f1ec; }
  ::-webkit-scrollbar-thumb { background: #c4c7c7; }
  ::-webkit-scrollbar-thumb:hover { background: #747878; }
  @keyframes soft-pulse { 0%,100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,.35); } 50% { transform: scale(1.25); opacity: .65; box-shadow: 0 0 8px 2px rgba(34,197,94,.18); } }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
  @keyframes maskUp { from { transform: translateY(105%) skewY(4deg); } to { transform: translateY(0) skewY(0); } }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes panelIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
  @keyframes backdropIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes gridDrift { from { background-position: 0 0, 0 0; } to { background-position: 32px 32px, 32px 32px; } }
  @keyframes ruleGrow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
  @keyframes sway { 0%, 100% { transform: rotate(-0.7deg) translateY(0) scale(1); } 50% { transform: rotate(0.8deg) translateY(-14px) scale(1.012); } }
  @keyframes swayAlt { 0%, 100% { transform: scaleX(-1) rotate(0.6deg) translateY(-10px); } 50% { transform: scaleX(-1) rotate(-0.9deg) translateY(6px); } }
  @keyframes inkIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes chiyoSheen { from { background-position: 150% 0; } to { background-position: -50% 0; } }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; transition: none !important; } }

.hv-0:hover{border-color:#111 !important}
.hv-1:hover{color:#000 !important;padding-left:6px !important}
.hv-2:hover{color:#000 !important;padding-left:6px !important}
.hv-3:hover{color:#000 !important;padding-left:6px !important}
.hv-4:hover{color:#000 !important;padding-left:6px !important}
.hv-5:hover{color:#000 !important;padding-left:6px !important}
.hv-6:hover{color:#000 !important;padding-left:6px !important}
.hv-7:hover{color:#000 !important;padding-left:6px !important}
.hv-8:hover{border-color:#111 !important;background:rgba(238,238,233,.75) !important}
.hv-9:hover{transform:translateY(-2px) !important;background:#000 !important;color:#fafaf5 !important}
.hv-10:hover{transform:translateY(-2px) !important;background:#efefe9 !important}
.hv-11:hover{color:#000 !important;border-color:#000 !important}
.hv-12:hover{background:rgba(238,238,233,.75) !important;padding-left:18px !important}
.hv-13:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-14:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-15:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-16:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-17:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-18:hover{background:rgba(238,238,233,.75) !important;padding-left:18px !important}
.hv-19:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-20:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-21:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-22:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-23:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-24:hover{background:rgba(238,238,233,.75) !important;padding-left:18px !important}
.hv-25:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-26:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-27:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-28:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-29:hover{background:rgba(238,238,233,.75) !important;padding-left:18px !important}
.hv-30:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-31:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-32:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-33:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-34:hover{padding-left:8px !important}
.hv-35:hover{padding-left:8px !important}
.hv-36:hover{padding-left:8px !important}
.hv-37:hover{padding-left:8px !important}
.hv-38:hover{padding-left:8px !important}
.hv-39:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-40:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-41:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-42:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-43:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-44:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-45:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-46:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.hv-47:hover{border-color:#111 !important;gap:18px !important}
.hv-48:hover{border-color:#111 !important}
.hv-49:hover{border-color:#111 !important}
.hv-50:hover{background:#111 !important;color:#fafaf5 !important;border-color:#111 !important}
.hv-51:hover{transform:translateY(-2px) !important;color:#fafaf5 !important}
.row-hv:hover{padding-left:8px !important}
.proj-hv:hover{background:rgba(238,238,233,.75) !important;padding-left:18px !important}
.tag-hv:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.chip-hv:hover{background:#111 !important;border-color:#111 !important;color:#fafaf5 !important}
.link-hv:hover{border-color:#111 !important}
</style>
</head>
<body>
<div style="min-height:100vh;background:#fafaf5;color:#1a1c19;position:relative;overflow-x:hidden;--accent:#22c55e;transition:background-color .6s ease" id="root">

<div id="chiyoWrap" style="display:none">
<div style="position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0">
<div id="chiyoLayer" style="position:absolute;inset:0;opacity:.94;filter:saturate(1.05)">
<img data-frame="1" src="assets/chiyo/s-01.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:1" />
<img data-frame="2" src="assets/chiyo/s-02.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="3" src="assets/chiyo/s-03.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="4" src="assets/chiyo/s-04.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="5" src="assets/chiyo/s-05.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="6" src="assets/chiyo/s-06.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="7" src="assets/chiyo/s-07.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="8" src="assets/chiyo/s-08.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="9" src="assets/chiyo/s-09.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="10" src="assets/chiyo/s-10.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="11" src="assets/chiyo/s-11.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="19" src="assets/chiyo/s-19.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="20" src="assets/chiyo/s-20.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="21" src="assets/chiyo/s-21.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="22" src="assets/chiyo/s-22.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
<img data-frame="23" src="assets/chiyo/s-23.jpg" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0" />
</div>
<div style="position:absolute;inset:0;background:#241531;opacity:0;mix-blend-mode:multiply" id="chiyoVeil"></div>
<div style="position:absolute;inset:0;background:radial-gradient(ellipse 70% 60% at 78% 45%, transparent 0%, rgba(26,15,38,.28) 78%)"></div>
</div>
<div style="position:fixed;inset:0;pointer-events:none;z-index:1;background:#fafaf5;opacity:0" id="chiyoScrim"></div>
</div>

<div style="position:fixed;inset:0;overflow:hidden;pointer-events:none;z-index:0;animation:inkIn 2.6s ease-out both">
<div  style="position:absolute;left:-4vw;bottom:-16vh;height:132vh;will-change:transform">
<img src="vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg" alt="" style="height:100%;width:auto;display:block;opacity:.12;mix-blend-mode:multiply;transform-origin:50% 100%;animation:sway 26s ease-in-out infinite" />
</div>
<div  style="position:absolute;right:-12vw;bottom:-28vh;height:172vh;will-change:transform">
<img src="vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg" alt="" style="height:100%;width:auto;display:block;opacity:.075;mix-blend-mode:multiply;transform-origin:50% 100%;animation:swayAlt 37s ease-in-out infinite" />
</div>
<div  style="position:absolute;left:36vw;bottom:-10vh;height:86vh;will-change:transform">
<img src="vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg" alt="" style="height:100%;width:auto;display:block;opacity:.05;filter:blur(1.4px);mix-blend-mode:multiply;transform-origin:50% 100%;animation:sway 46s ease-in-out infinite reverse" />
</div>
<div style="position:absolute;inset:0;background:radial-gradient(ellipse 64% 54% at 44% 40%, rgba(250,250,245,.88) 0%, rgba(250,250,245,.52) 46%, rgba(250,250,245,0) 80%)"></div>
</div>
<canvas id="field" style="position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:1"></canvas>
<div style="background-image:linear-gradient(#9a9a92 1px, transparent 1px), linear-gradient(90deg, #9a9a92 1px, transparent 1px);background-size:32px 32px;opacity:.055;position:fixed;inset:0;pointer-events:none;z-index:1;animation:gridDrift 24s linear infinite"></div>

<div id="ring" style="position:fixed;top:0;left:0;width:34px;height:34px;border:1px solid rgba(26,28,25,.45);border-radius:9999px;pointer-events:none;z-index:9999;opacity:0;transform:translate3d(-100px,-100px,0);transition:width .25s ease, height .25s ease, background-color .25s ease, border-color .25s ease"></div>
<div id="dot" style="position:fixed;top:0;left:0;width:5px;height:5px;background:#1a1c19;border-radius:9999px;pointer-events:none;z-index:9999;opacity:0;transform:translate3d(-100px,-100px,0)"></div>

<div style="position:fixed;top:0;left:0;right:0;height:2px;background:transparent;z-index:60;pointer-events:none">
<div id="progress" style="height:100%;width:100%;background:var(--accent);transform-origin:0 50%;transform:scaleX(0)"></div>
</div>

<aside style="height:100vh;width:264px;position:fixed;top:0;left:0;border-right:1px solid #c4c7c7;background-color:#fafaf5;background-image:url('vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg');background-size:cover;background-position:center;background-repeat:no-repeat;display:flex;flex-direction:column;padding:28px 24px;z-index:50;box-sizing:border-box;transition:width .35s cubic-bezier(.16,1,.3,1)" id="aside">
<button data-act="sidebar" style="position:absolute;top:24px;right:-13px;width:26px;height:26px;border-radius:9999px;border:1px solid #c4c7c7;background:#fafaf5;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:51;padding:0" class="hv-0">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'wght' 400,'opsz' 24;font-size:15px;line-height:1;color:#444748" id="sideIcon">chevron_left</span>
</button>
<div style="margin-bottom:36px">
<h1 style="font-size:12px;line-height:16px;font-weight:600;letter-spacing:.18em;color:#000;margin:0 0 5px 0;white-space:nowrap">%%SHORTNAME%%</h1>
<span class="side-label" style="display:contents">
<p style="font-size:10px;line-height:14px;font-weight:500;letter-spacing:.16em;color:#444748;margin:0;white-space:nowrap">APPLIED AI · EMBEDDED</p>
</span>
</div>
<nav style="flex-grow:1;position:relative">
<div style="position:absolute;left:-24px;top:0;width:2px;height:36px;background:var(--accent);transition:transform .5s cubic-bezier(.16,1,.3,1);transform:translateY(0px)" id="navInd"></div>
<div style="display:flex;flex-direction:column;gap:8px">
<a href="#home" data-act="nav" data-nav="0" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-1">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">home</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Home</span></span>
</a>
<a href="#projects" data-act="nav" data-nav="1" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-2">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">biotech</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Work</span></span>
</a>
<a href="#about" data-act="nav" data-nav="2" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-3">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">person</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">About</span></span>
</a>
<a href="#skills" data-act="nav" data-nav="3" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-4">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">psychology</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Stack</span></span>
</a>
<a href="#education" data-act="nav" data-nav="4" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-5">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">school</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Education</span></span>
</a>
<a href="#interests" data-act="nav" data-nav="5" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-6">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">interests</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Interests</span></span>
</a>
<a href="#contact" data-act="nav" data-nav="6" style="display:flex;align-items:center;gap:12px;height:36px;color:#444748;transition:color .3s ease, padding-left .35s cubic-bezier(.16,1,.3,1)" class="hv-7">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:19px;line-height:1">alternate_email</span>
<span class="side-label" style="display:contents"><span style="font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap">Contact</span></span>
</a>
</div>
</nav>
<div style="display:flex;flex-direction:column;gap:8px;padding-top:20px;border-top:1px solid rgba(196,199,199,.6)">
<div style="display:flex;align-items:center;gap:8px">
<span style="width:7px;height:7px;border-radius:9999px;background:var(--accent);animation:soft-pulse 2.4s cubic-bezier(.4,0,.6,1) infinite"></span>
<span class="side-label" style="display:contents"><span style="font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#1a1c19;white-space:nowrap">Open for freelance</span></span>
</div>
<span class="side-label" style="display:contents"><span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#747878;letter-spacing:.04em;white-space:nowrap">IST <span id="clock">--:--</span></span></span>
</div>
</aside>

<main style="margin-left:264px;min-height:100vh;position:relative;z-index:2;transition:margin-left .35s cubic-bezier(.16,1,.3,1)" id="main">
<div style="max-width:1240px;margin:0 auto;width:100%;padding:0 48px;box-sizing:border-box">

<section id="home" style="padding:104px 0 72px 0">
<div style="display:flex;align-items:center;gap:14px;margin-bottom:26px;overflow:hidden">
<span style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#747878;animation:fadeUp .7s ease-out both;animation-delay:.05s" data-metasoft="1">Applied AI Systems Engineer</span>
<span style="flex:1;height:1px;background:#c4c7c7;transform-origin:0 50%;animation:ruleGrow 1.1s cubic-bezier(.16,1,.3,1) both;animation-delay:.15s"></span>
<span id="slapWrap" style="display:none">
<span style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:#8a8d8d;white-space:nowrap" data-metasoft="1">Slaps landed <span id="slapCount">0</span></span>
</span>
<button data-act="chiyo" data-chiyo-toggle="1" style="display:inline-flex;align-items:center;gap:7px;border:1px solid #c4c7c7;background-color:rgba(250,250,245,.55);background-image:linear-gradient(100deg,rgba(255,255,255,0) 18%,color-mix(in oklch, var(--accent) 34%, transparent) 44%,rgba(255,255,255,0) 70%);background-size:220% 100%;background-repeat:no-repeat;animation:chiyoSheen 4.2s linear infinite;padding:7px 13px;cursor:pointer;font-family:inherit;white-space:nowrap;transition:border-color .3s ease" class="hv-8">
<span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 400,'GRAD' 0,'opsz' 24;font-size:15px;line-height:1;color:#8a8d8d" id="chiyoIcon">bolt</span>
<span style="font-size:9px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#1a1c19">Chiyo mode</span>
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.1em;color:#8a8d8d" id="chiyoStatus">OFF</span>
</button>
</div>
<h2 style="font-family:Bitter,serif;font-weight:300;font-size:clamp(56px,9.4vw,132px);line-height:.88;letter-spacing:-.025em;text-transform:uppercase;margin:0;color:#111">
<span style="display:block;overflow:hidden;padding-bottom:.04em"><span style="display:block;animation:maskUp .95s cubic-bezier(.16,1,.3,1) both;animation-delay:.1s">%%FIRSTNAME%%</span></span>
<span style="display:block;overflow:hidden;padding-bottom:.04em"><span style="display:block;animation:maskUp .95s cubic-bezier(.16,1,.3,1) both;animation-delay:.22s">%%LASTNAME%%</span></span>
</h2>
<div style="display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:56px;margin-top:44px;align-items:end">
<div style="animation:fadeUp .8s ease-out both;animation-delay:.5s">
<p style="font-family:Bitter,serif;font-size:21px;line-height:1.5;color:#1a1c19;margin:0 0 26px 0;max-width:44ch;text-wrap:pretty">%%SUMMARY%%</p>
<div style="display:flex;flex-wrap:wrap;gap:10px">
<a href="mailto:%%EMAIL%%" style="display:inline-flex;align-items:center;gap:10px;background:#111;color:#fafaf5;padding:14px 24px;font-size:10px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;transition:transform .35s cubic-bezier(.16,1,.3,1), background-color .3s ease" class="hv-9">Start a project <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:16px;line-height:1">arrow_outward</span></a>
<a href="%%RESUME_URL%%" download style="display:inline-flex;align-items:center;gap:10px;border:1px solid #747878;padding:14px 24px;font-size:10px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#111;transition:transform .35s cubic-bezier(.16,1,.3,1), background-color .3s ease" class="hv-10">Download resume <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:16px;line-height:1">download</span></a>
</div>
</div>
<div style="border:1px solid #c4c7c7;background:rgba(244,244,239,.72);backdrop-filter:blur(2px);padding:18px 20px;animation:fadeUp .8s ease-out both;animation-delay:.62s">
<div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid #c4c7c7">
<h3 style="font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:500;letter-spacing:.16em;text-transform:uppercase;margin:0;color:#444748">System dashboard</h3>
<span style="width:7px;height:7px;border-radius:9999px;background:var(--accent);animation:soft-pulse 2.4s cubic-bezier(.4,0,.6,1) infinite"></span>
</div>
<div style="display:flex;flex-direction:column;gap:13px">
<div style="display:grid;grid-template-columns:78px 1fr;gap:12px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#8a8d8d">Now</span>
<span style="font-size:13px;line-height:1.45;color:#1a1c19;min-height:19px"><span id="ticker">Building AI-driven applications</span><span style="animation:blink 1s step-end infinite;color:var(--accent)">▌</span></span>
</div>
<div style="display:grid;grid-template-columns:78px 1fr;gap:12px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#8a8d8d">Based</span>
<span style="font-size:13px;line-height:1.45;color:#1a1c19">%%LOCATION%%</span>
</div>
<div style="display:grid;grid-template-columns:78px 1fr;gap:12px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#8a8d8d">Focus</span>
<span style="font-size:13px;line-height:1.45;color:#1a1c19">Agentic AI · Embedded Systems</span>
</div>
<div style="display:grid;grid-template-columns:78px 1fr;gap:12px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#8a8d8d">Local</span>
<span style="font-family:'IBM Plex Mono',monospace;font-size:13px;line-height:1.45;color:#1a1c19" id="clockFull">--:--:--</span>
</div>
</div>
</div>
</div>
</section>

<section id="projects" data-reveal="1" style="padding-bottom:8px">
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:22px">
<div>
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8a8d8d;margin:0 0 6px 0">01 — Selected work</p>
<h2 style="font-family:Bitter,serif;font-weight:400;font-size:34px;line-height:1.1;text-transform:uppercase;letter-spacing:-.01em;margin:0">Projects / Open-Source</h2>
</div>
<a href="https://drive.google.com/drive/folders/1vqfYWG1C3KA-rb_5DO1uI2awG5tGS_9O?usp=sharing" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:6px;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#444748;border-bottom:1px solid #c4c7c7;padding-bottom:3px;transition:color .3s ease, border-color .3s ease" class="hv-11">View all <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:15px;line-height:1">arrow_outward</span></a>
</div>
<div style="border-top:1px solid #c4c7c7">
%%PROJECTS%%
</div>
</section>

<section id="about" data-reveal="1" style="padding:72px 0 0 0">
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8a8d8d;margin:0 0 26px 0">02 — Profile</p>
<div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:64px;align-items:start">
<div>
%%ABOUT%%
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;padding-top:22px;border-top:1px solid #c4c7c7">
<div>
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d;display:block;margin-bottom:6px">CGPA</span>
<span style="font-family:Bitter,serif;font-size:30px;font-weight:400;line-height:1">%%CGPA%%</span>
</div>
<div>
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d;display:block;margin-bottom:6px">Projects</span>
<span style="font-family:Bitter,serif;font-size:30px;font-weight:400;line-height:1">%%NPROJECTS%%</span>
</div>
<div>
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d;display:block;margin-bottom:6px">Grad year</span>
<span style="font-family:Bitter,serif;font-size:30px;font-weight:400;line-height:1">%%GRADYEAR%%</span>
</div>
</div>
</div>
<div id="skills">
<h3 style="font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:#444748;margin:0 0 18px 0">Technical stack</h3>
<div style="display:flex;flex-direction:column">
%%SKILLS%%
</div>
</div>
</div>
</section>

<section data-reveal="1" style="padding:72px 0 0 0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:64px;align-items:start">
<div id="education">
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8a8d8d;margin:0 0 26px 0">03 — Education</p>
<div style="position:relative;padding-left:26px">
<div style="position:absolute;left:3px;top:6px;bottom:6px;width:1px;background:#c4c7c7"></div>
%%EDU%%
</div>
</div>
<div id="interests">
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8a8d8d;margin:0 0 26px 0">04 — Interests &amp; strengths</p>
<div style="display:flex;flex-wrap:wrap;gap:7px;margin-bottom:26px">
%%INTERESTS%%
</div>
<div style="display:flex;flex-direction:column;gap:14px;padding-top:22px;border-top:1px solid #c4c7c7">
%%STRENGTHS%%
</div>
<div style="display:flex;flex-wrap:wrap;gap:18px;margin-top:26px;padding-top:20px;border-top:1px solid #c4c7c7">
%%HOBBIES%%
</div>
</div>
</section>

<section id="contact" data-reveal="1" style="padding:96px 0 72px 0;margin-top:72px;border-top:1px solid #c4c7c7">
<div style="display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:64px;align-items:start">
<div>
<h2 style="font-family:Bitter,serif;font-weight:300;font-size:clamp(38px,5vw,64px);line-height:1.02;letter-spacing:-.02em;margin:0 0 24px 0;text-transform:uppercase">Let's build<br />something</h2>
<a href="mailto:%%EMAIL%%" style="display:inline-flex;align-items:center;gap:12px;font-family:Bitter,serif;font-size:22px;color:#111;border-bottom:1px solid #c4c7c7;padding-bottom:6px;transition:border-color .35s ease, gap .35s cubic-bezier(.16,1,.3,1)" class="hv-47">%%EMAIL%% <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:22px;line-height:1">arrow_outward</span></a>
</div>
<div style="display:flex;flex-direction:column;gap:26px">
<div style="display:grid;grid-template-columns:80px 1fr;gap:14px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d">Phone</span>
<span style="font-size:13px;color:#1a1c19">%%PHONE%%</span>
</div>
<div style="display:grid;grid-template-columns:80px 1fr;gap:14px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d">Located</span>
<span style="font-size:13px;line-height:1.55;color:#1a1c19">%%ADDRESS%%</span>
</div>
<div style="display:grid;grid-template-columns:80px 1fr;gap:14px;align-items:baseline">
<span style="font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:.16em;text-transform:uppercase;color:#8a8d8d">Online</span>
<span style="display:flex;gap:18px">
%%LINKS%%
</span>
</div>
</div>
</div>
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:80px;padding-top:22px;border-top:1px solid #c4c7c7">
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.1em;color:#8a8d8d;margin:0">© %%YEAR%% %%NAME%%</p>
<p style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.1em;color:#8a8d8d;margin:0">&gt; designed &amp; built with purpose</p>
</div>
</section>

</div>
</main>

<div id="panelWrap" style="display:none">
<div data-act="close" style="position:fixed;inset:0;background:rgba(17,17,17,.32);z-index:80;animation:backdropIn .35s ease-out both;backdrop-filter:blur(2px)"></div>
<aside style="position:fixed;top:0;right:0;height:100vh;width:min(660px,92vw);background:#fafaf5;border-left:1px solid #c4c7c7;z-index:90;overflow-y:auto;box-shadow:-24px 0 60px rgba(17,17,17,.1);animation:panelIn .5s cubic-bezier(.16,1,.3,1) both">
<div style="position:sticky;top:0;background:rgba(250,250,245,.94);backdrop-filter:blur(6px);border-bottom:1px solid #c4c7c7;display:flex;justify-content:space-between;align-items:center;padding:20px 40px;z-index:2">
<span style="font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#8a8d8d">Case study</span>
<button data-act="close" style="display:inline-flex;align-items:center;gap:8px;background:none;border:1px solid #c4c7c7;padding:8px 14px;font-family:'IBM Plex Sans',sans-serif;font-size:10px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#111;cursor:pointer;transition:background-color .3s ease, border-color .3s ease" class="hv-50">Close <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:16px;line-height:1">close</span></button>
</div>
<div style="padding:44px 40px 80px 40px">

%%CASES%%
<div style="margin-top:44px;padding-top:26px;border-top:1px solid #c4c7c7;display:flex;justify-content:space-between;align-items:center">
<span style="font-size:13px;color:#747878">Want something like this built?</span>
<a href="mailto:%%EMAIL%%" style="display:inline-flex;align-items:center;gap:10px;background:#111;color:#fafaf5;padding:12px 22px;font-size:10px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;transition:transform .3s ease" class="hv-51">Get in touch <span style="font-family:'Material Symbols Outlined';font-variation-settings:'FILL' 0,'wght' 300,'GRAD' 0,'opsz' 24;font-size:16px;line-height:1">arrow_outward</span></a>
</div>
</div>
</aside>
</div>

</div>
<script>
(function () {
  var SECTIONS = ['home','projects','about','skills','education','interests','contact'];
  var TICKER = ['Building AI-driven applications','Merging machine learning, IoT and web','Shipping firmware on 400KB of RAM','Taking on freelance work'];
  var IDLE = [1,2,3,4], SLAP = [5,6,7,8,9,10,11], FAST = [19,20,21,22,23];
  var FAST_WINDOW_MS = 290, SLAP_DELAY_MS = 90, SLAP_VOLUME = 0.6, START_CHIYO_ON = true, MOTION = 'confident', CURSOR = true;
  var INK = "url('vectorizer/fee93e0d-1d82-4761-8be5-4d277d0f6bfa.svg')";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var chiyoOn = false, chiyoFrame = 1, chiyoBusy = false, chiyoReady = false, lastClick = 0, idleTimer, seqTimer, watchdog;
  var slapCount = parseInt(localStorage.getItem('chiyoSlapCount') || '0', 10) || 0;
  var sidebarCollapsed = false, active = 0, actx;
  var layer = $('#chiyoLayer');

  $('#slapCount').textContent = slapCount;

  function paintChiyo() {
    if (!layer) return;
    for (var i = 0; i < layer.children.length; i++) {
      var f = parseInt(layer.children[i].getAttribute('data-frame'), 10);
      layer.children[i].style.opacity = f === chiyoFrame ? '1' : '0';
    }
  }
  function waitForFrames() {
    if (!layer) { chiyoReady = true; return Promise.resolve(); }
    return Promise.all($('img', layer).map(function (img) { return img.decode ? img.decode().catch(function(){}) : Promise.resolve(); }))
      .then(function () { chiyoReady = true; });
  }
  function startIdle() {
    clearInterval(idleTimer);
    idleTimer = setInterval(function () {
      if (!chiyoOn || chiyoBusy) return;
      chiyoFrame = IDLE[(IDLE.indexOf(chiyoFrame) + 1) % IDLE.length];
      paintChiyo();
    }, 480);
  }
  function synthSlap(volume) {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!actx) actx = new AC();
    if (actx.state === 'suspended') actx.resume();
    var t = actx.currentTime, len = Math.floor(actx.sampleRate * 0.16);
    var buf = actx.createBuffer(1, len, actx.sampleRate), d = buf.getChannelData(0);
    for (var i = 0; i < len; i++) { var p = i / len; d[i] = (Math.random() * 2 - 1) * Math.pow(1 - p, 5); }
    var noise = actx.createBufferSource(); noise.buffer = buf;
    var bp = actx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1650; bp.Q.value = 0.85;
    var g = actx.createGain(); g.gain.setValueAtTime(volume, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    var body = actx.createOscillator(); body.type = 'sine';
    body.frequency.setValueAtTime(190, t); body.frequency.exponentialRampToValueAtTime(70, t + 0.09);
    var bg = actx.createGain(); bg.gain.setValueAtTime(volume * 0.5, t); bg.gain.exponentialRampToValueAtTime(0.0001, t + 0.1);
    noise.connect(bp).connect(g).connect(actx.destination);
    body.connect(bg).connect(actx.destination);
    noise.start(t); noise.stop(t + 0.16); body.start(t); body.stop(t + 0.1);
  }
  function slapSound() { setTimeout(function () { synthSlap(SLAP_VOLUME); }, SLAP_DELAY_MS); }

  function handleSlap(e) {
    if (!chiyoOn || !chiyoReady) return;
    if (e && e.target && e.target.closest && e.target.closest('[data-chiyo-toggle]')) return;
    var now = Date.now();
    var fast = now - lastClick < FAST_WINDOW_MS;
    lastClick = now;
    clearTimeout(seqTimer);
    var seq = fast ? FAST : SLAP, stepMs = fast ? 55 : 70;
    slapSound();
    slapCount += 1;
    localStorage.setItem('chiyoSlapCount', String(slapCount));
    $('#slapCount').textContent = slapCount;
    chiyoBusy = true;
    var i = 0;
    (function step() {
      chiyoFrame = seq[i]; paintChiyo(); i++;
      if (i < seq.length) seqTimer = setTimeout(step, stepMs);
      else seqTimer = setTimeout(function () { chiyoBusy = false; chiyoFrame = 1; paintChiyo(); }, 220);
    })();
    clearTimeout(watchdog);
    watchdog = setTimeout(function () { chiyoBusy = false; chiyoFrame = 1; paintChiyo(); }, seq.length * stepMs + 600);
  }

  function setChiyo(on) {
    chiyoOn = on; chiyoFrame = 1; chiyoBusy = false;
    $('#chiyoWrap').style.display = on ? 'block' : 'none';
    $('#slapWrap').style.display = on ? 'contents' : 'none';
    var aside = $('#aside');
    aside.style.backgroundColor = on ? 'transparent' : '#fafaf5';
    aside.style.backgroundImage = on ? 'none' : INK;
    $('#chiyoIcon').style.fontVariationSettings = "'FILL' " + (on ? 1 : 0) + ",'wght' 400,'GRAD' 0,'opsz' 24";
    $('#chiyoIcon').style.color = on ? 'var(--accent)' : '#8a8d8d';
    $('#chiyoStatus').style.color = on ? 'var(--accent)' : '#8a8d8d';
    $('#chiyoStatus').textContent = on ? 'ON' : 'OFF';
    $('#root').style.textShadow = on ? '0 0 5px rgba(250,250,245,.72),0 0 1px rgba(250,250,245,.9)' : '';
    $('[data-metasoft]').forEach(function (el) { el.style.color = on ? '#4a4d4d' : ''; });
    if (on) { paintChiyo(); if (!chiyoReady) waitForFrames().then(startIdle); else startIdle(); }
  }

  function setSidebar(collapsed) {
    sidebarCollapsed = collapsed;
    $('#aside').style.width = collapsed ? '76px' : '264px';
    $('#main').style.marginLeft = collapsed ? '76px' : '264px';
    $('#sideIcon').textContent = collapsed ? 'chevron_right' : 'chevron_left';
    $('.side-label').forEach(function (el) { el.style.display = collapsed ? 'none' : 'contents'; });
  }
  function setActive(i) { active = i; $('#navInd').style.transform = 'translateY(' + i * 44 + 'px)'; }
  function openCase(i) {
    $('.case').forEach(function (el) { el.style.display = el.getAttribute('data-case') === String(i) ? 'block' : 'none'; });
    $('#panelWrap').style.display = 'block';
  }

  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('[data-act]') : null;
    if (!el) return;
    var act = el.getAttribute('data-act');
    if (act === 'chiyo') setChiyo(!chiyoOn);
    else if (act === 'sidebar') setSidebar(!sidebarCollapsed);
    else if (act === 'nav') setActive(parseInt(el.getAttribute('data-nav'), 10) || 0);
    else if (act === 'open') openCase(el.getAttribute('data-open'));
    else if (act === 'close') $('#panelWrap').style.display = 'none';
  });
  document.addEventListener('pointerdown', handleSlap);

  function tickClock() {
    var opts = { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit', hour12: false };
    $('#clock').textContent = new Intl.DateTimeFormat('en-GB', opts).format(new Date());
    $('#clockFull').textContent = new Intl.DateTimeFormat('en-GB', Object.assign({ second: '2-digit' }, opts)).format(new Date()) + ' IST';
  }
  tickClock(); setInterval(tickClock, 1000);
  var tIdx = 0;
  setInterval(function () { tIdx = (tIdx + 1) % TICKER.length; $('#ticker').textContent = TICKER[tIdx]; }, 4200);

  var progress = $('#progress');
  function onScroll() {
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    progress.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, h.scrollTop / max) : 0) + ')';
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  var revealObs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.style.opacity = '1'; e.target.style.transform = 'none'; revealObs.unobserve(e.target); }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });
  $('[data-reveal]').forEach(function (el) {
    if (reduced) return;
    el.style.opacity = '0';
    el.style.transform = 'translateY(22px)';
    el.style.transition = 'opacity .9s cubic-bezier(.16,1,.3,1), transform .9s cubic-bezier(.16,1,.3,1)';
    revealObs.observe(el);
  });
  setTimeout(function () { $('[data-reveal]').forEach(function (el) { el.style.opacity = '1'; el.style.transform = 'none'; }); }, 2600);

  var sectionObs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { var i = SECTIONS.indexOf(e.target.id); if (i >= 0 && i !== active) setActive(i); }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  SECTIONS.forEach(function (id) { var el = document.getElementById(id); if (el) sectionObs.observe(el); });

  (function cursor() {
    if (!CURSOR || window.matchMedia('(pointer: coarse)').matches) return;
    var ring = $('#ring'), dot = $('#dot');
    if (!ring || !dot) return;
    var mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my, shown = false;
    window.addEventListener('mousemove', function (e) {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = 'translate3d(' + (mx - 2.5) + 'px,' + (my - 2.5) + 'px,0)';
      if (!shown) { shown = true; ring.style.opacity = '1'; dot.style.opacity = '1'; }
      var t = e.target;
      var grow = !!(t && t.closest && (t.closest('a,button,[role=button],[data-act]') || t.closest('div[style*="cursor:pointer"]')));
      ring.style.width = grow ? '54px' : '34px';
      ring.style.height = grow ? '54px' : '34px';
      ring.style.backgroundColor = grow ? 'rgba(26,28,25,.07)' : 'transparent';
      ring.style.borderColor = grow ? 'rgba(26,28,25,.75)' : 'rgba(26,28,25,.45)';
    }, { passive: true });
    (function loop() {
      var w = parseFloat(ring.style.width || '34');
      rx += (mx - rx) * 0.16; ry += (my - ry) * 0.16;
      ring.style.transform = 'translate3d(' + (rx - w / 2) + 'px,' + (ry - w / 2) + 'px,0)';
      requestAnimationFrame(loop);
    })();
  })();

  (function field() {
    var cv = $('#field');
    if (!cv || reduced || MOTION === 'calm') return;
    var ctx = cv.getContext('2d'), w = 0, h = 0, pts = [], mouse = { x: -999, y: -999 };
    var density = MOTION === 'showpiece' ? 13000 : 22000, speed = MOTION === 'showpiece' ? 0.22 : 0.13;
    function setup() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = cv.clientWidth; h = cv.clientHeight;
      cv.width = w * dpr; cv.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var n = Math.min(150, Math.round((w * h) / density));
      pts = [];
      for (var i = 0; i < n; i++) pts.push({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * speed, vy: (Math.random() - 0.5) * speed, r: Math.random() * 1.1 + 0.5 });
    }
    setup();
    window.addEventListener('resize', setup);
    window.addEventListener('mousemove', function (e) { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
    (function draw() {
      ctx.clearRect(0, 0, w, h);
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < -20) p.x = w + 20; if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20; if (p.y > h + 20) p.y = -20;
        var dx = p.x - mouse.x, dy = p.y - mouse.y, d2 = dx * dx + dy * dy;
        var glow = d2 < 26000 ? 1 - d2 / 26000 : 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r + glow * 1.4, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(26,28,25,' + (0.1 + glow * 0.35) + ')';
        ctx.fill();
      }
      requestAnimationFrame(draw);
    })();
  })();

  waitForFrames().then(function () { if (START_CHIYO_ON) setChiyo(true); else startIdle(); });
})();
</script>
</body>
</html>
"""
