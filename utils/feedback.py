# feedback.py
from textblob import TextBlob
import re
from typing import TypedDict

# ------------------- Constants -------------------
FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "actually", "literally"]
HESITATION_PHRASES = ["i think", "maybe", "i guess", "probably", "i'm not sure", "kind of", "sort of"]
CONFIDENT_PHRASES = ["i led", "i built", "i created", "i achieved", "i managed", "i improved", "i delivered"]

# ------------------- Typed Dict -------------------
class Feedback(TypedDict):
    tone: str
    fillers: int
    hesitation: int
    confident_phrases: int
    sentence_structure: str
    confidence_score: float

# ------------------- Analysis Function -------------------
def analyze_text(text: str) -> Feedback:
    """
    Analyze a user's answer and return structured feedback.
    Works for both typed and transcribed audio text.
    """
    text_lower = text.lower().strip()

    # --- Filler words count ---
    fillers_used = sum(text_lower.count(word) for word in FILLER_WORDS)

    # --- Hesitation phrases count ---
    hesitation_count = sum(text_lower.count(phrase) for phrase in HESITATION_PHRASES)

    # --- Confident phrases count ---
    confident_count = sum(text_lower.count(phrase) for phrase in CONFIDENT_PHRASES)

    # --- Sentiment analysis ---
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.25:
        tone = "Positive / Confident"
    elif sentiment < -0.25:
        tone = "Negative / Uncertain"
    else:
        tone = "Neutral / Mixed"

    # --- Sentence structure ---
    sentences = re.split(r"[.!?]", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    avg_sentence_len = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
    if avg_sentence_len > 18:
        structure = "Well-developed / Detailed"
    elif avg_sentence_len > 10:
        structure = "Decent / Clear"
    else:
        structure = "Brief / Could Elaborate More"

    # --- Confidence score (0-100) ---
    # Start with sentiment contribution
    base_conf = (sentiment + 1) / 2 * 60  # maps [-1,1] to [0,60]
    # Add weight for confident phrases
    base_conf += confident_count * 8
    # Subtract weight for fillers and hesitation
    base_conf -= fillers_used * 5
    base_conf -= hesitation_count * 6
    confidence_score = max(0, min(100, round(base_conf, 1)))

    return Feedback(
        tone=tone,
        fillers=fillers_used,
        hesitation=hesitation_count,
        confident_phrases=confident_count,
        sentence_structure=structure,
        confidence_score=confidence_score,
    )
