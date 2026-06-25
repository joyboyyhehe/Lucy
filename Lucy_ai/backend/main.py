import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Lucy AI Backend", version="1.0.0")

# CORS middleware configuration
# Tauri app in dev mode typically runs on localhost (e.g. http://localhost:1420 or http://tauri.localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev setup; lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "Lucy AI Backend",
        "firebase_project": os.getenv("FIREBASE_PROJECT_ID", "lucy-2d8bb")
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Simple echo/skeleton response for Phase 0
    # In Phase 1, we will integrate Groq LLM tool-calling here
    user_msg = request.message
    bot_reply = f"Hello! I received your message: '{user_msg}'. My Groq brain is warming up!"
    
    return ChatResponse(
        response=bot_reply,
        session_id=request.session_id or "default-session"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
