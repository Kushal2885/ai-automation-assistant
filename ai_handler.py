import os
from pathlib import Path
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parent
_ENV_FILE = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=True)

DEFAULT_MODEL = "gemini-3.6-flash"

SYSTEM_PROMPT = """You are an AI Automation Assistant that helps users with coding tasks and code analysis.

When a user sends a message, always respond using EXACTLY this format with these three section headers:

[EXPLANATION]
A clear, plain-English explanation of what you understood, what the code does, or how you solved the problem. Write this so a non-technical person can follow along.

[CODE]
If the task requires code (or you are analyzing/improving code), put the complete, runnable Python code here.
- Write clean, well-commented code.
- Do NOT wrap it in markdown code fences (no backticks). Just plain code.
- If no code is needed (e.g., the user asked a conceptual question), write: NO_CODE

[EXPECTED OUTPUT]
Describe what the code is expected to print or return when it runs successfully. If there is no code, write: N/A

Rules:
- Always include all three sections, even if a section contains NO_CODE or N/A.
- Never skip a section header.
- Keep explanations friendly and non-technical where possible.
- If the user provides code to analyze, explain what it does, identify any bugs, and provide a corrected version.
- Only generate Python code. If asked for another language, explain that and provide a Python equivalent.
"""


def check_api_key_configured() -> tuple[bool, str]:
    """
    Safe diagnostic: reports only whether GEMINI_API_KEY is present and
    non-placeholder. Never returns or logs the key value itself.

    Returns:
        (is_configured, status_message)
    """
    load_dotenv(dotenv_path=_ENV_FILE, override=True)
    key = os.getenv("GEMINI_API_KEY", "")
    env_exists = _ENV_FILE.exists()

    if not env_exists:
        return False, f".env file not found at: {_ENV_FILE}"
    if not key:
        return False, f".env file exists but GEMINI_API_KEY is empty or missing"
    if key == "your_gemini_api_key_here":
        return False, "GEMINI_API_KEY is still set to the placeholder value"
    return True, f"GEMINI_API_KEY is set (length={len(key)}, starts with '{key[:4]}')"


def get_ai_response(user_message: str, conversation_history: list) -> tuple[str, str]:
    """
    Send the user's message to the Gemini API and return the structured response.

    Args:
        user_message:         The raw input from the user (natural language or code).
        conversation_history: List of prior {"role": ..., "content": ...} dicts
                              from Streamlit session state.

    Returns:
        A tuple of (response_text, error_message).
        On success: (text, "")
        On failure: ("", human-readable error string)
    """
    load_dotenv(dotenv_path=_ENV_FILE, override=True)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "", (
            f"Gemini API key not found. "
            f"Create the file {_ENV_FILE} and add: GEMINI_API_KEY=your-key-here\n"
            f"Get a free key at https://aistudio.google.com/app/apikey"
        )
    if api_key == "your_gemini_api_key_here":
        return "", (
            f"GEMINI_API_KEY is still set to the placeholder value. "
            f"Open {_ENV_FILE} and replace it with your actual key."
        )

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    # Gemini SDK uses role "model" for assistant turns; Streamlit uses "assistant".
    history_contents: list[types.Content] = []
    for msg in conversation_history:
        sdk_role = "model" if msg["role"] == "assistant" else "user"
        history_contents.append(
            types.Content(
                role=sdk_role,
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )

    try:
        client = genai.Client(api_key=api_key)

        chat = client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=2048,
            ),
            history=history_contents,
        )

        response = chat.send_message(user_message)

        if not response.text or not response.text.strip():
            return "", (
                "The AI returned an empty response. "
                "This can happen due to safety filters or a transient API issue. "
                "Please rephrase your request and try again."
            )

        return response.text, ""

    except errors.APIError as e:
        code = getattr(e, "code", None)
        message = getattr(e, "message", str(e))

        if code == 400:
            return "", f"Bad request sent to Gemini API (400): {message}"
        elif code == 401 or code == 403:
            return "", (
                "Invalid or unauthorised Gemini API key (401/403). "
                "Check that GEMINI_API_KEY in your .env file is correct and active."
            )
        elif code == 429:
            return "", (
                "Gemini API rate limit reached (429). "
                "You've sent too many requests. Wait a moment and try again, "
                "or check your quota at https://aistudio.google.com"
            )
        elif code == 500 or code == 503:
            return "", (
                f"Gemini API server error ({code}). "
                "Google's servers may be temporarily unavailable. Please try again shortly."
            )
        else:
            return "", f"Gemini API error (code {code}): {message}"

    except Exception as e:
        return "", f"Unexpected error communicating with Gemini API: {str(e)}"


def parse_response(raw_response: str) -> dict:
    """
    Parse the structured AI response into its three components.

    Args:
        raw_response: The full text returned by the AI.

    Returns:
        A dict with keys: 'explanation', 'code', 'expected_output'.
        Falls back gracefully if the AI doesn't follow the format exactly.
    """
    result = {
        "explanation": "",
        "code": "",
        "expected_output": "",
    }

    sections = {
        "explanation":     "[EXPLANATION]",
        "code":            "[CODE]",
        "expected_output": "[EXPECTED OUTPUT]",
    }

    positions = {}
    for key, header in sections.items():
        idx = raw_response.find(header)
        if idx != -1:
            positions[key] = idx

    sorted_keys = sorted(positions, key=lambda k: positions[k])
    for i, key in enumerate(sorted_keys):
        start = positions[key] + len(sections[key])
        end = positions[sorted_keys[i + 1]] if i + 1 < len(sorted_keys) else len(raw_response)
        result[key] = raw_response[start:end].strip()

    if not any(result.values()):
        result["explanation"] = raw_response.strip()

    if result["code"].upper().strip() in ("NO_CODE", "NO CODE", "NONE", "N/A", ""):
        result["code"] = ""

    if result["expected_output"].upper().strip() in ("N/A", "NONE", ""):
        result["expected_output"] = ""

    return result
