import io
import os
import re
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

model = Model("model")


def transcribe_audio(wav_io: io.BytesIO) -> str:
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


def clean_text(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r'[_*]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()


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
        "model": "llama3-8b-8192",
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


def text_to_speech_bytes(text: str) -> io.BytesIO:
    mp3_io = io.BytesIO()
    try:
        tts = gTTS(text=text, lang="en")
        tts.write_to_fp(mp3_io)
        mp3_io.seek(0)
        return mp3_io
    except Exception as e:
        print("TTS error:", e)
        return mp3_io


@dp.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer("👋 Hello! Send me a voice message and I will reply in English.")


@dp.message(F.voice)
async def voice_handler(message: types.Message):
    voice_bytes = None
    wav_io = None
    reply_audio_io = None

    try:
        voice_file = await bot.get_file(message.voice.file_id)
        voice_bytes = io.BytesIO()
        await bot.download_file(voice_file.file_path, voice_bytes)

        voice_bytes.seek(0)
        audio = AudioSegment.from_file(voice_bytes, format="ogg")
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav", parameters=["-ar", "16000", "-ac", "1"])
        wav_io.seek(0)

        text = transcribe_audio(wav_io)
        if not text:
            await message.reply("Sorry, I couldn't understand the audio. Please speak clearly.")
            return

        await message.reply(f"📝 You said: {text}")

        ai_reply = get_ai_response(text)

        reply_audio_io = text_to_speech_bytes(ai_reply)

        await message.reply_voice(types.BufferedInputFile(reply_audio_io.read(), filename="reply.mp3"))
        await message.reply(ai_reply)

    finally:
        if voice_bytes:
            voice_bytes.close()
        if wav_io:
            wav_io.close()
        if reply_audio_io:
            reply_audio_io.close()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
