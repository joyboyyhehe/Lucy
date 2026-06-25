import os
import urllib.request
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple

logger = logging.getLogger("lucy.voice")

# Folder to store local voice model weights
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Lucy_workspace", "voice_models"))
MODEL_PATH = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODEL_DIR, "voices-v1.0.bin")

# Release files from kokoro-onnx author
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

# Thread pool executor for blocking audio/synthesis tasks
executor = ThreadPoolExecutor(max_workers=2)

# Global Kokoro instance
_kokoro_instance = None

def ensure_model_files():
    """Ensure that the required ONNX model and voices weight files are present.
    Downloads them automatically if missing.
    """
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    # Download model if missing
    if not os.path.exists(MODEL_PATH):
        logger.info(f"Model file missing. Downloading from {MODEL_URL}...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
            logger.info("Successfully downloaded Kokoro ONNX model.")
        except Exception as e:
            logger.error(f"Failed to download model: {str(e)}")
            raise

    # Download voices if missing
    if not os.path.exists(VOICES_PATH):
        logger.info(f"Voices file missing. Downloading from {VOICES_URL}...")
        try:
            urllib.request.urlretrieve(VOICES_URL, VOICES_PATH)
            logger.info("Successfully downloaded Kokoro voices bin file.")
        except Exception as e:
            logger.error(f"Failed to download voices: {str(e)}")
            raise


def get_kokoro():
    """Lazy initialize and return the Kokoro instance."""
    global _kokoro_instance
    if _kokoro_instance is not None:
        return _kokoro_instance

    # Import inside function to prevent crash if kokoro-onnx is not installed yet
    from kokoro_onnx import Kokoro
    
    ensure_model_files()
    
    logger.info("Initializing Kokoro ONNX engine...")
    _kokoro_instance = Kokoro(MODEL_PATH, VOICES_PATH)
    logger.info("Kokoro ONNX engine initialized.")
    return _kokoro_instance


def _synthesize_and_play_sync(text: str, voice_name: str):
    """Synchronous worker that synthesizes and plays audio."""
    try:
        import sounddevice as sd
        
        kokoro = get_kokoro()
        
        logger.info(f"Synthesizing speech for voice '{voice_name}': '{text[:30]}...'")
        samples, sample_rate = kokoro.create(text, voice=voice_name, speed=1.0)
        
        logger.info("Playing synthesized audio stream.")
        sd.play(samples, sample_rate)
        sd.wait() # Block until playback finishes
        logger.info("Audio playback complete.")
        return True
    except Exception as e:
        logger.error(f"Error in TTS execution: {str(e)}")
        return False


async def speak(text: str, voice_name: str = "bf_isabella") -> bool:
    """Asynchronously synthesize text and play it locally on the system speakers."""
    loop = asyncio.get_running_loop()
    # Run the blocking synthesis and playback inside the thread pool executor
    success = await loop.run_in_executor(executor, _synthesize_and_play_sync, text, voice_name)
    return success
