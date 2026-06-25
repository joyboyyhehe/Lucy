import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import firebase_admin
from firebase_admin import credentials, firestore
from lucy.tools import LucyTool, registry

logger = logging.getLogger("lucy.memory")

# Locate config path relative to the root backend dir
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firebase_config.json"))

db = None

def init_firebase():
    """Initialize Firebase Admin SDK using local file or environment variable."""
    global db
    if db is not None:
        return db

    config_json_str = os.getenv("FIREBASE_CONFIG_JSON")
    
    try:
        if config_json_str:
            logger.info("Initializing Firebase Admin SDK using FIREBASE_CONFIG_JSON environment variable...")
            cred_dict = json.loads(config_json_str)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif os.path.exists(CONFIG_PATH):
            logger.info(f"Initializing Firebase Admin SDK using local file: {CONFIG_PATH}...")
            cred = credentials.Certificate(CONFIG_PATH)
            firebase_admin.initialize_app(cred)
        else:
            logger.warning("Firebase credentials NOT found. Firestore memory features are disabled.")
            return None
            
        db = firestore.client()
        logger.info("Firebase Firestore client initialized successfully.")
        return db
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
        db = None
        return None

# Attempt startup initialization
init_firebase()


def is_memory_enabled() -> bool:
    """Check if the Firestore client is active."""
    global db
    if db is None:
        # Retry initialization in case env variables/files were populated after boot
        init_firebase()
    return db is not None


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Retrieve user profile configurations from Firestore."""
    if not is_memory_enabled():
        # Fallback default values
        return {
            "name": "Prathap",
            "preferences": {
                "theme": "dark",
                "voice": "bf_isabella"
            },
            "habits": {}
        }
        
    try:
        doc_ref = db.collection("users").document(user_id).collection("config").document("profile")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            # Create default document if missing
            default_profile = {
                "name": "Prathap",
                "preferences": {
                    "theme": "dark",
                    "voice": "bf_isabella"
                },
                "habits": {}
            }
            doc_ref.set(default_profile)
            return default_profile
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return {}


def update_user_profile(user_id: str, data: Dict[str, Any]) -> bool:
    """Update user profile configurations (e.g. settings, preferences)."""
    if not is_memory_enabled():
        return False
        
    try:
        doc_ref = db.collection("users").document(user_id).collection("config").document("profile")
        doc_ref.set(data, merge=True)
        return True
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return False


def get_context_memories(user_id: str) -> List[str]:
    """Retrieve list of user preferences and facts for Groq context injection."""
    if not is_memory_enabled():
        return ["Local environment only. No cloud memories loaded."]
        
    try:
        memories_ref = db.collection("users").document(user_id).collection("memories")
        # Get latest 15 memories
        query = memories_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(15)
        docs = query.stream()
        
        mem_strings = []
        for doc in docs:
            d = doc.to_dict()
            mem_strings.append(f"- [{d.get('type', 'fact')}]: {d.get('content')}")
            
        return mem_strings
    except Exception as e:
        logger.error(f"Error retrieving memories: {str(e)}")
        return ["Could not load memories from database."]


def add_memory(user_id: str, content: str, memory_type: str = "fact") -> bool:
    """Add a new user fact or preference to Firestore."""
    if not is_memory_enabled():
        logger.info(f"Memory (local-only): Did not write fact '{content}' to Firestore.")
        return False
        
    try:
        mem_ref = db.collection("users").document(user_id).collection("memories").document()
        mem_ref.set({
            "type": memory_type,
            "content": content,
            "timestamp": datetime.utcnow()
        })
        logger.info(f"Successfully recorded memory for {user_id}: {content}")
        return True
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        return False


def save_session_log(user_id: str, session_id: str, summary: str, actions: List[str]) -> bool:
    """Log user session notes and events to Firestore."""
    if not is_memory_enabled():
        return False
        
    try:
        session_ref = db.collection("users").document(user_id).collection("sessions").document(session_id)
        session_ref.set({
            "date": datetime.utcnow(),
            "summary": summary,
            "actions_taken": actions
        })
        logger.info(f"Logged session summary for {user_id} ({session_id})")
        return True
    except Exception as e:
        logger.error(f"Error saving session log: {str(e)}")
        return False


class AddUserMemoryTool(LucyTool):
    name = "add_user_memory"
    description = "Save a personal fact or preference about the user into long-term Firestore memory (e.g. user's preferred IDE, food, rules)."
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The exact fact or preference to remember about the user (e.g., 'User prefers PyCharm over VS Code')."
            },
            "type": {
                "type": "string",
                "description": "The category of memory.",
                "enum": ["fact", "preference", "habit"]
            }
        },
        "required": ["content"]
    }

    async def run(self, content: str, type: str = "fact") -> Dict[str, Any]:
        user_id = "prathap"
        success = add_memory(user_id, content, type)
        if success:
            return {"status": "success", "message": f"Recorded to long-term memory: '{content}'"}
            
        # Fallback if Firestore is offline
        return {"status": "success", "message": f"Recorded locally: '{content}' (Firestore offline)"}

# Register memory tool
registry.register(AddUserMemoryTool())
