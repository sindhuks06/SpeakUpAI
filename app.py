import streamlit as st
from textblob import TextBlob
import random
from PyPDF2 import PdfReader
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import numpy as np
import av

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="🎙 SpeakUpAI - Your AI Co-Interviewer",
    page_icon="💬",
    layout="wide"
)

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
/* Full page background image with gradient overlay */
body {
    background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)),
                url('https://images.unsplash.com/photo-1581091215361-2b61f1a4c64b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80');
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-position: center;
}

/* Header */
.header {
    text-align:center;
    padding:20px;
    border-radius:20px;
    color:white;
    font-size:3em;
    font-weight:bold;
    background: linear-gradient(90deg, #6a11cb, #2575fc);
    box-shadow: 0px 5px 20px rgba(0,0,0,0.4);
    margin-bottom:15px;
}
.subheader {
    text-align:center;
    font-size:1.4em;
    color:#fff;
    margin-bottom:20px;
}

/* Chat bubbles */
.chat-box {
    background: rgba(255,255,255,0.9);
    padding: 12px;
    border-radius: 20px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.2);
    position: relative;
}
.chat-box::after {
    content: "";
    position: absolute;
    bottom: -8px;
    width: 10px; height: 10px;
    background: inherit;
    transform: rotate(45deg);
}
.assistant-msg {background:#d1c4e9;}
.user-msg {background:#ffccbc; margin-left:auto;}
.avatar {height:50px;width:50px;border-radius:50%;margin-right:10px;}

/* Feedback box */
.feedback-box {
    background: rgba(255,255,255,0.95);
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
}

/* Footer */
.footer {
    text-align:center;
    color:white;
    margin-top:20px;
    font-weight:bold;
    font-size:1em;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="header">💬 SpeakUpAI</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Your personal AI interviewer & confidence coach</div>', unsafe_allow_html=True)

# ---------- RESUME UPLOAD ----------
st.subheader("📄 Upload your resume (optional)")
uploaded_file = st.file_uploader("Upload PDF resume", type=["pdf"])

resume_text = ""
if uploaded_file is not None:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        resume_text += page.extract_text()
    st.success("Resume uploaded successfully!")
    st.text_area("Resume Content Preview", resume_text, height=200)

# ---------- INTERVIEW MODE ----------
mode = st.selectbox(
    "🎯 Choose interview mode:",
    ["HR Interview", "Technical Round", "Stress Interview"]
)

st.divider()

# ---------- QUESTION BANK ----------
questions = {
    "HR Interview": ["Tell me about yourself.", "What are your strengths and weaknesses?", "Why should we hire you?"],
    "Technical Round": ["Explain OOP concepts in simple terms.", "What is a REST API?", "How does Python manage memory?"],
    "Stress Interview": ["Why are you not better than others?", "Convince me you’re not wasting my time.", "What will you do if your project fails?"]
}

# ---------- SESSION STATE ----------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []

# ---------- ASK FIRST QUESTION ----------
if len(st.session_state.chat) == 0:
    first_q = f"Can you tell me about your experience with {resume_text.split()[0]}?" if resume_text else random.choice(questions[mode])
    st.session_state.chat.append(("assistant", first_q))

# ---------- DISPLAY CHAT ----------
for role, text in st.session_state.chat:
    avatar = "https://img.icons8.com/ios-filled/50/000000/robot.png" if role=="assistant" else "https://img.icons8.com/ios-filled/50/000000/user.png"
    cls = "assistant-msg" if role=="assistant" else "user-msg"
    st.markdown(f"""
        <div class="chat-box {cls}">
            <img class="avatar" src="{avatar}">
            <div>{text}</div>
        </div>
    """, unsafe_allow_html=True)

# ---------- VOICE INPUT ----------
st.subheader("🎤 Speak your answer (optional)")
webrtc_streamer(key="mic", mode=WebRtcMode.SENDONLY)

# ---------- TEXT INPUT ----------
prompt = st.chat_input("Or type your answer here...")

if prompt:
    st.session_state.chat.append(("user", prompt))
    sentiment = TextBlob(prompt).sentiment.polarity
    tone = "😊 Confident / Positive" if sentiment > 0.2 else "😟 Hesitant / Negative" if sentiment < -0.2 else "😐 Neutral"

    feedback = {
        "tone": tone,
        "confidence": round((sentiment+1)/2*100,1),
        "filler_words": sum(prompt.lower().count(w) for w in ["um","uh","like","you know"])
    }
    st.session_state.feedback.append(feedback)
    next_q = f"Can you elaborate on your project or skill mentioned in your resume?" if resume_text else random.choice(questions[mode])
    st.session_state.chat.append(("assistant", next_q))

# ---------- FEEDBACK ----------
st.divider()
st.subheader("📊 Live Feedback Summary")
if st.session_state.feedback:
    last = st.session_state.feedback[-1]
    st.markdown(f"""
        <div class="feedback-box">
            <b>Tone:</b> {last['tone']}<br>
            <b>Confidence:</b> {last['confidence']}%<br>
            <b>Filler Words:</b> {last['filler_words']}<br>
            <div style='margin-top:10px; background:#ddd; border-radius:5px;'>
                <div style='width:{last['confidence']}%; background: linear-gradient(to right, #6a11cb, #2575fc); padding:5px; border-radius:5px; text-align:center; color:white;'>
                    {last['confidence']}%
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""
<div style="
    position: fixed;
    bottom: 0;
    width: 100%;
    background-color: rgba(0,0,0,0.6);
    color: white;
    text-align: center;
    padding: 10px;
    font-weight: bold;
    z-index: 9999;
">
🚀 Built with ❤ by Team TechTitans | TERRATHON 5.0  
</div>
""", unsafe_allow_html=True)
