from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="BNB AI Interview Coach", version="0.1.0")
app.include_router(router)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")
