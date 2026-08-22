# Portfolio Backend (v2)

A complete backend-driven portfolio system. The backend generates and serves your portfolio HTML directly, eliminating the need for a separate frontend.

## Features

- **Backend-Driven Portfolio**: Serve portfolio as HTML from FastAPI
- **PDF Resume Upload**: Upload and parse PDF resumes
- **Auto-Parsing**: Extract resume data using rule-based parsing
- **Live Updates**: Update portfolio by editing resume content
- **Admin API**: REST API for resume management
- **Chiyo Interactive**: Built-in interactive background toggle

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Database models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # DB configuration
│   ├── utils/
│   │   ├── extraction.py       # PDF text extraction
│   │   └── renderer.py         # HTML portfolio renderer
│   └── routers/
│       ├── portfolio.py        # Portfolio serving routes
│       └── admin.py            # Admin API routes
├── uploads/                    # Uploaded PDF resumes
├── requirements.txt            # Python dependencies
└── portfolio.db               # SQLite database
```

## Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Run the server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Portfolio
- `GET /` - Main portfolio page (HTML)
- `GET /resume/{id}` - Specific resume portfolio

### Admin API
- `GET /api/resumes` - List all resumes
- `GET /api/resumes/{id}` - Get resume details
- `POST /api/resumes` - Upload and parse resume PDF
- `PUT /api/resumes/{id}` - Update resume content
- `DELETE /api/resumes/{id}` - Delete resume
- `GET /api/resumes/{id}/pdf` - Download resume PDF
- `GET /api/slaps` - Get Chiyo slap count
- `POST /api/slaps` - Increment slap count

## How It Works

1. **Upload Resume**: POST a PDF to `/api/resumes`
2. **Auto-Parse**: Backend extracts text and parses into sections
3. **Store Data**: Resume data saved to SQLite database
4. **Generate Portfolio**: Backend renders HTML portfolio from stored data
5. **Serve Portfolio**: `GET /` returns the portfolio HTML

## Configuration

Create a `.env` file:
```env
DATABASE_URL=sqlite:///./portfolio.db
API_HOST=0.0.0.0
API_PORT=8000
GROQ_API_KEY=your_key_here  # Optional for enhanced parsing
```

## Database Schema

### Resumes Table
- `id` - Resume ID
- `filename` - Original PDF filename
- `filepath` - Path to uploaded PDF
- `content_json` - Parsed resume data (JSON)
- `created_at` - Upload timestamp
- `updated_at` - Last modified timestamp

### SlapCount Table
- `id` - Record ID
- `count` - Total Chiyo slaps
- `updated_at` - Last update

## Performance

- **Portfolio Load**: < 100ms (pre-rendered HTML)
- **Upload Time**: 1-3 seconds (PDF parsing)
- **Database Size**: < 1MB for 100 resumes

## Development

To add custom rendering:
1. Edit `app/utils/renderer.py`
2. Modify the `render_portfolio_html()` function
3. Restart server to see changes

All portfolio HTML is generated on-demand from stored resume data.
