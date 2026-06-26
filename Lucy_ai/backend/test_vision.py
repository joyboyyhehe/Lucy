import os
import sys
import asyncio
from PIL import Image, ImageDraw

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

# Load env variables from backend .env
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"), override=True)

from lucy.vision_tools import TakeScreenshotTool, VisionAnalyzeTool

async def main():
    print("--- Starting Vision Verification Test ---")
    
    # 1. Attempt screen capture
    screenshot_tool = TakeScreenshotTool()
    print("Executing TakeScreenshotTool...")
    res = await screenshot_tool.run()
    print("Screenshot Tool Response:", res)
    
    # Resolve target paths
    temp_dir = os.path.abspath(os.path.join(backend_path, "..", "..", "Lucy_workspace", "temp"))
    screenshot_path = os.path.join(temp_dir, "screenshot.png")
    
    # 2. Fallback to mock image if screenshot failed (common in headless/sandboxed agent environments)
    if res.get("status") != "success":
        print("\n[WARNING] Screen capture failed. This is expected in headless/sandboxed terminal environments.")
        print("Generating a mock screenshot to verify the Vision API pipeline...")
        
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        # Create a mock image with PIL
        img = Image.new("RGB", (800, 600), color=(30, 30, 40))
        d = ImageDraw.Draw(img)
        # Draw some mock window UI elements
        d.rectangle([(50, 50), (750, 550)], fill=(45, 45, 55), outline=(100, 100, 100), width=2)
        d.text((100, 100), "Lucy AI Companion - Diagnostics Window", fill=(255, 255, 255))
        d.text((100, 150), "Status: Online", fill=(100, 255, 100))
        d.text((100, 200), "Error: None", fill=(255, 255, 255))
        d.text((100, 250), "Testing Groq Vision LLM Llama-4-Scout Integration", fill=(200, 200, 200))
        
        img.save(screenshot_path, "PNG")
        print(f"Mock screenshot saved successfully at: {screenshot_path}")
        image_relative_path = "temp/screenshot.png"
    else:
        print(f"Real screenshot captured successfully at: {screenshot_path}")
        image_relative_path = res["filepath"]
        
    # Verify image exists and has content
    if not os.path.exists(screenshot_path) or os.path.getsize(screenshot_path) == 0:
        print("ERROR: Image file is missing or empty.")
        sys.exit(1)
        
    print(f"Image verification passed. Size: {os.path.getsize(screenshot_path)} bytes.")
    
    # 3. Call VisionAnalyzeTool to test Groq Vision integration
    print("\nExecuting VisionAnalyzeTool...")
    vision_tool = VisionAnalyzeTool()
    
    prompt_query = "Read the text on the screen and describe the status of the window."
    analysis_res = await vision_tool.run(
        image_path=image_relative_path,
        prompt=prompt_query
    )
    
    print("\nVision Analyze Tool Response:")
    print(analysis_res)
    
    if analysis_res.get("status") == "success":
        print("\n[SUCCESS] Vision API pipeline verified successfully!")
        print("Analysis Content:\n", analysis_res["analysis"])
        sys.exit(0)
    else:
        print("\n[FAILED] Vision API analysis failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
