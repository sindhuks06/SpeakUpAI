import openai
from config import OPENAI_API_KEY, WHISPER_MODEL, GPT_MODEL
from typing import List, Dict

openai.api_key = OPENAI_API_KEY

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.
    Returns the transcript as string.
    """
    with open(audio_file_path, "rb") as f:
        transcription = openai.audio.transcriptions.create(
            file=f,
            model=WHISPER_MODEL
        )
    return transcription.get('text', '')

def ask_gpt(question: str, conversation: List[Dict[str, str]] = []) -> str:
    """
    Ask GPT model a question, optionally including previous conversation.
    Returns GPT response as string.
    """
    messages: List[Dict[str, str]] = [{"role": "system", "content": "You are a helpful AI interviewer."}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": question})

    response = openai.chat.completions.create(
        model=GPT_MODEL,
        messages=messages
    )

    # Safely get content
    choices = getattr(response, "choices", [])
    if choices and len(choices) > 0:
        msg = getattr(choices[0], "message", {})
        content = msg.get("content") if isinstance(msg, dict) else ""
        return content or ""
    return ""
