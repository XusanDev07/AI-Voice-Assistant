import io
from gtts import gTTS

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
