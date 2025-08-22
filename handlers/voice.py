from aiogram import Router, types, F
from bot_init import bot
from services.transcribe import transcribe_audio
from services.ai_client import get_ai_response
from services.tts import text_to_speech_bytes
from pydub import AudioSegment
import io

router = Router()

@router.message(F.voice)   # ✅ F.voice ishlatiladi
async def voice_handler(message: types.Message):
    voice_bytes = io.BytesIO()
    wav_io = io.BytesIO()
    reply_audio_io = None

    try:
        voice_file = await bot.get_file(message.voice.file_id)
        await bot.download_file(voice_file.file_path, voice_bytes)

        voice_bytes.seek(0)
        audio = AudioSegment.from_file(voice_bytes, format="ogg")
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
        voice_bytes.close()
        wav_io.close()
        if reply_audio_io:
            reply_audio_io.close()
