# memory.py  ← NEW FILE
# Stores conversation history per session.
# Keeps last N messages so Gemini has context for follow-up questions.

MAX_HISTORY = 10  # keep last 5 exchanges (user + assistant = 2 each)

# In-memory store: { session_id: [ {role, content}, ... ] }
_sessions = {}


def get_history(session_id: str) -> list:
    """Returns chat history for a session."""
    return _sessions.get(session_id, [])


def add_message(session_id: str, role: str, content: str):
    """Appends a message to the session history. Trims to MAX_HISTORY."""
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "content": content})
    # Keep only the last MAX_HISTORY messages
    if len(_sessions[session_id]) > MAX_HISTORY:
        _sessions[session_id] = _sessions[session_id][-MAX_HISTORY:]


def clear_history(session_id: str):
    """Clears history for a session."""
    if session_id in _sessions:
        del _sessions[session_id]


def format_history_for_prompt(session_id: str) -> str:
    """Formats history as a readable string to inject into prompts."""
    history = get_history(session_id)
    if not history:
        return ""
    lines = []
    for msg in history:
        prefix = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {msg['content']}")
    return "\n".join(lines)