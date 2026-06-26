import os
import base64
import logging
from typing import Any, Dict
from PIL import ImageGrab
from groq import Groq
from lucy.tools import LucyTool, registry

logger = logging.getLogger("lucy.vision")

# Resolved temp directory path for screenshot storage
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Lucy_workspace", "temp"))

def get_groq_client() -> Groq:
    """Retrieve Groq client initialized with env API key."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured in .env file.")
    return Groq(api_key=api_key)


class TakeScreenshotTool(LucyTool):
    name = "take_screenshot"
    description = "Capture a full screenshot of the user's primary monitor and save it locally in the workspace."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def run(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(TEMP_DIR):
                os.makedirs(TEMP_DIR)

            filepath = os.path.join(TEMP_DIR, "screenshot.png")
            
            # Grab primary monitor screen using Pillow
            screenshot = ImageGrab.grab()
            screenshot.save(filepath, "PNG")
            
            logger.info(f"Screenshot successfully captured and saved to: {filepath}")
            return {
                "status": "success",
                "filepath": "temp/screenshot.png",
                "message": "Screenshot captured successfully."
            }
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to capture screenshot: {str(e)}"
            }


class VisionAnalyzeTool(LucyTool):
    name = "vision_analyze"
    description = "Send a captured screenshot or local image to the vision LLM for content extraction, error analysis, or description."
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the local image file (relative to workspace root, e.g. 'temp/screenshot.png')."
            },
            "prompt": {
                "type": "string",
                "description": "The request or query details for the image (e.g. 'What is the error on the screen?', 'Describe this image')."
            }
        },
        "required": ["image_path", "prompt"]
    }

    async def run(self, image_path: str, prompt: str) -> Dict[str, Any]:
        try:
            # Resolve path relative to workspace
            workspace_root = os.path.abspath(os.path.join(TEMP_DIR, ".."))
            abs_image_path = os.path.abspath(os.path.join(workspace_root, image_path))
            
            # Security verification
            if not abs_image_path.startswith(workspace_root):
                return {"status": "error", "message": "Access Denied: Target image lies outside the allowed workspace."}

            if not os.path.exists(abs_image_path):
                return {"status": "error", "message": f"Image file not found: {image_path}"}

            # Encode image to base64
            with open(abs_image_path, "rb") as image_file:
                base64_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Initialize Groq client
            client = get_groq_client()
            
            logger.info(f"Sending image '{image_path}' to Groq vision API with prompt: '{prompt}'")
            
            # Call Groq vision LLM model
            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1024
            )

            analysis = response.choices[0].message.content
            logger.info("Groq vision analysis completed.")
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except ValueError as ve:
            return {"status": "error", "message": str(ve)}
        except Exception as e:
            logger.error(f"Failed to perform vision analysis: {str(e)}")
            return {"status": "error", "message": f"Vision analysis failed: {str(e)}"}

# Register vision tools
registry.register(TakeScreenshotTool())
registry.register(VisionAnalyzeTool())
