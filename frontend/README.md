# AI Interview Agent — Frontend

React user interface for the AI Interview Agent, connected to the FastAPI
backend.

## Stack

- React 18
- Vite 5

## Development

```bash
cd frontend
npm install
npm run dev
```

The development server runs at http://localhost:5173.

## Backend API

The frontend talks to the FastAPI backend at `POST /api/interview` and
`GET /health`.

### Local development (CORS-safe)

During development, Vite proxies `/api` and `/health` to the FastAPI backend
at `http://localhost:8000` (see `vite.config.js`). This lets the frontend and
backend run on different origins without needing CORS configuration on the
backend.

Start the backend first:

```bash
cd THE-PANDORA
uvicorn app.main:app --reload --port 8000
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173.

### API base URL override

For a different backend origin (e.g. a deployed environment), set the
`VITE_API_BASE_URL` environment variable. When unset, the frontend uses
same-origin (relying on the Vite dev proxy in development).

Create a `.env` file in the `frontend/` directory:

```bash
VITE_API_BASE_URL=https://your-backend.example.com
```

Do not commit secrets or API keys to the frontend.

## Build

```bash
cd frontend
npm install
npm run build
```

The production bundle is output to `frontend/dist/`.

## Scripts

| Script      | Description                          |
| ----------- | ------------------------------------ |
| `npm run dev`    | Start the Vite development server |
| `npm run build`  | Build the production bundle       |
| `npm run preview`| Preview the production bundle     |

## Notes

- The frontend loads the REAL supplied candidate profiles from
  `src/data/candidates.json` (a copy of the organizer's `data/candidates.json`).
  The start screen presents a candidate selector — the frontend never invents
  candidate fields or profiles.
- The initial request sends the selected REAL candidate object (`member` +
  `missions` + `signals`); subsequent requests send only the `sessionId` and
  the candidate's `message`.
- The backend is the source of truth for questions, follow-ups, evaluation,
  difficulty, interview state, and completion.
- The interview completes when the backend returns `done: true` with a
  `feedback` object (`summary`, `strengths`, `gaps`, `next`).
- The Gemini API key belongs ONLY to the backend (`GEMINI_API_KEY` in the
  backend environment). No API key is ever placed in the frontend.
