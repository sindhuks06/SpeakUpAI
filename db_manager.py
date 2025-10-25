# db_manager.py
import os
import random
from openai import OpenAI
import chromadb
from analysis_schema import AnalysisFeedback

# Initialize OpenAI
client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB
client_db = chromadb.PersistentClient(path="./chroma_data")
collection = client_db.get_or_create_collection("mock_interview_memory")

def transcribe_audio(audio_path: str) -> tuple[str, float]:
    """
    Convert audio to text using OpenAI Whisper API.
    Returns (text, confidence)
    """
    if not os.path.exists(audio_path):
        return "", 0.0
    try:
        with open(audio_path, "rb") as f:
            transcript = client_ai.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        text = transcript.text.strip()
        # Simple heuristic for confidence
        words = text.split()
        confidence = min(1.0, max(0.5, len(words)/20))
        return text, confidence
    except Exception as e:
        print("Transcription error:", e)
        return "", 0.0

def save_interview_qa(user_id: str, question: str, answer: str, confidence: float):
    """Save a Q&A entry into the database"""
    doc_id = f"{user_id}_{random.randint(1000,9999)}"
    collection.add(
        ids=[doc_id],
        documents=[f"Q: {question}\nA: {answer}\nConfidence: {confidence}"],
        metadatas=[{"user_id": user_id}]
    )

def get_previous_qa(user_id: str):
    """Retrieve previous answers for a user"""
    results = collection.query(
        query_texts=["interview history"],
        n_results=5,
        where={"user_id": user_id}
    )
    docs = results["documents"]
    if not docs or not docs[0]:
        return "No previous data found."
    return "\n\n".join(docs[0])