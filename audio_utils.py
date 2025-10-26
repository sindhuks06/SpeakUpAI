from openai import OpenAI
from config import OPENAI_API_KEY

client_ai = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio_whisper(audio_path: str) -> str:
    with open(audio_path, "rb") as f:
        transcription = client_ai.audio.transcriptions.create(
            file=f,
            model="whisper-1"
        )
    return transcription.text
