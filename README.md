# ⚡ DevForge — Smart API Integration Tool

> Paste any API documentation URL. Get a production-ready wrapper class in seconds.

## 🎯 What it does

DevForge is an AI-powered developer tool that:
1. **Scrapes** API documentation from any URL (recursively follows relevant sub-pages)
2. **Extracts** structured API info: endpoints, auth methods, parameters — using Gemini 1.5 Pro
3. **Generates** a ready-to-use wrapper class in Python or JavaScript, tailored to your use case

## 🏗️ Architecture

```
Frontend (React + Vite)
        ↕
Backend (FastAPI)
  ├── scraper.py       — BeautifulSoup doc scraping
  ├── extractor.py     — Gemini LLM structured extraction
  └── generator.py     — Gemini LLM code generation
```

## 🚀 Setup & Usage

### Prerequisites
- Gemini API key — free at [aistudio.google.com](https://aistudio.google.com)

---

### Option A — Docker (recommended for demo/submission)

**One command to run everything:**

```bash
# First time setup
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY

# Run the app
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend API → http://localhost:8000

**Install Docker on Manjaro/Arch:**
```bash
sudo pacman -S docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER  # then logout/login
```

---

### Option B — Native (for development with hot reload)

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
uvicorn main:app --reload
```

**Frontend** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

- Frontend → http://localhost:5173
- Backend API → http://localhost:8000

## 📦 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze` | Scrape + extract API info |
| POST | `/generate` | Generate wrapper from extracted info |
| POST | `/analyze-and-generate` | Full pipeline in one call |

## 🛠️ Tech Stack

- **Backend**: FastAPI, BeautifulSoup4, Google Generative AI SDK
- **Frontend**: React 18, Vite
- **LLM**: Gemini 1.5 Pro (structured extraction + code generation)
- **Scraping**: requests + lxml + BeautifulSoup

## 💡 Solution Approach

The core insight is that API documentation, despite varying in format, always contains the same information: base URLs, endpoints, HTTP methods, parameters, and auth requirements. By combining targeted web scraping with a large-context LLM (Gemini 1.5 Pro), we can reliably extract this structure and use it to generate idiomatic, production-ready wrapper code in any language.

The tool uses a two-stage LLM pipeline:
1. **Extraction stage**: Structured JSON output from raw docs text
2. **Generation stage**: Code generation with context about the specific use case

## 📁 Project Structure

```
devforge/
├── backend/
│   ├── main.py          # FastAPI app & routes
│   ├── scraper.py       # URL scraping & cleaning
│   ├── extractor.py     # Gemini extraction
│   ├── generator.py     # Code generation
│   ├── models.py        # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── InputPanel.jsx
│           ├── StepProgress.jsx
│           ├── EndpointViewer.jsx
│           └── CodeOutput.jsx
├── colab/
│   └── devforge_demo.ipynb
└── README.md
```
