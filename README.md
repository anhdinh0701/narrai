# NarrAI MVP - AI Story Generation System

## Project Structure

```
narrai-mvp/
backend/
  agents/
    qa_refiner.py        # Agent 1: Q&A Refinement Engine
    story_generator.py   # Agent 2: Story Generation Engine
  llm/
    groq_client.py       # Groq LLM Integration
  db/
    models.py            # Database Models
  main.py                # FastAPI Server
  requirements.txt       # Python Dependencies
  .env                   # API Keys (configured)

frontend/
  index.html             # Main UI
  style.css              # Styling
  script.js              # Client Logic
```

## System Workflow

1. **User Input**: Nhap y tuong truyen ban dau
2. **Agent 1 (Q&A Refiner)**: 
   - Tao 4 cau hoi de lam ro y dinh
   - Co doc cau tra loi -> tao story brief chi tiet
3. **Agent 2 (Story Generator)**:
   - Nhan story brief tu Agent 1
   - Tao truyen chu hoan chinh
4. **Output**: Hien thi truyen va cho phep tai xuong

## Prerequisites

- Python 3.8+
- Node.js (optional, for modern http server)
- Groq API Key (already configured)

## Installation & Setup

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Backend Server

```bash
cd backend
python main.py
```

Backend will run at: http://localhost:8000

### 3. Run Frontend

In another terminal:

```bash
cd frontend

# Option A: Using Python (recommended)
python -m http.server 3000

# Option B: Using Node.js (if installed)
npx http-server -p 3000

# Option C: Open directly (without live server)
# Just open index.html in browser (may have CORS issues)
```

Frontend will run at: http://localhost:3000

## Usage

1. Open http://localhost:3000 in browser
2. Enter your story idea in Vietnamese
3. Answer 4 clarifying questions
4. Select story length (short/medium/long)
5. Wait for story generation (30-60 seconds)
6. Download or create another story

## Features

- [x] Two-Agent Architecture (Q&A + Story Generation)
- [x] Vietnamese language support
- [x] Multiple story lengths
- [x] Story export (.txt)
- [ ] Trending themes integration
- [ ] Community features
- [ ] User authentication

## Tech Stack

- **Backend**: FastAPI + Python
- **LLM**: Groq (Llama 3.1 70B)
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Database**: SQLite (local)

## API Endpoints

### POST /api/generate-questions
```json
Request:
{
  "prompt": "Your story idea here"
}

Response:
{
  "status": "success",
  "questions": ["Q1", "Q2", "Q3", "Q4"],
  "analysis": "Initial analysis"
}
```

### POST /api/refine-prompt
```json
Request:
{
  "initial_prompt": "Original idea",
  "answers": ["A1", "A2", "A3", "A4"]
}

Response:
{
  "status": "success",
  "refined_prompt": "Detailed story brief"
}
```

### POST /api/generate-story
```json
Request:
{
  "refined_prompt": "Story brief",
  "story_length": "medium"
}

Response:
{
  "status": "success",
  "story": "Full story text...",
  "word_count": 1856
}
```

### GET /api/health
Returns: {"status": "ok"}

## Troubleshooting

### CORS Error
Make sure backend is running and CORS is enabled in main.py

### API Key Error
Check .env file has valid GROQ_API_KEY

### Slow Story Generation
Story generation takes 30-60s on Llama 3.1 70B. This is normal.

### Unicode/Encoding Error
Make sure files are saved as UTF-8 encoding

## Next Steps (Phase 2)

- Add trending themes JSON
- Implement story history/database persistence
- Add user authentication
- Integrate real-time trends from social media
- Build mobile app
- Add multi-language support

## Demo Checklist

- [x] Backend API working
- [x] Frontend UI responsive
- [x] Two-Agent workflow functional
- [ ] Test with sample prompts
- [ ] Record demo video
- [ ] Prepare pitch materials

## Credits

Team: Những ngôi sao mộng mơ
School: VNU-International School
Hackathon: iStartup 2026
