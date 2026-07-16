# SkillProof frontend

Vue 3 + Vite implementation of the Sprint 1 repository-to-evidence journey. The application uses plain JavaScript, native `fetch`, and the Composition API. It intentionally does not calculate scores, coverage meaning, or claim eligibility in the browser; those values come from the API.

## Run locally

1. Copy `.env.example` to `.env` if the backend is not available at `http://localhost:8000`.
2. Install dependencies with `npm install`.
3. Start the frontend with `npm run dev`.

The default development proxy sends `/api/*` to the local backend. The **Complete example** and **Partial example** buttons use explicit in-browser sample data, so every result state remains inspectable before a backend is running.

## Quality checks

- `npm run lint` — lint JavaScript and Vue single-file components.
- `npm test` — run the Vitest and Vue Test Utils suite once.
- `npm run test:watch` — run tests in watch mode.
- `npm run build` — create the production bundle in `dist/`.

## API boundary

The live flow calls:

- `POST /api/v1/scans` with `{ "repository_url": "https://github.com/owner/repository" }`.
- `GET /api/v1/scans/{scan_id}` until the scan is terminal, honoring each `Retry-After` header.
- `GET /api/v1/scans/{scan_id}/evidence` and follows opaque cursors until the ledger is loaded.

Server field names stay in `snake_case`. Excerpts are inserted into a `<code>` element as text and are never interpreted as HTML.
