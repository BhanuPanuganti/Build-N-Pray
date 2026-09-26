from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import code_routes, interview_routes, routes
from app.core.config import settings
from app.services.agent import AgentUnavailable

app = FastAPI(title="BNB AI Interview Coach", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted({settings.frontend_url.rstrip("/"), "http://localhost:3000", "http://127.0.0.1:3000"}),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(routes.router)
app.include_router(code_routes.router)
app.include_router(interview_routes.router)


@app.exception_handler(AgentUnavailable)
def agent_unavailable(_: Request, exc: AgentUnavailable):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/")
def root():
    return {"service": "BNB AI Interview Coach API", "docs": "/docs", "frontend": settings.frontend_url}
