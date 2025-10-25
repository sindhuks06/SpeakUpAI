import streamlit as st
from textblob import TextBlob
import random

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="🎙 SpeakUpAI - Your AI Co-Interviewer",
    page_icon="💬",
    layout="wide"
)

# ---------- CUSTOM CSS (Aesthetic Theme) ----------
st.markdown("""
    <style>
    /* Animated gradient background */
    body {
        background: linear-gradient(-45deg, #1b2735, #090a0f, #283e51, #485563);
        background-size: 400% 400%;
        animation: gradientShift 10s ease infinite;
        color: white;
    }
    @keyframes gradientShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* Header */
    .title {
        text-align: center;
        font-size: 3.5em;
        font-weight: 800;
        background: linear-gradient(90deg, #6a11cb, #2575fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 10px;
        text-shadow: 0 0 25px rgba(37, 117, 252, 0.4);
    }

    .sub {
        text-align: center;
        font-size: 1.3em;
        color: #d0d0d0;
        margin-bottom: 1.5em;
        font-weight: 400;
    }

    /* Glassmorphism cards */
    .glass {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 25px;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 25px;
    }

    /* Chat bubbles */
    .chat-bubble-user {
        background: linear-gradient(135deg, #00c6ff, #0072ff);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 0 20px;
        margin: 8px;
        max-width: 75%;
        float: right;
        clear: both;
        box-shadow: 0 0 10px rgba(0, 114, 255, 0.5);
    }

    .chat-bubble-bot {
        background: linear-gradient(135deg, #ff758c, #ff7eb3);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 20px 0;
        margin: 8px;
        max-width: 75%;
        float: left;
        clear: both;
        box-shadow: 0 0 10px rgba(255, 120, 150, 0.5);
    }

    /* Metric cards */
    .metric-box {
        text-align: center;
        padding: 15px;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.08);
        margin: 5px;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.05);
    }

    /* Animated progress bar */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00c6ff , #0072ff);
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #aaa;
        font-size: 0.9em;
        margin-top: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("<div class='title'>💬 SpeakUpAI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Your AI Interview Partner — Practice • Improve • Shine 🌟</div>", unsafe_allow_html=True)

# ---------- SELECT INTERVIEW MODE ----------
with st.container():
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    mode = st.selectbox("🎯 Choose your interview mode:", ["HR Interview", "Technical Round", "Stress Interview"])
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- QUESTION BANK ----------
questions = {
    "HR Interview": [
        "Tell me about yourself.",
        "What motivates you to perform well at work?",
        "Why should we hire you?",
        "Where do you see yourself in 5 years?"
    ],
    "Technical Round": [
        "Explain OOP concepts in simple terms.",
        "What is a REST API?",
        "How does Python manage memory?",
        "What is the difference between stack and heap memory?"
    ],
    "Stress Interview": [
        "Why are you not better than others?",
        "Convince me you’re not wasting my time.",
        "What will you do if your project fails?",
        "Why should I choose you when others are smarter?"
    ]
}

# ---------- SESSION STATE ----------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []

# ---------- DISPLAY CHAT ----------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
for role, text in st.session_state.chat:
    if role == "user":
        st.markdown(f"<div class='chat-bubble-user'>{text}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>{text}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------- FIRST QUESTION ----------
if len(st.session_state.chat) == 0:
    first_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", first_q))
    st.rerun()

# ---------- USER INPUT ----------
prompt = st.chat_input("💭 Type your answer...")

if prompt:
    st.session_state.chat.append(("user", prompt))

    # ----------- TEXT ANALYSIS -----------
    sentiment = TextBlob(prompt).sentiment.polarity
    if sentiment > 0.2:
        tone = "😊 Confident / Positive"
        remark = "You sound energetic and self-assured — excellent tone!"
    elif sentiment < -0.2:
        tone = "😟 Hesitant / Negative"
        remark = "Try to add more positive phrasing — confidence matters!"
    else:
        tone = "😐 Neutral"
        remark = "Good base — you can elevate it by sounding more assertive."

    filler_words = ["um", "uh", "like", "you know"]
    filler_count = sum(prompt.lower().count(w) for w in filler_words)
    confidence = round((sentiment + 1) / 2 * 100 - filler_count * 5, 1)
    confidence = max(0, min(confidence, 100))

    feedback = {
        "tone": tone,
        "confidence": confidence,
        "filler_words": filler_count,
        "remark": remark
    }
    st.session_state.feedback.append(feedback)

    # ----------- NEXT QUESTION -----------
    next_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", next_q))
    st.rerun()

# ---------- FEEDBACK SUMMARY ----------
st.markdown("<div class='glass'>", unsafe_allow_html=True)
st.subheader("📊 Real-time Feedback Summary")

if st.session_state.feedback:
    last = st.session_state.feedback[-1]
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'><h4>{last['tone']}</h4></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><h4>Confidence: {last['confidence']}%</h4></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'><h4>Filler Words: {last['filler_words']}</h4></div>", unsafe_allow_html=True)
    st.progress(last["confidence"] / 100)
    st.success(last["remark"])
else:
    st.info("Your live feedback will appear after your first answer.")
st.markdown("</div>", unsafe_allow_html=True)

# ---------- PERFORMANCE OVERVIEW ----------
if len(st.session_state.feedback) > 1:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("📈 Confidence Growth Tracker")
    scores = [f["confidence"] for f in st.session_state.feedback]
    st.line_chart(scores, height=220)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("<div class='footer'>🚀 Built with ❤️ by <b>Team SpeakUpAI</b> | AI Hackathon 2025</div>", unsafe_allow_html=True)
