# db_manager.py

import os
import random
import time
from datetime import datetime
from openai import OpenAI
import chromadb

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
                model="gpt-4o-transcribe",  # faster and better
                file=f
            )
        text = transcript.text.strip()
        confidence = min(1.0, max(0.5, len(text.split()) / 25))
        return text, confidence
    except Exception as e:
        print("Transcription error:", e)
        return "", 0.0


def save_interview_qa(
    user_id: str,
    question: str,
    answer: str,
    confidence: float,
    feedback: dict = None
):
    """
    Save a Q&A entry along with feedback into ChromaDB.
    Feedback example:
    {
        "tone": "Positive",
        "fillers": 2,
        "confidence_score": 8,
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


def get_previous_qa(user_id: str, limit: int = 5):
    """
    Retrieve previous answers and feedback for a user sorted by relevance.
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
