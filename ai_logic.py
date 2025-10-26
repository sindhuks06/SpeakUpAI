# ai_logic.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from textblob import TextBlob
import re
import json
import random

load_dotenv()

# Initialize OpenAI Client
API_KEY = os.getenv("OPENAI_API_KEY")
if API_KEY is None:
    raise ValueError("❌ OPENAI_API_KEY not found. Please create a .env file and set the key.")

client = OpenAI(api_key=API_KEY)

# ----------------------------------------
# Feedback Data Class (moved outside)
# ----------------------------------------
class Feedback:
    def __init__(self, confidence=0.5, tone_description="Neutral",
                 filler_word_count=0, sentiment_score=0.0,
                 suggestions=None):
        self.confidence = confidence
        self.tone_description = tone_description
        self.filler_word_count = filler_word_count
        self.sentiment_score = sentiment_score
        self.suggestions = suggestions if suggestions else []


# ----------------------------------------
# 🎯 Generate Adaptive Interview Question
# ----------------------------------------
def generate_adaptive_question(current_question: str, user_answer: str,
                               user_id: str = "default_user") -> str:
    try:
        prompt = f"""
        You are an expert HR interviewer.
        Given the current question and the candidate's previous answer,
        ask ONE relevant follow-up interview question.

        Previous Question: {current_question}
        Candidate Answer: {user_answer}

        The question should:
        - Be contextual
        - Not repeat previous questions
        - Be professional
        - Be open-ended
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional interviewer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=120,
            temperature=0.7,
        )

        question = response.choices[0].message.content.strip()
        if not question.endswith("?"):
            question += "?"
        return question

    except Exception as e:
        print(f"[AI ERROR - Question Generation]: {e}")
        return random.choice([
            "Can you describe a challenging project you worked on?",
            "What’s one thing you’re most proud of in your career?",
            "How do you handle tight deadlines?"
        ])


# ----------------------------------------
# 🧩 Analyze Response
# ----------------------------------------
def analyze_response_gpt4o(transcript_text: str, avg_wpm: float = 120):
    if not transcript_text.strip():
        return Feedback(0.0, "Neutral", 0, 0.0)

    try:
        sentiment = TextBlob(transcript_text).sentiment.polarity
        filler_words = len(re.findall(r"\b(um+|uh+|like|you know|so)\b",
                                      transcript_text.lower()))

        prompt = f"""
        You are an expert communication coach. Analyze this response:
        "{transcript_text}"

        Return ONLY JSON in this structure:
        {{
            "confidence_level": 0.0,
            "tone_description": "string",
            "suggestions": ["string1", "string2"]
        }}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You evaluate professional communication."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.4,
        )

        # Ensure clean JSON extraction
        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        confidence = float(parsed.get("confidence_level", 0.5))
        tone = parsed.get("tone_description", "Neutral")
        suggestions = parsed.get("suggestions", [])

        return Feedback(confidence, tone, filler_words, sentiment, suggestions)

    except Exception as e:
        print(f"[AI ERROR - Response Analysis]: {e}")
        return Feedback(0.5, "Neutral", 0, 0.0)
