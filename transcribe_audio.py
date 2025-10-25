# transcribe_audio.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def transcribe_audio(file_path: str) -> tuple[str, float]:
    """
    Converts audio to text using Whisper and returns an optional confidence score.
    Args:
        file_path (str)
    Returns:
        tuple[str, float]: transcribed text, confidence (0-1)
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.Audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        text = transcript.text.strip()
        
        # Simple confidence heuristic (placeholder)
        words = text.split()
        confidence = min(1.0, max(0.5, len(words)/20))  # ~0.5–1.0
        return text, confidence
    
    except Exception as e:
        return f"[Error: {e}]", 0.0