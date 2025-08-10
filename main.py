import re
import io
import os
import json
import requests
import asyncio
from aiogram import Bot, Dispatcher, F, types
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Load Vosk model (offline)
model = Model("model")


def transcribe_audio(wav_io: io.BytesIO):
    wav_io.seek(0)
    import wave
    wf_wave = wave.open(wav_io, "rb")
    rec = KaldiRecognizer(model, wf_wave.getframerate())
    rec.SetWords(True)
    text = ""

    while True:
        data = wf_wave.readframes(4000)
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
        "messages": [
            {
                "role": "user",
                "content": f"{prompt}\n\nPlease answer briefly in 1-2 sentences without using markdown formatting."
            }
        ],
        "temperature": 0.7
    }
    r = requests.post(url, headers=headers, json=data)
    text = r.json()["choices"][0]["message"]["content"].strip()

    # Markdown belgilarini olib tashlash
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'[*_`]', '', text)
    return text


def text_to_speech(text: str) -> io.BytesIO:
    mp3_io = io.BytesIO()
    tts = gTTS(text=text, lang="en")
    tts.write_to_fp(mp3_io)
    mp3_io.seek(0)
    return mp3_io


@dp.message(F.voice)
async def voice_handler(message: types.Message):
    voice_file = await bot.get_file(message.voice.file_id)
    voice_bytes = io.BytesIO()
    await bot.download_file(voice_file.file_path, voice_bytes)

    try:
        voice_bytes.seek(0)
        audio = AudioSegment.from_file(voice_bytes, format="ogg")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav", parameters=["-ar", "16000", "-ac", "1"])

        text = transcribe_audio(wav_io)
        await message.reply(f"📝 You say: {text}")

        ai_reply = get_ai_response(text)

        reply_audio_io = text_to_speech(ai_reply)

        await message.reply_voice(types.BufferedInputFile(reply_audio_io.read(), filename="reply.mp3"))
        await message.reply(ai_reply)

    finally:
        voice_bytes.close()
        wav_io.close()
        reply_audio_io.close()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
