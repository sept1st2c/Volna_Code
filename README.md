# Volna

Voice AI DSA tutor. Explain the problem back, defend your approach out loud, get gated hints, write real code, and have it graded by real sandboxed execution instead of an LLM's opinion.

See `PLAN.md` for the full architecture and design rationale.

## Prerequisites

- Python 3.11+ and a venv at `server/.venv` with `server/requirements.txt` installed
- Node.js and `web/node_modules` installed (`npm install` in `web/`)
- Docker Desktop running, for the self-hosted Piston sandbox
- A `.env` file at the repo root with `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` (see `.env.example`)

## Running everything for a live voice session

Four things need to be running at once, each in its own terminal.

**1. Piston (sandboxed code execution).** Only needs to be started once; it keeps running across sessions.

```
docker run -d --name piston_api --privileged -p 2000:2000 ^
  -v "C:\Users\3shub\Documents\Volna-Code\.piston-data\packages:/piston/packages" ^
  --tmpfs /piston/jobs:exec ^
  -e PISTON_OUTPUT_MAX_SIZE=131072 -e PISTON_MAX_FILE_SIZE=10000000 ^
  ghcr.io/engineer-man/piston
```

If it's already running, skip this. Check with `docker ps --filter name=piston_api`.

**2. FastAPI backend** (problem listing, LiveKit token minting):

```
cd server
.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

**3. LiveKit voice agent worker** (the actual tutoring brain + voice loop). Must be launched as a module, not as a script, or sibling package imports break:

```
cd server
.venv\Scripts\python.exe -m agent.worker dev
```

Wait for a `registered worker` log line before connecting from the frontend.

**4. Frontend:**

```
cd web
npm run dev
```

Then open `http://localhost:3000/tutor/two-sum` (or any other problem slug from `http://localhost:3000/problems`), click **Connect voice**, allow microphone access, and wait for the "tutor agent present" indicator before speaking.

## Known rough edges

- The room name the frontend requests must exactly match a real problem slug (e.g. `two-sum`) -- this is how the worker figures out which problem to tutor.
- A full microphone-in/speaker-out round trip has not yet been verified by anyone other than a live human tester -- if something sounds wrong, check the worker terminal's logs first.
