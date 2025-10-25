import streamlit as st
from textblob import TextBlob
import random

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="🎙 SpeakUpAI - Your AI Co-Interviewer",
    page_icon="💬",
    layout="centered"
)

# ---------- HEADER ----------
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 2.5em;
            color: #ffffff;
            background: linear-gradient(90deg, #6a11cb, #2575fc);
            padding: 0.6em;
            border-radius: 10px;
            margin-bottom: 1em;
        }
        .sub {
            text-align: center;
            font-size: 1.2em;
            color: #666;
            margin-bottom: 1.5em;
        }
    </style>
    <div class="title">💬 SpeakUpAI</div>
    <div class="sub">Your personal AI interviewer & confidence coach</div>
""", unsafe_allow_html=True)

# ---------- SELECT INTERVIEW MODE ----------
mode = st.selectbox(
    "🎯 Choose interview mode:",
    ["HR Interview", "Technical Round", "Stress Interview"]
)

st.divider()

# ---------- QUESTION BANK ----------
questions = {
    "HR Interview": [
        "Tell me about yourself.",
        "What are your strengths and weaknesses?",
        "Why should we hire you?"
    ],
    "Technical Round": [
        "Explain OOP concepts in simple terms.",
        "What is a REST API?",
        "How does Python manage memory?"
    ],
    "Stress Interview": [
        "Why are you not better than others?",
        "Convince me you’re not wasting my time.",
        "What will you do if your project fails?"
    ]
}

# ---------- SESSION STATE ----------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []

# ---------- DISPLAY CHAT ----------
for role, text in st.session_state.chat:
    with st.chat_message(role):
        st.write(text)

# ---------- ASK QUESTION ----------
if len(st.session_state.chat) == 0:
    first_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", first_q))
    st.rerun()

# ---------- USER INPUT ----------
prompt = st.chat_input("Your response...")

if prompt:
    # Add user message
    st.session_state.chat.append(("user", prompt))

    # Simple tone analysis using TextBlob
    sentiment = TextBlob(prompt).sentiment.polarity
    if sentiment > 0.2:
        tone = "😊 Confident / Positive"
    elif sentiment < -0.2:
        tone = "😟 Hesitant / Negative"
    else:
        tone = "😐 Neutral"

    # Generate feedback
    feedback = {
        "tone": tone,
        "confidence": round((sentiment + 1) / 2 * 100, 1),
        "filler_words": sum(prompt.lower().count(w) for w in ["um", "uh", "like", "you know"])
    }
    st.session_state.feedback.append(feedback)

    # Next question
    next_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", next_q))
    st.rerun()

# ---------- FEEDBACK SUMMARY ----------
st.divider()
st.subheader("📊 Live Feedback Summary")

if st.session_state.feedback:
    last = st.session_state.feedback[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric("Tone", last["tone"])
    col2.metric("Confidence (%)", f"{last['confidence']}")
    col3.metric("Filler words", last["filler_words"])

    st.progress(last["confidence"] / 100)
else:
    st.info("Your feedback will appear here after your first answer.")

# ---------- FOOTER ----------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:gray;'>🚀 Built with ❤️ by Team TechTitans | AI Hackathon 2025</p>",
    unsafe_allow_html=True
)
