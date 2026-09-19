from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .db import init_db
from .agent import chat
from .config import GEMINI_API_KEY, GEMINI_MODEL

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app = FastAPI(title="Datazoic AI", version="4.2.0", description="Datazoic AI professional business assistant.")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "version": "4.2.0", "name": "Datazoic AI", "gemini_configured": bool(GEMINI_API_KEY), "gemini_model": GEMINI_MODEL}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    message = req.message.strip()
    if not message:
        return {"message": "Please enter a message.", "details": {"type": "validation_error"}}
    return chat(message, history=req.history)
