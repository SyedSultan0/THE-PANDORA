# THE-PANDORA

AI Interview Agent — a conversational technical interview application powered
by the Gemini API.

## Backend setup

```bash
pip install -r requirements.txt
```

Create a local `.env` file (never commit it) with your Gemini API key:

```bash
GEMINI_API_KEY=your-key-here
```

Optional model override:

```bash
GEMINI_MODEL=gemini-2.0-flash
```

The `.env` file is loaded automatically by `app/main.py` (via python-dotenv)
and is excluded from Git via `.gitignore`.

## Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs
- Interview endpoint: `POST /api/interview`

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` and `/health` to `http://localhost:8000` (see
`frontend/vite.config.js`).

## Tests

```bash
python -m pytest tests/ -v