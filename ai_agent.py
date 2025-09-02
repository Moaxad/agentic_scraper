import requests
from config import GROQ_API_KEY, MODEL

def ask_ai(user_request: str):
    """Send user request to Groq (via deepseek)."""
    url = "https://api.deepseek.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a scraping task generator."},
            {"role": "user", "content": f"User wants: {user_request}. Suggest URL and fields."}
        ]
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    response = r.json()["choices"][0]["message"]["content"]
    return parse_ai_response(response)

def parse_ai_response(text: str):
    """Very simple parser. AI should return JSON."""
    import json
    try:
        return json.loads(text)
    except:
        # fallback if AI returns raw text
        return {"url": "", "fields": []}
