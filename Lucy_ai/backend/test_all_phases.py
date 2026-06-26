import os
import sys
import asyncio
import logging

# Set up logging to avoid output flooding
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("lucy.test_all")

backend_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"), override=True)

from lucy.tools import registry
import lucy.tools_impl
import lucy.file_tools
import lucy.memory
import lucy.vision_tools
from lucy.brain import query_brain

async def run_test():
    print("====================================================")
    print("      LUCY AI - COMPREHENSIVE DIAGNOSTICS SUITE     ")
    print("====================================================\n")

    # 1. Verify Tool Registry
    print("[1/5] Checking Tool Registry...")
    expected_tools = [
        "system_info", "open_app", "browser_search",
        "file_search", "file_read", "file_write", "file_create", "file_move",
        "add_user_memory", "take_screenshot", "vision_analyze"
    ]
    registered_tools = [t.name for t in registry.get_all_tools()]
    print(f"Registered Tools ({len(registered_tools)}): {registered_tools}")
    
    missing_tools = [t for t in expected_tools if t not in registered_tools]
    if missing_tools:
        print(f"[FAIL] Missing registered tools: {missing_tools}")
        return False
    print("[OK] Tool Registry loaded successfully.\n")

    # 2. Test System Tools
    print("[2/5] Testing System Tools...")
    sys_info_res = await registry.execute("system_info", {})
    if sys_info_res.get("status") == "success":
        print(f"[OK] System Info Tool: Works (OS: {sys_info_res.get('system')}, CPU: {sys_info_res.get('cpu_percent')}%)")
    else:
        print("[FAIL] System Info Tool failed to execute.")
        return False
    print("")

    # 3. Test File Operations Sandbox
    print("[3/5] Testing Workspace File Sandbox...")
    test_file = "temp/diagnostic_test.txt"
    test_file_moved = "notes/diagnostic_test_moved.txt"
    
    # Write
    write_res = await registry.execute("file_write", {"filepath": test_file, "content": "Lucy test content", "mode": "overwrite"})
    if write_res.get("status") != "success":
        print(f"[FAIL] file_write failed: {write_res}")
        return False
    
    # Read
    read_res = await registry.execute("file_read", {"filepath": test_file})
    if read_res.get("status") != "success" or read_res.get("content") != "Lucy test content":
        print(f"[FAIL] file_read failed: {read_res}")
        return False
        
    # Search
    search_res = await registry.execute("file_search", {"pattern": "*diagnostic*"})
    if search_res.get("status") != "success" or search_res.get("count") == 0:
        print(f"[FAIL] file_search failed: {search_res}")
        return False

    # Move
    move_res = await registry.execute("file_move", {"src": test_file, "dest": test_file_moved, "action": "move"})
    if move_res.get("status") != "success":
        print(f"[FAIL] file_move failed: {move_res}")
        return False
        
    # Read Moved
    read_moved = await registry.execute("file_read", {"filepath": test_file_moved})
    if read_moved.get("status") != "success":
        print(f"[FAIL] Reading moved file failed: {read_moved}")
        return False

    # Clean Up
    workspace_root = os.path.abspath(os.path.join(backend_path, "..", "..", "Lucy_workspace"))
    abs_moved_path = os.path.join(workspace_root, test_file_moved)
    if os.path.exists(abs_moved_path):
        os.remove(abs_moved_path)
        
    print("[OK] File Sandbox operations executed successfully.\n")

    # 4. Test Memory Fallback
    print("[4/5] Testing Memory / Firestore Fallback...")
    mem_res = await registry.execute("add_user_memory", {"content": "User is validating Lucy", "type": "fact"})
    if "Recorded" in mem_res.get("message", ""):
        print(f"[OK] Memory Fallback: Works ({mem_res.get('message')})")
    else:
        print(f"[FAIL] Memory Tool returned invalid message: {mem_res}")
        return False
    print("")

    # 5. Test Vision Pipeline
    print("[5/5] Testing Vision Analysis API...")
    # Generate mock screenshot
    from PIL import Image, ImageDraw
    temp_dir = os.path.join(workspace_root, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    screenshot_path = os.path.join(temp_dir, "screenshot.png")
    
    img = Image.new("RGB", (300, 100), color=(50, 50, 60))
    d = ImageDraw.Draw(img)
    d.text((20, 40), "Lucy Phase 4 Diagnostics Passed", fill=(255, 255, 255))
    img.save(screenshot_path, "PNG")

    vision_res = await registry.execute("vision_analyze", {
        "image_path": "temp/screenshot.png",
        "prompt": "Read the text in the image exactly."
    })
    
    if vision_res.get("status") == "success":
        print("[OK] Vision Analyze Tool: Works")
        print(f"   Groq Vision Output: '{vision_res.get('analysis').strip()}'")
    else:
        print(f"[FAIL] Vision Analyze Tool: {vision_res}")
        return False
    print("")

    print("====================================================")
    print("SUCCESS: ALL TESTS PASSED SUCCESSFULLY UP TO PHASE 4!")
    print("====================================================")
    return True

if __name__ == "__main__":
    asyncio.run(run_test())
