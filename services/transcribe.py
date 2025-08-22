import io
import json
import wave
from vosk import Model, KaldiRecognizer
from config import MODEL_PATH

model = Model(MODEL_PATH)

def transcribe_audio(wav_io: io.BytesIO) -> str:
    wav_io.seek(0)
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
