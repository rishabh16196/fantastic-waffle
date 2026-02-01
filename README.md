# Leveling Guide Example Generator

Transform generic career leveling guides into specific, actionable examples using AI.

## The Problem

Managers struggle to explain career progression to their direct reports. Leveling guides exist, but their definitions are too generic. Employees ask: *"What specifically do I need to do to get promoted?"*

## The Solution

Upload your company's leveling guide, and this tool generates 3 specific examples for each cell, showing employees exactly what great performance looks like at each level.

## Features

- **File Upload**: Support for PDF, CSV, and text files
- **AI-Powered Parsing**: Automatically extracts the structure from your leveling guide
- **Contextual Examples**: Uses your company website for relevant examples
- **Persistent Storage**: All results stored for future email generation features

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite + TypeScript
- **AI**: OpenAI GPT-4o

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your OpenAI key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
echo "FRONTEND_URL=http://localhost:5173" >> .env

# Run the server
uvicorn main:app --reload
```

**Required Environment Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `FRONTEND_URL`: URL of frontend for CORS (default: http://localhost:5173)
- `DATABASE_URL`: SQLite or Postgres URL (default: sqlite:///./leveling_guide.db)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 to use the app.

**For production**, set `VITE_API_URL` to your backend URL before building:
```bash
VITE_API_URL=https://your-backend.onrender.com/api npm run build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Upload a leveling guide and start processing |
| GET | `/api/sessions/{id}` | Get session with all generated examples |
| GET | `/api/sessions/{id}/status` | Check processing status |
| GET | `/api/sessions` | List all sessions |

## Data Model

```
Session (one per upload)
├── Levels (rows: L1, L2, L3...)
├── Competencies (columns: Technical, Leadership...)
└── Cells (intersection of level × competency)
    └── Examples (3 AI-generated examples per cell)
```

### Design Decisions

1. **Normalized SQL Schema**: Enables future queries by level ("show all L4 expectations") or competency ("show leadership progression across levels") for email generation.

2. **Background Processing**: File parsing and example generation happen asynchronously to avoid request timeouts.

3. **Original Content Storage**: We store the raw uploaded content for debugging and potential reprocessing.

## Future Improvements

With more time, I would:

1. **Streaming Results**: Show examples as they're generated instead of waiting for all
2. **Email Integration**: Generate and send formatted emails with results
3. **Export Options**: PDF/Notion/Google Sheets export
4. **User Accounts**: Save and manage multiple leveling guides
5. **Caching**: Cache company context from website scraping

## License

MIT
