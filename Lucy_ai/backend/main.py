import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lucy.main")

# Import brain query and voice speak engines
from lucy.brain import query_brain
from lucy.voice import speak

app = FastAPI(title="Lucy AI Backend", version="1.0.0")

# Workspace Sandbox Setup
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Lucy_workspace"))

@app.on_event("startup")
def initialize_workspace():
    logger.info("Initializing Lucy local workspace directories...")
    folders = ["notes", "downloads", "temp", "projects"]
    for folder in folders:
        path = os.path.join(WORKSPACE_DIR, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            logger.info(f"Created workspace subdirectory: {path}")
    logger.info("Workspace initialization complete.")

# Configure CORS
# Tauri apps run on tauri.localhost or localhost:1420
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    voice_enabled: bool | None = True

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SpeakRequest(BaseModel):
    text: str
    voice: str | None = "bf_isabella"

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Lucy AI Backend",
        "firebase_project": os.getenv("FIREBASE_PROJECT_ID", "lucy-2d8bb")
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    logger.info(f"Received message: {request.message}")
    
    # Query Groq LLM brain (handles tool call loops internally)
    response_text = await query_brain(request.message)
    
    # Speak the response using Kokoro TTS in the background (non-blocking for API response)
    if request.voice_enabled:
        background_tasks.add_task(speak, response_text, "bf_isabella")
    
    return ChatResponse(
        response=response_text,
        session_id=request.session_id or "default-session"
    )

@app.post("/api/speak")
async def speak_endpoint(request: SpeakRequest, background_tasks: BackgroundTasks):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    logger.info(f"Synthesizing text: {request.text[:30]}...")
    background_tasks.add_task(speak, request.text, request.voice)
    return {"status": "processing"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
