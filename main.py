import os
import json
import wave
import requests
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import FSInputFile
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Load Vosk model (offline)
model = Model("model")

def transcribe_audio(file_path):
    wf = wave.open(file_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    text = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text += result.get("text", "") + " "
    final_result = json.loads(rec.FinalResult())
    text += final_result.get("text", "")
    return text.strip()

def get_ai_response(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    r = requests.post(url, headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"]

def text_to_speech(text, output_file):
    tts = gTTS(text=text, lang="en")
    tts.save(output_file)

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    file = await bot.get_file(message.voice.file_id)
    file_path = file.file_path
    await bot.download_file(file_path, "voice.ogg")

    # Convert OGG to WAV
    os.system("ffmpeg -i voice.ogg -ar 16000 -ac 1 voice.wav -y")

    # Transcribe
    text = transcribe_audio("voice.wav")
    await message.reply(f"📝 Siz aytdingiz: {text}")

    # AI response
    ai_reply = get_ai_response(text)

    # Text to speech
    text_to_speech(ai_reply, "reply.mp3")

    # Send AI response
    await message.reply(ai_reply)
    await message.reply_voice(FSInputFile("reply.mp3"))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
