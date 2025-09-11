import requests
from config import GROQ_API_KEY
from services.clean_text import clean_text

def get_ai_response(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    sys_msg = (
        "You are a helpful assistant. Answer briefly in 1-2 sentences. "
        "Do NOT use markdown formatting."
    )

    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": prompt}
    ]

    data = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        payload = r.json()
        text = payload["choices"][0]["message"]["content"]
        return clean_text(text)
    except Exception as e:
        print("AI request error:", e)
        return "Sorry, I couldn't process your request at the moment."
