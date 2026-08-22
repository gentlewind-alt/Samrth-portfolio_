# Putting this design on the live site

Two files here. Both were generated from `Portfolio v2.dc.html`.

- **`index.html`** — the whole design as one plain HTML file (no component runtime, no build step). Vanilla JS carries everything: Chiyo mode, the slap animation + synthesized slap sound, the collapsible sidebar, case-study drawers, cursor ring, particle canvas, scroll progress, IST clock, reveal-on-scroll.
- **`renderer.py`** — the same page as a `TEMPLATE` string with `%%TOKEN%%` holes, plus `render_portfolio_html(resume_data, resume_id)` with the **same signature as the current one**, so `routers.py`, the Next.js preview and `export.py` all keep working.

## Steps

**1. Replace the renderer (makes it permanent).**
Copy `renderer.py` over `backend/app/utils/renderer.py`. It fills from the same schema keys already in use: `name`, `email`, `number`, `address`, `links`, `description`, `project`, `education`, `skills`, `hobbies`, `strengths`.

Parsing rules worth knowing when editing in the CMS:

| Field | Expected shape |
| --- | --- |
| `project.body` | one project per line — `Title — description (Tech, Tech, Tech)`; the parenthesised list becomes tech tags, each line also becomes a case-study drawer |
| `skills.body` | one row per line — `Languages: Python, Java, C` |
| `education.body` | one per line — `Institution — B.Tech, IT · Bhubaneswar · CGPA 8.24 · 2026`; the year is picked up automatically, first entry gets the accent dot |
| `hobbies.body` | comma-separated; each maps to a Material icon |
| `description.body` | first line = hero + about lead, remaining lines = about paragraphs |

**2. Ship the assets.** The page loads `vectorizer/…svg` and `assets/chiyo/s-*.jpg`. Move the Chiyo frames to repo-root `assets/chiyo/`, then:

```python
# backend/app/main.py
app.mount("/vectorizer", StaticFiles(directory="vectorizer"), name="vectorizer")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
```

```js
// frontend/next.config.js — alongside the existing /vectorizer rule
{ source: '/assets/:path*', destination: 'http://127.0.0.1:8000/assets/:path*' },
```

```python
# export.py — next to the existing vectorizer copytree
chiyo_src = os.path.join("assets", "chiyo")
if os.path.exists(chiyo_src):
    shutil.copytree(chiyo_src, os.path.join(dist_dir, "assets", "chiyo"))
```

**3. Optional shortcut for a quick look.** Drop `index.html` in as `dist/index.html` (with `assets/` and `vectorizer/` beside it) to see it live immediately — but `export.py` deletes `dist/` on every run, so it only sticks once step 1 is done.

## Notes

- `renderer.py` renders the Chiyo layer, the frames and the toggle, so `frontend/components/ChiyoBackground` is redundant once this is in — the old `🐱` floating button in the previous renderer is gone.
- Case-study drawers are generated from project lines (title, description, tags). The hand-written long-form case studies in the design are not in the resume schema; if you want them, add a `case_study` field and extend `_projects_html`.
- The resume button points at `/api/resumes/{resume_id}/pdf`, which `export.py` already rewrites to the local PDF filename in static builds.
