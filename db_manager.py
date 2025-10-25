# db_manager.py

import random
import time
from datetime import datetime
from openai import OpenAI
import chromadb
from config import OPENAI_API_KEY  # <-- import API key from config

# ------------------- Initialize OpenAI -------------------
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# ------------------- Initialize ChromaDB -------------------
client_db = chromadb.PersistentClient(path="./chroma_data")
collection = client_db.get_or_create_collection("mock_interview_memory")


# ------------------- Audio Transcription -------------------
def transcribe_audio(audio_path: str) -> tuple[str, float]:
    """
    Convert audio to text using OpenAI Whisper API.
    Returns (text, confidence)
    """
    if not audio_path:
        return "", 0.0
    try:
        with open(audio_path, "rb") as f:
            transcript = client_ai.audio.transcriptions.create(
                model="gpt-4o-transcribe",  # recommended
                file=f
            )
        text = transcript.text.strip()
        # Simple heuristic for confidence based on length
        confidence = min(1.0, max(0.5, len(text.split()) / 25))
        return text, confidence
    except Exception as e:
        print("Transcription error:", e)
        return "", 0.0


# ------------------- Save Q&A -------------------
def save_interview_qa(
    user_id: str,
    question: str,
    answer: str,
    confidence: float,
    feedback: dict = None
):
    """
    Save a Q&A entry along with optional feedback into ChromaDB.
    feedback example:
    {
        "tone": "Positive",
        "fillers": 2,
        "confidence_score": 85,
        "clarity": 7
    }
    """
    doc_id = f"{user_id}_{int(time.time())}_{random.randint(1000, 9999)}"
    now = datetime.utcnow().isoformat()

    metadata = {
        "user_id": user_id,
        "confidence": confidence,
        "timestamp": now
    }
    if feedback:
        metadata.update(feedback)

    collection.add(
        ids=[doc_id],
        documents=[f"Q: {question}\nA: {answer}"],
        metadatas=[metadata]
    )


# ------------------- Retrieve Previous Q&A -------------------
def get_previous_qa(user_id: str, limit: int = 5) -> str:
    """
    Retrieve previous answers and feedback for a user sorted by relevance.
    Returns a formatted string for display.
    """
    results = collection.query(
        query_texts=["mock interview"],
        n_results=limit,
        where={"user_id": user_id}
    )

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return "No previous data found."

    history = []
    for doc, meta in zip(docs, metas):
        feedback_info = ", ".join(f"{k}: {v}" for k, v in meta.items() if k not in ["user_id", "timestamp"])
        history.append(
            f"{doc}\nFeedback: {feedback_info}\nTime: {meta.get('timestamp','')}\n"
        )

    return "\n\n".join(history)
