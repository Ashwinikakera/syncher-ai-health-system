"""
ml_service/chatbot/groq_client.py
Groq API client for the RAG chatbot pipeline.
Uses model: menstllama (custom fine-tuned model for menstrual health).
This client is ONLY for the chatbot — health analysis uses health_engine.py.
"""

import logging
import os
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY, GROQ_CHATBOT_MODEL, GROQ_TEMPERATURE

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set. Chatbot cannot function.")
        _client = Groq(api_key=api_key)
    return _client


def chat_completion(
    system_prompt:   str,
    user_message:    str,
    context_chunks:  list[str],
    max_tokens:      int = 512,
) -> str:
    """
    Sends a RAG-augmented chat message to Groq menstllama.

    Parameters
    ----------
    system_prompt   : base system instruction for the model
    user_message    : the user's original question
    context_chunks  : retrieved RAG context passages (injected into user prompt)
    max_tokens      : max response tokens

    Returns
    -------
    str : model response text
    """
    # Build augmented user message with RAG context
    if context_chunks:
        context_block = "\n\n".join(
            f"[Context {i+1}]: {chunk}" for i, chunk in enumerate(context_chunks)
        )
        augmented_message = (
            f"Use the following context to answer the question.\n\n"
            f"{context_block}\n\n"
            f"Question: {user_message}"
        )
    else:
        augmented_message = user_message

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_CHATBOT_MODEL,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": augmented_message},
            ],
            max_tokens=max_tokens,
            temperature=GROQ_TEMPERATURE,
        )
        answer = response.choices[0].message.content.strip()
        logger.info("Chatbot response (%d chars) for query: '%s...'",
                    len(answer), user_message[:40])
        return answer

    except Exception as exc:
        logger.error("Groq chatbot call failed: %s", exc)
        return (
            "I'm sorry, I couldn't process your question right now. "
            "Please try again in a moment."
        )


def raw_completion(
    messages:   list[dict],
    tools:      "Optional[list[dict]]" = None,
    max_tokens: int = 512,
) -> dict:
    """
    Low-level completion call used by the LLM Agent loop in rag.py.
    Returns the raw assistant message as a dict so the agent can
    inspect tool_calls vs plain content.

    Returns:
        {
          "content":    str,
          "tool_calls": list | None,
        }
    """
    try:
        client = _get_client()
        kwargs: dict = dict(
            model       = GROQ_CHATBOT_MODEL,
            messages    = messages,
            max_tokens  = max_tokens,
            temperature = GROQ_TEMPERATURE,
        )
        if tools:
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return {
            "content":    msg.content or "",
            "tool_calls": tool_calls,
        }

    except Exception as exc:
        logger.error("raw_completion failed: %s", exc)
        return {
            "content": (
                "I'm sorry, I couldn't process your question right now. "
                "Please try again in a moment."
            ),
            "tool_calls": None,
        }


def is_available() -> bool:
    """Quick connectivity check. Returns True if Groq client initialises."""
    try:
        _get_client()
        return True
    except Exception:
        return False