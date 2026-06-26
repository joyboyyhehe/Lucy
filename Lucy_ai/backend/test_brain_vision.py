import os
import sys
import asyncio

backend_path = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, backend_path)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, ".env"), override=True)

from lucy.brain import query_brain

async def main():
    print("--- Testing Brain ReAct Loop on Vision Prompt ---")
    user_prompt = "What is wrong on my screen?"
    print(f"User Prompt: '{user_prompt}'")
    
    # We run query_brain, which should output logs showing tool calls
    response = await query_brain(user_prompt)
    print("\n--- Final Brain Response ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
