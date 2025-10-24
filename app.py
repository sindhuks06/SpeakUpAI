import streamlit as st
import json
from utils.feedback import analyze_text
# from utils.ai_helpers import ask_gpt  # Commented out to avoid API calls

# Load question bank
with open("data/question_bank.json") as f:
    question_bank = json.load(f)

st.title("💬 RehearsalRoom - AI Interviewer")

mode = st.selectbox("Choose Interview Type:", ["HR", "Technical", "Stress"])
questions = question_bank[mode]

conversation = []

for i, q in enumerate(questions):
    st.write(f"**AI:** {q}")
    user_answer = st.text_input("Your Answer:", key=f"answer_{i}")
    
    if user_answer:
        # Save the user's answer
        conversation.append({"role": "user", "content": user_answer})
        
        # Feedback from local analysis
        feedback = analyze_text(user_answer)
        st.write(f"**Feedback:** Tone: {feedback['tone']}, Filler Words: {feedback['fillers']}, Confidence Score: {feedback['confidence']}")
        
        # Placeholder AI feedback (no API call)
        ai_followup = "AI feedback placeholder (API skipped for testing)"
        st.write(f"**AI:** {ai_followup}")
