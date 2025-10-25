import io
import re
import tempfile
import random
from typing import List

import streamlit as st
import streamlit.components.v1 as components
from gtts import gTTS
from io import BytesIO
from streamlit_webrtc import webrtc_streamer

from db_manager import save_interview_qa, get_previous_qa, transcribe_audio

# ---------- Helper: Sentiment Analysis ----------
from textblob import TextBlob

def sentiment_polarity(text: str) -> float:
    """Returns sentiment polarity between -1 (negative) and 1 (positive)."""
    if not text or text.strip() == "":
        return 0.0
    blob = TextBlob(text)
    return blob.sentiment.polarity

def count_fillers(text: str) -> int:
    """Counts common filler words like 'um', 'uh', 'like', etc."""
    fillers = ["um", "uh", "like", "you know", "actually", "basically", "literally"]
    text_lower = text.lower()
    return sum(text_lower.count(f) for f in fillers)



st.set_page_config(page_title="💬 SpeakUpAI", layout="centered")


def speak_text_bytes(text: str) -> BytesIO:
    """Return an in-memory mp3 BytesIO for the given text using gTTS."""
    tts = gTTS(text)
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf


st.title("💬 SpeakUpAI - AI Mock Interviewer")

# ---------- session state setup ----------
if "user_id" not in st.session_state:
    st.session_state.user_id = "demo_user"
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "questions" not in st.session_state:
    st.session_state.questions = []


# ---------- Resume upload ----------
st.subheader("📄 Upload your resume (optional)")
uploaded_file = st.file_uploader("Upload PDF resume", type=["pdf"])
resume_text = ""
if uploaded_file is not None:
    try:
        pdf_bytes = uploaded_file.read()
        from PyPDF2 import PdfReader

        pdf = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
        resume_text = " ".join(pages).strip()
        st.success("Resume uploaded")
        st.text_area("Resume preview (first 2000 chars)", resume_text[:2000], height=180)
    except Exception as e:
        st.error(f"Could not parse resume: {e}")


# ---------- Interview mode and question bank ----------
mode = st.selectbox("🎯 Choose interview mode:", ["HR Interview", "Technical Round", "Stress Interview"])

QUESTION_BANK = {
    "HR Interview": [
        "Tell me about yourself.",
        "What are your strengths and weaknesses?",
        "Why should we hire you?",
        "Describe a time you solved a difficult problem.",
        "Where do you see yourself in 5 years?",
        "How do you handle feedback?",
        "What motivates you?",
    ],
    "Technical Round": [
        "Explain OOP concepts in simple terms.",
        "What is a REST API?",
        "How does Python manage memory?",
        "Describe how you would design a scalable web service.",
        "Explain a project where you used algorithms or data structures.",
        "How do you test and debug your code?",
        "What tradeoffs do you consider when optimizing performance?",
    ],
    "Stress Interview": [
        "Why are you not better than others?",
        "Convince me you’re not wasting my time.",
        "What will you do if your project fails?",
        "Why should we trust you to lead?",
        "Tell me something you regret.",
        "Explain why this company should hire you immediately.",
        "What would you do differently in your last role?",
    ],
}


# ---------- Control panel: start / reset ----------
col1, col2 = st.columns([3, 1])
with col1:
    start = st.button("Start Interview")
with col2:
    reset = st.button("Reset")

if reset:
    st.session_state.interview_active = False
    st.session_state.questions = []
    st.session_state.q_index = 0
    st.session_state.answers = []
    st.session_state.feedback = []
    st.success("Interview reset")

if start and not st.session_state.interview_active:
    # Prepare 7 questions
    if resume_text:
        # personalize first question if possible
        tokens = re.findall(r"\w+", resume_text)
        first = f"Can you tell me about your experience with {tokens[0]}?" if tokens else None
    else:
        first = None

    pool = QUESTION_BANK.get(mode, [])[:]
    random.shuffle(pool)
    # Ensure deterministic length 7
    questions = []
    if first:
        questions.append(first)
    # fill the rest from pool
    for q in pool:
        if len(questions) >= 7:
            break
        if q not in questions:
            questions.append(q)
    # if still fewer than 7 (unlikely), pad with repeats
    while len(questions) < 7:
        questions.append(random.choice(pool or ["Tell me about yourself."]))

    st.session_state.questions = questions[:7]
    st.session_state.q_index = 0
    st.session_state.answers = []
    st.session_state.feedback = []
    st.session_state.interview_active = True
    try:
        st.experimental_rerun()
    except AttributeError:
        # Streamlit may not expose experimental_rerun in this version; toggle a session key to force rerun
        st.session_state["_rerun_flag"] = not st.session_state.get("_rerun_flag", False)


# ---------- Interview runtime ----------
from audio_recorder_streamlit import audio_recorder
import tempfile
import os
import time

if "answers" not in st.session_state:
    st.session_state.answers = []
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "q_index" not in st.session_state:
    st.session_state.q_index = 0

if st.session_state.interview_active:
    questions = st.session_state.questions
    q_idx = st.session_state.q_index

    if q_idx < len(questions):
        current_q = questions[q_idx]
        st.markdown(f"### Question {q_idx + 1} of {len(questions)}")
        st.write(current_q)

        # 🔊 AI speaks the question
        try:
            st.audio(speak_text_bytes(current_q), format="audio/mp3")
        except Exception:
            st.warning("Audio playback unavailable.")

        st.subheader("🎤 Record your answer")

        audio_bytes = audio_recorder(
            pause_threshold=1.2,
            sample_rate=44100,
            icon_size="2x",
        )

        if audio_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmpfile.write(audio_bytes)
                tmp_path = tmpfile.name

            user_text, confidence = transcribe_audio(tmp_path)
            os.remove(tmp_path)

            sentiment_score = sentiment_polarity(user_text)
            tone = (
                "Confident / Positive" if sentiment_score > 0.2 else
                "Hesitant / Negative" if sentiment_score < -0.2 else
                "Neutral"
            )
            filler_count = count_fillers(user_text)

            # Save the answer for summary
            st.session_state.answers.append({
                "question": current_q,
                "answer": user_text,
                "confidence": confidence,
                "tone": tone,
                "sentiment": sentiment_score,
                "fillers": filler_count,
            })

            st.success("✅ Answer recorded and transcribed successfully!")
            st.write(f"*Transcript:* {user_text}")
            st.write(f"*Confidence:* {confidence:.2f}")
            st.write(f"*Tone:* {tone}")
            st.write(f"*Filler words:* {filler_count}")

            # ✅ Next Question Button
            if st.button("➡ Next Question"):
                st.session_state.q_index += 1
                if st.session_state.q_index >= len(st.session_state.questions):
                    st.session_state.interview_active = False
                st.rerun()

    else:
        # ✅ End of interview - Show Summary
        st.session_state.interview_active = False
        st.subheader("📋 Interview Summary Report")

        total_conf = sum(a["confidence"] for a in st.session_state.answers) / len(st.session_state.answers)
        total_fillers = sum(a["fillers"] for a in st.session_state.answers)
        avg_sent = sum(a["sentiment"] for a in st.session_state.answers) / len(st.session_state.answers)

        st.write(f"*Average Transcript Confidence:* {total_conf:.2f}")
        st.write(f"*Total Filler Words:* {total_fillers}")
        st.write(f"*Average Sentiment:* {avg_sent:.2f}")

        st.divider()

        for i, a in enumerate(st.session_state.answers, 1):
            st.markdown(f"*Q{i}. {a['question']}*")
            st.write(a['answer'])
            st.caption(f"Confidence: {a['confidence']:.2f} | Tone: {a['tone']} | Fillers: {a['fillers']}")

        st.divider()

        # 💡 AI Improvement Suggestions
        improvements = []
        if total_conf < 0.6:
            improvements.append("Try to speak more clearly and maintain consistent volume.")
        if total_fillers > 5:
            improvements.append("Reduce filler words like 'um', 'uh', 'like'.")
        if avg_sent < 0:
            improvements.append("Try to sound more positive or confident in your tone.")
        if not improvements:
            improvements.append("Excellent delivery and tone! Keep practicing structured answers.")

        st.subheader("💡 Feedback & Improvement Suggestions")
        for tip in improvements:
            st.write(f"• {tip}")

        # Reset button for new session
        if st.button("🔁 Start New Interview"):
            for key in ["answers", "q_index", "interview_active", "questions"]:
                st.session_state.pop(key, None)
            st.success("New session started!")
            st.rerun()



# ---------- When interview ends: show report ----------
if not st.session_state.get("interview_active", False) and st.session_state.get("answers"):
    st.divider()
    st.subheader("📋 Interview Summary Report")

    answers = st.session_state.answers
    # Aggregate metrics
    avg_conf = sum(a.get("transcript_confidence", 0) for a in answers) / max(1, len(answers))
    total_fillers = sum(a.get("filler_count", 0) for a in answers)
    avg_sentiment = sum(a.get("sentiment_score", 0) for a in answers) / max(1, len(answers))

    st.metric("Average Transcript Confidence", f"{avg_conf:.2f}")
    st.metric("Total Filler Words", f"{total_fillers}")
    st.metric("Average Sentiment", f"{avg_sentiment:.2f}")

    for i, a in enumerate(answers, 1):
        st.markdown(f"*Q{i}. {a['question']}*")
        st.write(a["answer"])
        st.write(f"Confidence: {a['transcript_confidence']:.2f} | Tone: {a['tone']} | Fillers: {a['filler_count']}")

    # Offer a downloadable text report
    report_lines = ["Interview Summary\n"]
    report_lines.append(f"User: {st.session_state.user_id}\n")
    report_lines.append(f"Mode: {mode}\n")
    report_lines.append(f"Average Confidence: {avg_conf:.2f}\n")
    report_lines.append(f"Total Fillers: {total_fillers}\n")
    report_lines.append("\nDetails:\n")
    for i, a in enumerate(answers, 1):
        report_lines.append(f"Q{i}: {a['question']}\n")
        report_lines.append(f"A{i}: {a['answer']}\n")
        report_lines.append(f"Confidence: {a['transcript_confidence']:.2f}, Tone: {a['tone']}, Fillers: {a['filler_count']}\n\n")

    report_text = "".join(report_lines)
    st.download_button("Download summary report", report_text, file_name="interview_report.txt")

    # Also show previous Q&A from DB
    try:
        prev_qa = get_previous_qa(st.session_state.user_id)
        st.subheader("📜 Previous Answers (from DB)")
        st.text(prev_qa)
    except Exception:
        st.info("No previous Q&A available or DB query failed.")