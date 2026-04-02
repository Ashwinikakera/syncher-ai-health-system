# ml_service/chatbot/groq_client.py
# Day 7 — Task 2: Optimized Groq client (replaces original)

from groq import Groq
from ml_service.config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def check_groq_running() -> bool:
    """Verify Groq API key is valid and reachable."""
    try:
        client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False


def list_available_models() -> list:
    """Return current model in use."""
    return [GROQ_MODEL]


def generate_response(
    prompt: str,
    system_prompt: str = None,
    mode: str = "chat",          # "chat" | "nlp"
) -> str:
    """
    Optimized Groq call.

    Changes from original:
    - mode="chat"  → more tokens (250), lower temp (0.5) for consistent health answers
    - mode="nlp"   → fewer tokens (120), temp=0.0 for strict JSON extraction
    - Added stop sequences to prevent Groq from rambling past the answer
    - Added basic response quality check — retries once if response is too short
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    # Per-mode settings
    if mode == "nlp":
        max_tokens  = 120
        temperature = 0.0       # deterministic for JSON extraction
        top_p       = 1.0
        stop        = None
    else:
        max_tokens  = 250       # was 150 — gives room for complete answers
        temperature = 0.5       # was 0.7 — less random = more reliable health info
        top_p       = 0.9
        stop        = ["User:", "Human:"]   # prevent role-play bleed

    def _call() -> str:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
        )
        return response.choices[0].message.content.strip()

    try:
        result = _call()

        # Quality check for chat mode — retry once if suspiciously short
        if mode == "chat" and len(result.split()) < 8:
            result = _call()

        return result

    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}")