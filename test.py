import requests

API_KEY = "key"
URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_groq(question: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 200
    }

    response = requests.post(URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        return f"Xatolik: {response.status_code} - {response.text}"


if __name__ == "__main__":
    while True:
        user_input = input("Savolingizni yozing (chiqish uchun 'exit'): ")
        if user_input.lower() == "exit":
            break
        answer = ask_groq(user_input)
        print("AI javobi:", answer)
