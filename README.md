# BNB Interview Coach

A practice interview for technical roles. A candidate rehearses a timed coding round and a spoken conversation written from a job description and a résumé. An interviewer can publish that job once, share a link, and read a scoreboard of who attempted it.

Scores, written feedback, and camera observations are a practice record. They are there so the candidate and the interviewer can see what happened.

## Features

### Accounts

- Candidates sign up by default and keep sessions under their email.
- Interviewers publish jobs. Creating an interviewer account requires `ADMIN_ACCESS_CODE`.
- Sign-in is a bearer token. The browser stores the account in `localStorage`.

### Solo rehearsal

From `/setup`, a candidate pastes or uploads a résumé (PDF, DOCX, or TXT), adds a job description, and chooses the rounds. The agent reads that profile and runs the interview. Coding problems in this mode come from the practice bank.

### Interviewer links

An interviewer posts a role, a job description, and the criteria they care about. The agent prepares the interview once:

- A coding problem written for that job, with a statement, starter code, and tests. Expected outputs come from running a reference solution locally. The reference is not stored. Hidden tests stay on the server.
- Spoken rounds that use the same job, then the student's own résumé once they join.

The interviewer gets one link (`/i/<token>`). A student must sign in, then starts. After attempts, the scoreboard lists name, email, status, per-round scores, the overall score, and a link to the written report.

### Coding round

- Monaco editor with question on the left and the editor on the right. Thirteen languages, with light and dark themes matched to the app.
- Visible samples can be run freely. Submit runs the hidden tests and finishes the round.
- Starter code parses stdin so the candidate works on the solution.
- Drafts persist per problem and language. The timer lives on the server, so a refresh does not reset it. When time runs out, the current code is submitted.
- Correctness comes from executing the code (Judge0 by default). The agent writes the complexity and quality notes. If the agent is unavailable at submit time, the tests still count and the complexity note is labelled as an estimate.

### Spoken rounds

Project and fundamentals are a conversation, not a fixed question list. The interviewer plans topics from the job and the résumé, follows up, probes claims, and moves on when an answer is enough. One question at a time. Scores stay off the screen until the report.

Each skill discussed gets a rating and the evidence behind it. A round score is the average of those ratings. The overall score averages the rounds that were completed.

### Voice

Questions are read aloud with Cartesia, and the text stays on screen. The candidate can speak an answer; the transcript stays editable, and that written text is what gets scored. Typing works when the microphone is off. If Cartesia is unavailable, the browser voice asks the question. The coding round is not read aloud.

### Monitoring

The session can use the camera and microphone and can record leaving the tab, leaving full screen, a missing face, more than one person, lighting, a phone, and eyes held off the screen. A glance at the keyboard waits before it counts. Mouth movement is kept for review and does not add a warning. One continuous condition is one warning. Five warnings lock the practice round. The report lists what was observed.

### Report

The report speaks to the candidate as "you": round scores, skill ratings, what worked, what to improve, the coding review, and the monitoring log. It lives outside the session layout so opening it does not start the camera.

## Stack

- API: FastAPI, Python 3.13, LangGraph
- App: Next.js 16, React, Tailwind CSS 4, Monaco
- Agent: Hugging Face by default (`Qwen/Qwen2.5-72B-Instruct`), with Gemini and Groq as fallbacks
- Code: Judge0 Community Edition, or a local runner for offline development
- Data: MongoDB, with an in-memory store when `MONGODB_URI` is empty
- Voice: Cartesia

## Run locally

From `Build-N-Pray/`:

```powershell
uv sync
copy .env.example .env
uv run main.py
```

From `Build-N-Pray/frontend/`, in a second terminal:

```powershell
npm install
npm run dev
```

Open `http://localhost:3000`. The API listens on `http://127.0.0.1:8000`. The Next.js app proxies `/api` to it, so the browser talks only to port 3000.

Set `HUGGINGFACE_API_KEY` before starting an interview. There is no demo mode. If the agent is down, the app says so.

Publishing an interviewer link calls the agent twice (a brief, then the coding problem) and can take a minute or two. The dev proxy waits up to three minutes for that request.

Check the live agent, voice, and code runner with:

```powershell
.\.venv\Scripts\python.exe scripts\check_live_services.py
```

## Configuration

Copy `.env.example` to `.env`. Leave a value empty to skip that service.

| Variable | Purpose |
| --- | --- |
| `HUGGINGFACE_API_KEY` | Required for the interview agent |
| `HF_CHAT_MODEL` | Chat model. Default `Qwen/Qwen2.5-72B-Instruct` |
| `AGENT_PROVIDERS` | Provider order. Default `huggingface,gemini,groq` |
| `GEMINI_API_KEY`, `GROQ_API_KEY` | Optional fallbacks |
| `MONGODB_URI` | Atlas or local Mongo. Empty uses in-memory storage |
| `MONGODB_DATABASE` | Default `bnb_interview` |
| `CARTESIA_API_KEY` | Spoken questions and speech-to-text |
| `CODE_RUNNER` | `judge0` (default) or `local` |
| `JUDGE0_URL` | Default `https://ce.judge0.com` (no key) |
| `JUDGE0_API_KEY` | RapidAPI key or self-hosted auth token |
| `ADMIN_ACCESS_CODE` | Required to create an interviewer account |
| `FRONTEND_URL` | Default `http://localhost:3000` |

If the API is not on port 8000, set `API_URL` in `frontend/.env.local`. Spoken answers also need `NEXT_PUBLIC_API_URL` pointed at the same API host. See `frontend/.env.example`.

## App

| Route | What it is |
| --- | --- |
| `/` | Home |
| `/sign-in` | Sign in or create an account |
| `/setup` | Solo interview setup |
| `/session/[id]` | Interview map. `?section=project` or `?section=fundamentals` opens the conversation |
| `/session/[id]/dsa` | Timed coding round |
| `/report/[id]` | Written report |
| `/admin`, `/admin/new` | Interviewer list and new job |
| `/admin/interviews/[id]` | Scoreboard and the public coding problem |
| `/i/[token]` | Shared interview link |

## Tests

```powershell
uv run --with pytest pytest
```

Interview tests use a scripted agent and an in-memory database, so they do not call Hugging Face or write to MongoDB.

## Documentation

Longer notes live in `documentations and learnings/` (agent, interviewer links, conversational rounds, code execution, frontend, Cartesia) and `documentations/` (MongoDB, proctoring, Cartesia credentials). Product intent is in `Product Philosophy.md`.
