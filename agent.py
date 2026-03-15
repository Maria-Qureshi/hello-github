"""
pathfinder_core.py
------------------
Core logic for the Pathfinder career assistant.
Handles memory persistence, model initialization, and chat session management.
"""

import json
import os
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# ── Setup ──────────────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MEMORY_FILE = "memory.json"
MODEL_NAME  = "gemini-2.5-flash-lite"

SYSTEM_INSTRUCTION = """
You are Pathfinder — a sharp, strategic career architect.
Your job is to help users design deliberate career paths, identify skill gaps,
and make high-leverage decisions about their professional growth.

Rules:
- Be concise and direct. No filler.
- Ask clarifying questions before giving advice when context is missing.
- Prioritize actionable, specific recommendations over generic advice.
- When suggesting resources, prefer free/accessible ones unless asked otherwise.
- Remember and reference details the user has shared earlier in the conversation.
""".strip()


# ── Memory ─────────────────────────────────────────────────────────────────────

def load_memory() -> list[dict]:
    """Load chat history from the memory file. Returns empty list on failure."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.warning("Memory file has unexpected format — resetting.")
            return []
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load memory: %s", e)
        return []


def save_memory(history) -> bool:
    """
    Serialize and save chat history to disk.
    Skips parts that don't have a text attribute (e.g. function calls).
    Returns True on success, False on failure.
    """
    try:
        serialized = [
            {
                "role": message.role,
                "parts": [
                    part.text
                    for part in message.parts
                    if hasattr(part, "text") and part.text
                ],
            }
            for message in history
        ]
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
        return True
    except (OSError, AttributeError) as e:
        logger.error("Failed to save memory: %s", e)
        return False


def clear_memory() -> bool:
    """Delete the memory file entirely. Returns True on success."""
    try:
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)
        return True
    except OSError as e:
        logger.error("Failed to clear memory: %s", e)
        return False


# ── Model ──────────────────────────────────────────────────────────────────────

def init_model() -> Optional[genai.GenerativeModel]:
    """Configure the Gemini client and return the model. Returns None on failure."""
    genai.configure(api_key=os.getenv("API_KEY"))    
    if not os.getenv("API_KEY"):
        logger.error("API_KEY not found in environment variables.")
        return None
    try:
        return genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION,
        )
    except Exception as e:
        logger.error("Failed to initialize model: %s", e)
        return None


def start_chat_session(model: genai.GenerativeModel, history: list[dict]):
    """Start a chat session, pre-loaded with existing history."""
    return model.start_chat(history=history)


# ── Messaging ──────────────────────────────────────────────────────────────────

def send_message(chat_session, user_input: str) -> Optional[str]:
    """
    Send a user message and return the assistant's response text.
    Returns None if the request fails.
    """
    if not user_input or not user_input.strip():
        return None
    try:
        response = chat_session.send_message(user_input.strip())
        return response.text
    except Exception as e:
        logger.error("Failed to get response: %s", e)
        return None


# ── CLI entry point ────────────────────────────────────────────────────────────

def run_cli():
    """Run Pathfinder in the terminal."""
    model = init_model()
    if model is None:
        print("Error: Could not initialize model. Check your API_KEY.")
        return

    history = load_memory()
    chat    = start_chat_session(model, history)

    print("Pathfinder Online. Type 'q' to quit, 'clear' to reset memory.\n")

    try:
        while True:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "q":
                break

            if user_input.lower() == "clear":
                if clear_memory():
                    print("Memory cleared.")
                else:
                    print("Failed to clear memory.")
                continue

            reply = send_message(chat, user_input)
            if reply:
                print(f"\nPathfinder: {reply}\n")
            else:
                print("Error: No response received. Try again.\n")

    finally:
        saved = save_memory(chat.history)
        status = "Progress saved." if saved else "Warning: could not save progress."
        print(f"\n{status} Exiting...")


if __name__ == "__main__":
    run_cli()