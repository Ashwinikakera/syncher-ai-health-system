"""
RAG Service for Chatbot (Simplified)
Uses only DailyLog fields that definitely exist
"""

from typing import Dict


def get_rag_response(user_data: Dict, question: str) -> Dict:
    """
    Format user data for LLM using only DailyLog fields.
    """
    
    user_context_str = f"""
User Health Data:
- Days since expected period: {user_data.get('cycle_delay', 0)} days
- Recent stress level: {user_data.get('stress', 'unknown')}
- Recent sleep: {user_data.get('sleep', 'unknown')} hours
- Recent exercise: {user_data.get('exercise', 'unknown')} (scale 0-10)
- Recent symptoms: {user_data.get('symptoms', 'unknown')} (scale 0-10)
    """.strip()
    
    return {
        "question": question,
        "user_context": user_context_str,
    }