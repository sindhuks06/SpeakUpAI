import streamlit as st
from ai_logic import analyze_response, generate_adaptive_question
from db_manager import get_personalized_context, save_conversation_context, transcribe_audio

# --- Page config ---
st.set_page_config(page_title="🎤 SpeakupAI", page_icon="🎭")

# --- Title ---
st.title("🎤 SpeakupAI — Your AI Co-Interviewer")

# --- Initialize session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display previous messages ---
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# --- Audio Input Section ---
st.write("### 🎙️ Record or Upload Your Answer")
audio_file = st.file_uploader("Upload your answer (MP3/WAV)", type=["mp3", "wav"])

if audio_file:
    # Transcribe audio (placeholder or P3’s real Whisper function)
    user_text = transcribe_audio(audio_file)

    # Show user message
    st.chat_message("user").write(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})

    # Analyze user response
    analysis = analyze_response(user_text)
    save_conversation_context(user_text, analysis)

    st.write("### 📊 Feedback")
    st.json(analysis)

    # Generate next adaptive question
    context = get_personalized_context()
    next_q = generate_adaptive_question(context, user_text)

    st.chat_message("assistant").write(next_q)
    st.session_state.messages.append({"role": "assistant", "content": next_q})

# --- Chat Input Section (Typing) ---
if user_input := st.chat_input("Or type your answer here..."):
    # Show user's message
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Analyze user response
    analysis = analyze_response(user_input)
    save_conversation_context(user_input, analysis)

    st.write("### 📊 Feedback")
    st.json(analysis)

    # Generate next adaptive question
    context = get_personalized_context()
    next_q = generate_adaptive_question(context, user_input)

    st.chat_message("assistant").write(next_q)
    st.session_state.messages.append({"role": "assistant", "content": next_q})
