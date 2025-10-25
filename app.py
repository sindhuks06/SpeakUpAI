import streamlit as st
from textblob import TextBlob
import random
from PyPDF2 import PdfReader
import os
import json

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
    st.session_state.user_name = None
if "chat" not in st.session_state:
    st.session_state.chat = []
if "feedback" not in st.session_state:
    st.session_state.feedback = []
if "session_count" not in st.session_state:
    st.session_state.session_count = 0

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
body {
    background: linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.3)),
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

.login-box {
    background: rgba(255,255,255,0.9);
    padding: 25px;
    border-radius: 20px;
    max-width: 400px;
    margin: auto;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
    text-align: center;
}

.footer {
    text-align:center;
    color:white;
    margin-top:20px;
    font-weight:bold;
    font-size:1em;
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

# ---------- LOGIN PAGE ----------
if st.session_state.user_name is None:
    st.markdown('<div class="header">💬 SpeakUpAI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheader">Your personal AI interviewer & confidence coach</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.subheader("👤 Login / Enter Your Name")
    name_input = st.text_input("Enter your name to start:", "")
    if st.button("Start Session"):
        if name_input.strip() != "":
            st.session_state.user_name = name_input.strip()

            # Memory Echo
            if st.session_state.user_name in user_data:
                st.session_state.session_count = user_data[st.session_state.user_name]["session_count"] + 1
                st.success(f"Welcome back {st.session_state.user_name}! 🎉 This is your session #{st.session_state.session_count}")
            else:
                st.session_state.session_count = 1
                st.success(f"Welcome {st.session_state.user_name}! 🎉 Let's start your first session")

            # Initialize user data
            user_data[st.session_state.user_name] = {
                "session_count": st.session_state.session_count,
                "last_mode": None,
                "last_resume": ""
            }
            with open(USER_DATA_FILE, "w") as f:
                json.dump(user_data, f, indent=4)
            
            st.stop()  # replaces deprecated experimental_rerun
        else:
            st.error("Please enter a valid name.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ---------- GREETING ----------
st.markdown('<div class="header">💬 SpeakUpAI</div>', unsafe_allow_html=True)
st.markdown(f'<div class="subheader">Welcome back {st.session_state.user_name}! This is your session #{st.session_state.session_count}</div>', unsafe_allow_html=True)

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
    user_data[st.session_state.user_name]["last_resume"] = resume_text

# ---------- INTERVIEW MODE ----------
mode = st.selectbox(
    "🎯 Choose interview mode:",
    ["HR Interview", "Technical Round", "Stress Interview"]
)
user_data[st.session_state.user_name]["last_mode"] = mode

# Save JSON updates
with open(USER_DATA_FILE, "w") as f:
    json.dump(user_data, f, indent=4)

st.divider()

# ---------- QUESTION BANK ----------
questions = {
    "HR Interview": ["Tell me about yourself.", "What are your strengths and weaknesses?", "Why should we hire you?"],
    "Technical Round": ["Explain OOP concepts in simple terms.", "What is a REST API?", "How does Python manage memory?"],
    "Stress Interview": ["Why are you not better than others?", "Convince me you’re not wasting my time.", "What will you do if your project fails?"]
}

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
            <img class="avatar" src="{avatar}" style="width:25px;height:25px;margin-right:10px;vertical-align:middle;">
            <span>{text}</span>
        </div>
    """, unsafe_allow_html=True)

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
🚀 Built with ❤ by Team TechTitans | TERRATHON 5.0 2025
</div>
""", unsafe_allow_html=True)

