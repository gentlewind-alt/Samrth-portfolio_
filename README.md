# Resume CMS & Static Portfolio Platform

A professional, high-performance resume parsing and management ecosystem. It integrates a local AI-assisted CMS editor with a deterministic layout engine, allowing you to parse raw resumes, make fine-grained edits, and automatically generate and publish a visually stunning, premium portfolio website.

---

## 🚀 Key Features

* **Controlled AI Parsing**: Restricts AI to semantic mapping, section classification, and normalization rather than rewriting your career achievements.
* **Pixel-Perfect Rendering**: Decouples data structure from page layout to ensure zero design or layout breakages.
* **Unified Local CMS Editor**: View original PDFs side-by-side with structured field edits inside a dark-themed Next.js workspace.
* **Static Exporter (`export.py`)**: Generates a self-contained, serverless static website (`dist/`) containing the pre-rendered HTML portfolio, background vector graphics, and your actual downloadable PDF resume.
* **Asynchronous Auto-Deploy**: Automatically updates local static files and pushes fresh builds to GitHub in the background whenever changes are saved, triggering live redeploys on hosts like Vercel.

---

## 🛠️ Architecture & Tech Stack

### Frontend (Local Client Editor)
* **Next.js & Tailwind CSS**: Minimalist, dark-themed admin dashboard and editor.
* **Iframe Sandbox**: Side-by-side original PDF preview and real-time styled portfolio preview.

### Backend (Local API Server)
* **FastAPI (Python)**: High-speed, asynchronous routing and data processing.
* **SQLite & SQLAlchemy**: Local relational database mapping resumes and structured schemas.
* **Groq SDK (`llama-3.1-8b-instant`)**: Fast schema extraction and bullet-point summarization.

---

## 📂 Repository Structure

```text
├── backend/                  # FastAPI python server, DB migrations, and schemas
├── frontend/                 # Next.js React client editor & admin dashboard
├── dist/                     # Public static export directory (HTML page, PDF, SVGs)
├── vectorizer/               # SVG background vector graphic assets
├── Samarthrawat_resume.html  # Premium design template (source of truth)
├── export.py                 # Offline static compiler script
└── README.md                 # Project documentation
```

---

## 💻 Local Setup & Execution

### 1. Backend Setup
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend/` directory with your Groq API key:
   ```ini
   GROQ_API_KEY=gsk_your_actual_groq_api_key
   ```
5. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 2. Frontend Setup
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Access the admin dashboard at `http://localhost:3000/admin`.

---

## 📦 How to Publish (Static Vercel Deployment)

To host your portfolio publicly on Vercel for free without needing a database or backend server in the cloud:

1. **Deploy to Vercel**:
   Import this GitHub repository to Vercel and configure the following overrides:
   * **Framework Preset**: `Other`
   * **Build Command**: (Override and leave blank)
   * **Output Directory**: `dist`

2. **Enable Live Auto-Publishing (Optional)**:
   Add these environment settings to your local `backend/.env` file:
   ```ini
   # Auto commit and push static files on every save
   AUTO_GIT_PUSH=true
   
   # (Optional) Trigger Vercel rebuild instantly
   VERCEL_DEPLOY_HOOK_URL=https://api.vercel.com/v1/integrations/deploy/prj_xxxx/xxxx
   ```

Now, clicking **"Save Changes"** in your local editor will automatically trigger a background commit, pushing the updated static portfolio directly to your hosted site!
