# AI Interview Agent — Frontend

React user interface skeleton for the AI Interview Agent.

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

- This milestone is a UI skeleton only — mock local state drives the start
  interview and submit answer transitions.
- No API calls are made yet; wiring to `POST /api/interview` happens in a
  later milestone.