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

### API base URL

The base URL is read from the `VITE_API_BASE_URL` environment variable. When
not set, it falls back to `http://localhost:8000` for local development.

Create a `.env` file in the `frontend/` directory to override it:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Do not commit secrets or API keys to the frontend.

## Build

```bash
cd frontend
npm install
npm run build
```

## Scripts

| Script      | Description                          |
| ----------- | ------------------------------------ |
| `npm run dev`    | Start the Vite development server |
| `npm run build`  | Build the production bundle       |
| `npm run preview`| Preview the production bundle     |

## Notes

- The frontend generates a unique `sessionId` when an interview starts and
  reuses it for every subsequent answer.
- The initial request sends the candidate payload; subsequent requests send
  only the `sessionId` and the candidate's `message`.
- The interview completes when the backend returns `done: true` with a
  `feedback` object (`summary`, `strengths`, `gaps`, `next`).