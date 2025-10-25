import streamlit as st
from textblob import TextBlob
import random
from PyPDF2 import PdfReader
import os
import json
from utils.feedback import analyze_text

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="🎙 SpeakUpAI - Your AI Co-Interviewer",
    page_icon="💬",
    layout="wide"
)

# ---------- USER DATA FILE ----------
USER_DATA_FILE = "user_data.json"
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r") as f:
        user_data = json.load(f)
else:
    user_data = {}

# ---------- SESSION STATE ----------
if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest"
if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "session_count" not in st.session_state:
    st.session_state.session_count = 1

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
body {
    background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)),
                url('https://images.unsplash.com/photo-1581091215361-2b61f1a4c64b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80');
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
    background-position: center;
}
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
.chat-box {
    background: rgba(255,255,255,0.85);
    border-radius: 15px;
    padding: 10px;
    margin-bottom: 10px;
}
.assistant-msg {
    border-left: 4px solid #6a11cb;
}
.user-msg {
    border-left: 4px solid #2575fc;
}
.feedback-box {
    background: rgba(255,255,255,0.85);
    border-radius: 15px;
    padding: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------- GREETING ----------
st.markdown('<div class="header">💬 SpeakUpAI</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subheader">Welcome {st.session_state.user_name}! Session #{st.session_state.session_count}</div>', unsafe_allow_html=True)

# ---------- RESUME UPLOAD ----------
st.subheader("📄 Upload your resume (optional)")
uploaded_file = st.file_uploader("Upload PDF resume", type=["pdf"])
resume_text = ""
if uploaded_file is not None:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        resume_text += page.extract_text() or ""
    st.success("Resume uploaded successfully!")
    st.text_area("Resume Preview", resume_text, height=200)

# ---------- INTERVIEW MODE ----------
mode = st.selectbox(
    "🎯 Choose interview mode:",
    ["HR", "Technical", "Stress"]
)

# ---------- QUESTION BANK ----------
questions = {
    "HR": ["Tell me about yourself.", "Why do you want to work here?", "What is your greatest strength?"],
    "Technical": ["Explain a project you worked on.", "What is polymorphism?", "How do you handle exceptions in Python?"],
    "Stress": ["You failed a project. How do you handle it?", "Describe a conflict you had with a team member."]
}

# ---------- INITIAL QUESTION ----------
if len(st.session_state.chat) == 0:
    first_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", first_q))

# ---------- DISPLAY CHAT ----------
for role, text in st.session_state.chat:
    avatar = "https://img.icons8.com/ios-filled/50/000000/robot.png" if role == "assistant" else "https://img.icons8.com/ios-filled/50/000000/user.png"
    cls = "assistant-msg" if role == "assistant" else "user-msg"
    st.markdown(f"""
        <div class="chat-box {cls}">
            <img class="avatar" src="{avatar}" style="width:25px;height:25px;margin-right:10px;vertical-align:middle;">
            <span>{text}</span>
        </div>
    """, unsafe_allow_html=True)

# ---------- TEXT INPUT ----------
prompt = st.chat_input("Type your answer here...")

if prompt:
    # Add user answer
    st.session_state.chat.append(("user", prompt))

    # Analyze feedback
    feedback = analyze_text(prompt)
    st.session_state.feedback.append(feedback)

    # Next question
    next_q = random.choice(questions[mode])
    st.session_state.chat.append(("assistant", next_q))

# ---------- FEEDBACK DISPLAY ----------
st.divider()
st.subheader("📊 Live Feedback Summary")

if st.session_state.feedback:
    last = st.session_state.feedback[-1]
    # Color code confidence
    if last["confidence_score"] >= 75:
        color = "#4CAF50"
    elif last["confidence_score"] >= 50:
        color = "#FFC107"
    else:
        color = "#F44336"

    st.markdown(f"""
        <div class="feedback-box">
            <b>Tone:</b> {last['tone']}<br>
            <b>Confidence Score:</b> <span style="color:{color}; font-weight:bold">{last['confidence_score']}%</span><br>
            <b>Filler Words:</b> {last['fillers']}<br>
            <b>Hesitation Phrases:</b> {last['hesitation']}<br>
            <b>Confident Phrases:</b> {last['confident_phrases']}<br>
            <b>Sentence Structure:</b> {last['sentence_structure']}<br>
            <div style='margin-top:10px; background:#ddd; border-radius:5px;'>
                <div style='width:{last['confidence_score']}%; background: linear-gradient(to right, #6a11cb, #2575fc); padding:5px; border-radius:5px; text-align:center; color:white;'>
                    {last['confidence_score']}%
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""
<div style="
    position: relative;
    bottom: 0;
    width: 100%;
    background-color: rgba(0,0,0,0.6);
    color: white;
    text-align: center;
    padding: 10px;
    font-weight: bold;
">
🚀 Built with ❤ by Team TechTitans | TERRATHON 5.0 2025
</div>
""", unsafe_allow_html=True)
