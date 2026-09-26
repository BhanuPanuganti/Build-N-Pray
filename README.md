# BNB - AI Interview Coach

FastAPI prototype for a spoken AI interview, DSA typing round, and privacy-aware proctoring observations.

## Start locally

```powershell
uv sync
uv run main.py
```

Open `http://127.0.0.1:8000`. The app begins in demo mode and needs no API key. In `.env`, set `DEMO_MODE=false`, set `HUGGINGFACE_API_KEY`, and choose `HF_CHAT_MODEL` to activate Hugging Face via LangChain.

The browser can request camera/microphone access and observe focus/full-screen changes; it cannot block another tab or window. Observations are never proof of cheating or an automatic hiring decision.
