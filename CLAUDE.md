# Blueprint Maker — Project Map

## What This Is
A web app that generates comprehensive business blueprint kits. Users answer a guided questionnaire (3 stages, 8 questions), the system researches their industry via LLM, then generates tailored department-level blueprints as downloadable HTML files.

## Tech Stack
- **Backend:** Python FastAPI (`server.py`) on Google Cloud Run
- **Frontend:** Vanilla JS single-page app (`static/index.html`)
- **AI:** OpenRouter API → Gemini 2.5 Pro (planning/research) + Gemini 2.5 Flash (rendering)
- **Auth:** Firebase Authentication (email/password + Google sign-in)
- **Database:** Firestore (`blueprint-maker` database)
- **Storage:** Firebase Cloud Storage for generated blueprint files
- **CI/CD:** GitHub Actions → auto-deploy to Cloud Run on push to `main`

## Folder Structure
```
blueprint_maker/
├── server.py              # FastAPI app — routes, session management, orchestration
├── config.py              # Environment config — API keys, model names, Firebase IDs
├── auth.py                # Firebase token verification
├── db.py                  # Firestore CRUD — users, blueprints, folders
├── storage.py             # Cloud Storage upload/download
├── research.py            # LLM-powered industry research (stage 1 & 2)
├── questionnaire.py       # Question definitions and stage routing
├── generator.py           # Blueprint generation — master context → department blueprints
├── renderer.py            # HTML rendering for blueprint files
├── static/
│   └── index.html         # Full frontend SPA (HTML + CSS + JS, ~2100 lines)
├── workspace/             # Layer 2 context directories (see below)
│   ├── intake/            # Questionnaire flow context
│   ├── research/          # Research phase context
│   ├── blueprint/         # Generation phase context
│   ├── templates/         # Blueprint templates
│   ├── skills/            # Layer 3 — specialized task instructions
│   └── references/        # Reference materials
├── .github/workflows/
│   └── docker.yml         # CI/CD — deploy to Cloud Run on push to main
├── Dockerfile             # Container config for Cloud Run
└── requirements.txt       # Python dependencies
```

## Architecture Rules

### Sessions
- Sessions are **in-memory** (`sessions` dict in server.py) — not persisted across server restarts
- Session TTL: 2 hours. Cleanup runs before each `/api/start`
- Session flow: `intake` → `researching` → `intake` → `compiling` → `ready` → `generating` → `generated`

### API Endpoints
| Endpoint | Purpose |
|----------|---------|
| `POST /api/start` | Create session, return first question (requires auth) |
| `POST /api/answer` | Submit answer, get next question or trigger research |
| `POST /api/generate` | Generate blueprint kit from compiled context |
| `GET /api/download/{sid}` | Download generated ZIP |
| `GET /api/preview/{sid}/{file}` | Preview single blueprint HTML |
| `POST /api/auth/sync` | Sync Firebase user to Firestore |
| `GET /api/blueprints` | List user's saved blueprints |

### Error Handling Conventions
- All frontend fetch calls must check `r.ok` before parsing JSON
- Use `fetchWithAuth()` for authenticated endpoints — handles token refresh + 401 retry
- Backend returns `detail` field in error responses
- Never swallow errors silently — at minimum log to console or show toast

### Naming Conventions
- Python files: `snake_case.py`
- Functions: `snake_case` (Python), `camelCase` (JS)
- CSS: BEM-ish with `--` for variants
- Blueprint files: `{department_name}_blueprint.html`, `glossary.html`

### Deployment
- **Project ID:** `studio-2972039985-2dbb1`
- **Region:** `us-central1`
- **Service:** `blueprint-maker`
- **Resources:** 2 vCPU, 2Gi memory, 3600s timeout
- Push to `main` triggers auto-deploy via GitHub Actions

## Project Links
- **GitHub:** https://github.com/aidgoc/blueprint-maker
- **Cloud Run:** `blueprint-maker` service in `us-central1` (project `studio-2972039985-2dbb1`)
- **Firestore DB:** `blueprint-maker` database in same project
- **Storage Bucket:** `blueprint-maker-storage-983595415114`

## Known Limitations
- Sessions are in-memory — lost on server restart or Cloud Run cold start
- Firebase tokens expire after 1 hour — frontend has `fetchWithAuth()` to handle refresh
- Research failures fall back to hardcoded default questions silently (no user notification)
- `_persist_blueprint_to_firebase()` can fail — response includes `persist_warning` flag
- `index.html` is a single ~2100-line file (HTML + CSS + JS all-in-one)

## Recent Decisions (2026-03-13)
- Anonymous access removed — all users must sign in (commit d42c6a4)
- All frontend fetch calls now use `r.ok` checks and `fetchWithAuth()` (commit 9e268df)
- Generation has 3-minute client-side timeout with retry UI
- Start/Generate buttons disable during API calls to prevent double-submit

## What NOT to Do
- Don't add npm/node tooling — frontend is intentionally vanilla JS
- Don't refactor the single-file `index.html` into components unless explicitly asked
- Don't add a database for sessions unless explicitly asked (known limitation)
- Don't commit `.env` files, Firebase credentials, or API keys
- Don't add dependencies without checking `requirements.txt` first
