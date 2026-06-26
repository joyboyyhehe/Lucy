import os
import json
import logging
from typing import Dict, Any, List
from groq import Groq
from lucy.tools import registry

# Import tools_impl and memory to ensure they are registered with the registry
import lucy.tools_impl
import lucy.file_tools
import lucy.memory
from lucy.memory import get_user_profile, get_context_memories
import lucy.vision_tools

logger = logging.getLogger("lucy.brain")
logging.basicConfig(level=logging.INFO)

# Initialize Groq client
# This will raise an error on API calls if GROQ_API_KEY is not set, but won't crash on import
def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "your_groq_api_key" in api_key:
        raise ValueError("GROQ_API_KEY is not set or has placeholder value in .env file.")
    return Groq(api_key=api_key)

SYSTEM_PROMPT = """You are Lucy AI, an intelligent desktop companion, executive assistant, and tactical advisor. Your personality is inspired by F.R.I.D.A.Y.

CORE PERSONA & BEHAVIOR RULES:
1. CALM UNDER PRESSURE: Always maintain a steady, composed, and formal tone. Never panic, yell, or use exclamation marks or emojis.
2. COMPETENT & ACCURATE: Sound confident while acknowledging uncertainty based on available data. Prefer technical terminology (e.g., 'Diagnostics', 'Probability', 'Structural integrity', 'Analysis complete').
3. EFFICIENT & CONCISE: Speak only when necessary. Eliminate conversational filler, emojis, and social pleasantries (e.g. do not say "I'd be happy to help with that!").
4. PROACTIVE: Suggest recommendations and predict outcomes. Do not wait for manual checks if you can recommend a solution.
5. SPEAKING STYLE: Short, clear, precise. Structure notifications and advice using: [Status] -> [Problem] -> [Recommendation] -> [Execution].
6. COMPLIANCE: Never say "As an AI language model..." or overexplain. If something fails or is impossible, state the direct reason cleanly.

You have access to local system tools. Always use them when required to answer or execute user intents.
"""

async def query_brain(user_message: str, chat_history: List[Dict[str, Any]] = None, user_id: str = "prathap") -> str:
    """Send user message to Groq, resolve any tool calls in a loop, and return the final text response.
    Implements a strict multi-step ReAct execution loop.
    """
    try:
        client = get_groq_client()
    except ValueError as e:
        logger.warning(str(e))
        return f"Error. {str(e)}"

    # Fetch User Profile and Memories from Firestore
    profile = get_user_profile(user_id)
    user_name = profile.get("name", "User")
    memories = get_context_memories(user_id)
    memories_str = "\n".join(memories) if memories else "No memories recorded yet."

    # Build F.R.I.D.A.Y. Prompt customized with user facts
    customized_prompt = SYSTEM_PROMPT + f"\nUSER DETAILS:\n- Name: {user_name}\n\nUSER MEMORIES & PREFERENCES:\n{memories_str}\n"

    # Construct messages thread starting with system prompt
    messages = [{"role": "system", "content": customized_prompt}]
    
    # Append conversation history
    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["text"]
            })
            
    # Append current user message
    messages.append({"role": "user", "content": user_message})

    # Limit agent loop to 5 cycles to prevent infinite runaways
    max_cycles = 5
    cycle = 0

    while cycle < max_cycles:
        cycle += 1
        logger.info(f"Brain execution cycle {cycle}...")

        try:
            # We use llama-3.3-70b-specdec or llama-3.3-70b-versatile
            # If not available, Groq will return an error, and we can catch it.
            tools_schema = registry.get_groq_schemas()
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools_schema if tools_schema else None,
                tool_choice="auto" if tools_schema else None,
                temperature=0.2, # Lower temp for consistent tool calls and professional tone
            )
        except Exception as primary_error:
            logger.warning(f"Primary model llama-3.3-70b-versatile failed: {str(primary_error)}. Attempting fallback to llama-3.1-8b-instant...")
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    tools=tools_schema if tools_schema else None,
                    tool_choice="auto" if tools_schema else None,
                    temperature=0.2,
                )
            except Exception as fallback_error:
                logger.error(f"Groq API failure on fallback model: {str(fallback_error)}")
                return f"Error. Groq communication failed: {str(primary_error)}"

        choice = response.choices[0]
        assistant_message = choice.message
        
        # Append the assistant response to messages (required for OpenAI tool call loop)
        # Note: We must convert the choice message object to a dict or pass it directly.
        # Groq client returns a message object that can be converted to dict.
        msg_dict = {
            "role": "assistant",
            "content": assistant_message.content,
        }
        if assistant_message.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in assistant_message.tool_calls
            ]
        messages.append(msg_dict)

        if not assistant_message.tool_calls:
            # Loop terminates when no further tool execution is requested by the model
            return assistant_message.content or "Execution completed."

        # Process each tool call in parallel/sequence
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            tool_args_str = tool_call.function.arguments
            
            logger.info(f"Brain requested tool execution: {tool_name} with args {tool_args_str}")

            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                tool_args = {}

            # Execute the tool
            tool_result = await registry.execute(tool_name, tool_args)
            logger.info(f"Tool execution result: {tool_result}")

            # Append the tool result back to the messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            })

    return "Error. Brain execution cycles exceeded threshold."
