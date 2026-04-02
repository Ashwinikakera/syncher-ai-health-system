# ml_service/test_groq_client.py

import traceback

try:
    from ml_service.chatbot.groq_client import generate_response
    print("Testing Groq client...")
    response = generate_response(
        prompt="My period is 3 days late. Should I worry?",
        system_prompt="You are a women's health assistant. Reply in 2 sentences max."
    )
    print("SUCCESS:", response)

except Exception as e:
    traceback.print_exc()