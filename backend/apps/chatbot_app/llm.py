"""
LLM Service for All AI Features - FIXED VERSION
Using correct Groq API: client.chat.completions.create()
"""

import os
from typing import Dict
from groq import Groq


def get_groq_client():
    """Initialize Groq client with API key from .env"""
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found in .env file. "
            "Get one from https://console.groq.com/"
        )
    
    return Groq(api_key=api_key)


# ============================================================================
# 1. CHATBOT - Answer user questions with their health context
# ============================================================================

def generate_chatbot_answer(user_data: Dict, question: str, rag_response: Dict) -> str:
    """
    Chatbot responds to user health questions using their actual data.
    """
    
    try:
        client = get_groq_client()
        user_context = rag_response.get("user_context", "")
        
        system_prompt = """You are Menstllama, a compassionate menstrual health assistant.
Your role:
- Answer menstrual health questions with empathy and accuracy
- Use the user's personal health data to personalize responses
- Provide practical, evidence-based suggestions
- Recommend doctor visits for severe symptoms
- Be concise (2-3 paragraphs max)

Important: Do NOT diagnose. Always suggest professional help for serious symptoms."""
        
        user_message = f"""{user_context}

User Question: {question}

Please answer based on their health data above."""
        
        # CORRECT GROQ API CALL
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        return response.choices[0].message.content if response.choices else "Unable to generate response."
    
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        print(f"[LLM Chatbot] Error: {e}")
        import traceback
        traceback.print_exc()
        return "I'm having trouble connecting right now. Please try again."


# ============================================================================
# 2. MY HEALTH - Analyze questionnaire answers
# ============================================================================

def analyze_health_questionnaire(health_data: Dict, score: int, risk_level: str) -> Dict:
    """
    AI analyzes health questionnaire answers with the score.
    """
    
    try:
        client = get_groq_client()
        
        # Format the answers nicely
        answers_str = "\n".join([
            f"Q{i}: {health_data.get(f'q{i}', 'Not answered')}"
            for i in range(1, 11)
        ])
        
        system_prompt = """You are an AI health analyst for menstrual health.
Your role:
- Analyze user's health questionnaire responses
- Provide personalized insights based on their answers
- Give practical health suggestions
- Be empathetic and non-judgmental
- Recommend doctor visits if needed

Keep response to 3-4 paragraphs max."""
        
        user_message = f"""User's Health Questionnaire Responses:
{answers_str}

Health Score: {score}/110
Risk Level: {risk_level}

Please analyze their responses and provide:
1. Summary of their health status
2. Key concerns based on answers
3. Practical suggestions for improvement"""
        
        # CORRECT GROQ API CALL
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=600,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        analysis = response.choices[0].message.content if response.choices else "Unable to analyze."
        
        return {
            "analysis": analysis,
            "score": score,
            "risk_level": risk_level
        }
    
    except ValueError as e:
        return {"analysis": f"Configuration error: {str(e)}", "score": score, "risk_level": risk_level}
    except Exception as e:
        print(f"[LLM Health Analysis] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"analysis": "Unable to analyze right now. Try again later.", "score": score, "risk_level": risk_level}


# ============================================================================
# 3. DASHBOARD - Generate daily insights from user logs
# ============================================================================

def generate_dashboard_insights(user_data: Dict, recent_logs: list) -> Dict:
    """
    AI generates daily insights from user's cycle and daily logs.
    """
    
    try:
        client = get_groq_client()
        
        # Format recent logs
        logs_str = "\n".join([
            f"- {log.get('date', 'Unknown')}: Stress={log.get('stress')}, Sleep={log.get('sleep')}hrs, Pain={log.get('pain')}"
            for log in recent_logs[-7:]  # Last 7 days
        ]) if recent_logs else "No logs yet"
        
        system_prompt = """You are a health insights AI for the Syncher menstrual health app.
Your role:
- Generate daily insights from user's health logs
- Identify patterns and trends
- Provide actionable suggestions
- Be positive and supportive

Keep response to 3-4 insights max, 1-2 sentences each."""
        
        user_message = f"""User's Recent Health Logs (Last 7 days):
{logs_str}

Current Status:
- Stress: {user_data.get('stress', 'unknown')}
- Sleep: {user_data.get('sleep', 'unknown')} hours
- Cycle Pain: {user_data.get('pain', 'unknown')}
- Mood: {user_data.get('mood', 'unknown')}

Please provide:
1. 2-3 key insights about their current health
2. 2-3 actionable suggestions for today
3. When to contact a doctor (if needed)"""
        
        # CORRECT GROQ API CALL
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        insights = response.choices[0].message.content if response.choices else "Keep logging for better insights."
        
        return {
            "insights": insights,
            "status": "active",
            "last_updated": "now"
        }
    
    except ValueError as e:
        return {"insights": f"Configuration error: {str(e)}", "status": "error", "last_updated": "now"}
    except Exception as e:
        print(f"[LLM Dashboard] Error: {e}")
        import traceback
        traceback.print_exc()
        return {"insights": "Keep logging for personalized insights.", "status": "pending", "last_updated": "now"}


# ============================================================================
# 4. FOOD SUGGESTIONS - AI recommends foods based on cycle phase
# ============================================================================

def suggest_foods_for_cycle(cycle_phase: str, health_conditions: list = None) -> Dict:
    """
    AI suggests foods based on cycle phase and health conditions.
    """
    
    try:
        client = get_groq_client()
        
        conditions_str = ", ".join(health_conditions) if health_conditions else "None"
        
        system_prompt = """You are a nutrition expert for menstrual health.
Your role:
- Suggest foods based on cycle phase and conditions
- Explain why each food helps
- Keep it practical and tasty

Format as a simple list with 5-7 foods."""
        
        user_message = f"""Cycle Phase: {cycle_phase}
Health Conditions: {conditions_str}

Please suggest 5-7 foods that would be good for them during this phase.
Include a brief reason for each."""
        
        # CORRECT GROQ API CALL
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=400,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        
        suggestions = response.choices[0].message.content if response.choices else "Eat nutrient-rich whole foods."
        
        return {
            "phase": cycle_phase,
            "suggestions": suggestions
        }
    
    except ValueError as e:
        return {"phase": cycle_phase, "suggestions": f"Configuration error: {str(e)}"}
    except Exception as e:
        print(f"[LLM Food Suggestions] Error: {e}")
        return {"phase": cycle_phase, "suggestions": "Eat balanced, nutrient-rich meals during all cycle phases."}