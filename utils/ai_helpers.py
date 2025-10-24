import openai
from config import OPENAI_API_KEY, WHISPER_MODEL, GPT_MODEL

openai.api_key = OPENAI_API_KEY

def transcribe_audio(audio_file_path):
    with open(audio_file_path, "rb") as f:
        transcription = openai.audio.transcriptions.create(
            file=f,
            model=WHISPER_MODEL
        )
    return transcription['text']

def ask_gpt(question, conversation=[]):
    messages = [{"role": "system", "content": "You are a helpful AI interviewer."}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": question})

    response = openai.chat.completions.create(
        model=GPT_MODEL,
        messages=messages
    )
    return response.choices[0].message.content
