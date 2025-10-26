import io
import os
import random
import tempfile
import time
from io import BytesIO
import streamlit as st
from gtts import gTTS
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from PyPDF2 import PdfReader
import base64

# ---------- Custom CSS Styling ----------
def set_modern_ui(image_file):
    import base64
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <style>
    /* Background */
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Roboto', sans-serif;
    }}

    /* Headings */
    h1, h2, h3 {{
        text-align: center;
        color: #0D1B2A; /* Dark heading color for blue background */
        font-weight: 700;
        transition: all 0.3s ease;
    }}

    /* Buttons */
    div.stButton > button {{
        background-color: #4A90E2;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, background-color 0.3s ease;
        cursor: pointer;
    }}
    div.stButton > button:hover {{
        background-color: #357ABD;
        transform: scale(1.05);
    }}

    /* Expander headers */
    .streamlit-expanderHeader {{
        color: #4A90E2;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
        transition: all 0.3s ease;
    }}
    .streamlit-expanderHeader:hover {{
        color: #357ABD;
    }}

    /* Floating cards for content sections */
    .stMarkdown, .stTextArea, .stFileUploader {{
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        margin: 15px auto;
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        max-width: 900px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .stMarkdown:hover, .stTextArea:hover, .stFileUploader:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.3);
    }}

    /* Audio player */
    .stAudio {{
        max-width: 800px;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
        background: #ffffff;
        padding: 10px;
        margin: 20px auto;
        transition: all 0.3s ease;
    }}

    /* Center everything */
    .block-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 40px;
        padding-bottom: 40px;
    }}

    /* Smooth section transition */
    .stApp, .stMarkdown, .stTextArea, .stFileUploader, .stAudio, h1, h2, h3 {{
        transition: all 0.3s ease-in-out;
    }}

    </style>
    """, unsafe_allow_html=True)


# Call the function at the top of your app.py
set_modern_ui("background.jpg")


# ---------- Load Environment and AI Logic ----------
load_dotenv()
from ai_logic import generate_adaptive_question, analyze_response_gpt4o

# ---------- Streamlit Setup ----------
st.set_page_config(page_title="💬 SpeakUpAI", layout="centered")
st.title("💬 SpeakUpAI - AI Resume Interviewer")

# ---------- Initialize Session State ----------
for key, default in {
    "user_id": "demo_user",
    "interview_active": False,
    "q_index": 0,
    "answers_by_question": {},
    "questions": [],
    "current_question": "",
    "summary_shown": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Helper Functions ----------
def count_fillers(text: str) -> int:
    """Count filler words in the given text."""
    if not text:
        return 0
        
    # Common filler words and phrases
    fillers = {
        # Basic fillers
        "um", "uh", "er", "ah", "like", "hmm", "huh",
        
        # Hesitation words
        "basically", "actually", "literally", "obviously",
        
        # Hedging phrases
        "you know", "kind of", "sort of", "i mean",
        "i guess", "i think", "maybe", "probably",
        
        # Unnecessary qualifiers
        "just", "really", "very", "quite", "fairly",
        
        # Vague references
        "stuff", "things", "something", "whatever",
        
        # Time fillers
        "so", "well", "right", "okay", "anyway",
        
        # Double words (will be matched as phrases)
        "like like", "you know like", "i mean like",
        "so basically", "kind of like"
    }
    
    # Convert text to lowercase for case-insensitive matching
    text = text.lower()
    
    # Count individual filler words
    words = text.split()
    word_count = sum(1 for word in words if word in fillers)
    
    # Count filler phrases (2-3 word combinations)
    phrases = [" ".join(words[i:i+3]) for i in range(len(words)-2)]
    phrases.extend([" ".join(words[i:i+2]) for i in range(len(words)-1)])
    phrase_count = sum(1 for phrase in phrases if phrase in fillers)
    
    # Get unique matches for debugging
    matches = set(word for word in words if word in fillers)
    matches.update(phrase for phrase in phrases if phrase in fillers)
    st.write("Debug - Found filler words/phrases:", sorted(matches))
    
    return word_count + phrase_count

def speak_text_bytes(text: str) -> BytesIO:
    tts = gTTS(text)
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf

def generate_resume_based_questions(resume_text, num_questions=3):
    """Generate interview questions from the uploaded resume."""
    questions = []
    current_question = f"Based on this resume, ask an insightful interview question:\n\n{resume_text[:1500]}"
    for _ in range(num_questions):
        q = generate_adaptive_question(current_question=current_question, user_answer="", user_id="resume_user")
        if q:
            questions.append(q)
            current_question = q
        else:
            break
    return questions

# ---------- Resume Upload ----------
st.subheader("📄 Upload your Resume")
uploaded_file = st.file_uploader("Upload your PDF Resume", type=["pdf"])
resume_text = ""

if uploaded_file:
    try:
        pdf = PdfReader(uploaded_file)
        resume_text = " ".join([page.extract_text() or "" for page in pdf.pages])
        st.success("✅ Resume uploaded successfully!")
        st.text_area("Resume Preview", resume_text[:2000], height=180)
    except Exception as e:
        st.error(f"Could not read PDF: {e}")

# ---------- Control Buttons ----------
col1, col2 = st.columns([3, 1])
with col1:
    start = st.button("🚀 Start Interview")
with col2:
    reset = st.button("🔁 Reset")

if reset:
    for k in st.session_state.keys():
        del st.session_state[k]
    st.rerun()

# ---------- Start Interview ----------
if start and not st.session_state.interview_active:
    if not resume_text.strip():
        st.warning("Please upload your resume first.")
    else:
        st.session_state.questions = generate_resume_based_questions(resume_text)
        if not st.session_state.questions:
            st.error("AI couldn't generate questions. Try uploading a different resume.")
        else:
            st.session_state.interview_active = True
            st.session_state.q_index = 0
            st.session_state.current_question = st.session_state.questions[0]
            st.session_state.summary_shown = False
            st.rerun()

# ---------- Interview Flow ----------
if st.session_state.interview_active:
    q_idx = st.session_state.q_index
    questions = st.session_state.questions
    current_q = st.session_state.current_question
    total = len(questions)

    st.progress(q_idx / total)
    st.markdown(f"### Question {q_idx + 1} of {total}")
    st.markdown(f"{current_q}")

    # Play question
    with st.expander("🔊 Listen to question", expanded=True):
        st.audio(speak_text_bytes(current_q), format="audio/mp3")

    st.subheader("🎤 Record your Answer")
    audio_bytes = audio_recorder(key=f"rec_{q_idx}")

    if audio_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            tmpfile.write(audio_bytes)
            tmp_path = tmpfile.name

        import speech_recognition as sr
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(tmp_path) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio_data = recognizer.record(source)
            user_text = recognizer.recognize_google(audio_data)
            st.success("✅ Answer recorded and transcribed!")
            st.markdown(f"Transcript: {user_text}")

            # Calculate metrics without AI
            words = user_text.split()
            word_count = len(words)
            filler_count = count_fillers(user_text)
            words_per_minute = (word_count / 60) * 1.5  # Rough estimate
            
            # Calculate confidence score based on various factors
            confidence_factors = {
                'filler_ratio': 1.0 - min(1.0, filler_count / (word_count * 0.1)),  # Penalize high filler word ratio
                'length_score': min(1.0, word_count / 50),  # Reward substantial answers up to 50 words
                'structure_score': 0.5  # Base structure score
            }
            
            # Adjust structure score based on answer patterns
            structure_markers = {
                'examples': ['for example', 'such as', 'instance', 'specifically'],
                'reasoning': ['because', 'therefore', 'thus', 'since', 'as a result'],
                'organization': ['first', 'second', 'finally', 'moreover', 'additionally']
            }
            
            for marker_type, phrases in structure_markers.items():
                if any(phrase in user_text.lower() for phrase in phrases):
                    confidence_factors['structure_score'] += 0.2  # Bonus for good structure
            
            # Calculate final confidence score
            confidence = sum(confidence_factors.values()) / len(confidence_factors)
            confidence = max(0.0, min(1.0, confidence))  # Ensure between 0 and 1
            
            # Determine tone based on confidence and filler words
            if confidence > 0.8:
                tone = "Very Confident"
            elif confidence > 0.6:
                tone = "Confident"
            elif confidence < 0.4:
                tone = "Hesitant"
            elif confidence < 0.5:
                tone = "Uncertain"
            else:
                tone = "Neutral"
            
            # Generate suggestions based on metrics
            suggestions = []
            if filler_count > word_count * 0.1:
                suggestions.append(f"Reduce filler words - found {filler_count} in your answer")
            if word_count < 30:
                suggestions.append("Provide more detailed responses")
            if confidence_factors['structure_score'] < 0.7:
                suggestions.append("Use more structured responses with examples and clear reasoning")
            
            # Basic sentiment analysis (simple positive/negative word counting)
            positive_words = {'great', 'good', 'excellent', 'best', 'strong', 'confident', 'successful', 'achieve', 'improve', 'positive'}
            negative_words = {'bad', 'weak', 'poor', 'fail', 'difficult', 'hard', 'problem', 'challenge', 'negative', 'worst'}
            
            words_lower = set(user_text.lower().split())
            positive_count = len(words_lower.intersection(positive_words))
            negative_count = len(words_lower.intersection(negative_words))
            
            if positive_count + negative_count > 0:
                sentiment = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                sentiment = 0.0

            # Store analysis
            st.session_state.answers_by_question[current_q] = {
                "answer": user_text,
                "confidence": confidence,
                "sentiment": sentiment,
                "tone": tone,
                "filler_count": filler_count,
                "suggestions": suggestions
            }

            # --- Display Analysis Immediately ---
            st.markdown("### 📊 AI Feedback for this Answer")
            st.markdown(f"""
- Confidence: {confidence:.2f}  
- Sentiment Score: {sentiment:.2f}  
- Tone: {tone}  
- Filler Words Used: {filler_count}  
""")
            if suggestions:
                st.markdown("Improvement Suggestions:")
                for s in suggestions:
                    st.info(f"💡 {s}")

            os.remove(tmp_path)

        except Exception as e:
            st.error(f"Transcription failed: {e}")

# ---------- Interview Flow ----------
current_q = st.session_state.get("current_question", "")

if current_q and current_q in st.session_state.answers_by_question:
    st.write("---")
    if st.session_state.q_index + 1 < len(st.session_state.questions):
        if st.button("Continue to Next Question ➡"):
            st.session_state.q_index += 1
            st.session_state.current_question = st.session_state.questions[st.session_state.q_index]
            st.rerun()
    else:
        if st.button("✅ Complete Interview and Show Summary"):
            st.session_state.interview_active = False
            st.session_state.summary_shown = True
            st.rerun()


# ---------- Final Summary (AI-Generated Human-Readable Report) ----------
if st.session_state.summary_shown and st.session_state.answers_by_question:
    st.header("📋 Comprehensive AI Interview Report")

    # --- Compute metrics ---
    answers = list(st.session_state.answers_by_question.values())
    avg_confidence = sum(a.get("confidence", 0) for a in answers) / len(answers)
    avg_sentiment = sum(a.get("sentiment", 0) for a in answers) / len(answers)
    total_fillers = sum(a.get("filler_count", 0) for a in answers)

    # --- Display overall metrics ---
    st.subheader("🎯 Overall Metrics")
    cols = st.columns(4)
    cols[0].metric("Confidence", f"{avg_confidence:.2f}/1.0")
    cols[1].metric("Sentiment", f"{avg_sentiment:.2f}")
    cols[2].metric("Filler Words", str(total_fillers))
    cols[3].metric("Questions Answered", f"{len(answers)}")

    # --- Generate human-readable AI report ---
    combined_text = "\n\n".join(
        f"Q{i+1}: {q}\nA{i+1}: {a['answer']}"
        for i, (q, a) in enumerate(st.session_state.answers_by_question.items())
    )

    with st.spinner("🤖 Generating AI feedback in Markdown style..."):
        ai_report = analyze_response_gpt4o(combined_text, avg_wpm=120)
    
    if ai_report:
        # Safely extract human-readable content from feedback object
        if hasattr(ai_report, "dict"):
            report_content = getattr(ai_report, "human_readable", None) or ai_report.dict
        else:
            report_content = {k: getattr(ai_report, k, None) for k in dir(ai_report) if not k.startswith("_")}
        
        # Print AI-generated report in Markdown style
        st.subheader("💬 AI Feedback Report")
        if isinstance(report_content, str):
            st.markdown(report_content)
        elif isinstance(report_content, dict):
            # Combine all keys for a readable report
            for key, val in report_content.items():
                if isinstance(val, list):
                    st.markdown(f"{key.replace('_',' ').title()}:")
                    for v in val:
                        st.info(f"💡 {v}")
                else:
                    st.markdown(f"{key.replace('_',' ').title()}:** {val}")
        else:
            st.write(report_content)
    else:
        st.warning("⚠ AI feedback could not be generated. Please check your API key or connection.")

    # --- Detailed conversation history ---
    st.subheader("📝 Conversation History & Answer Analysis")
    for i, (q, data) in enumerate(st.session_state.answers_by_question.items(), 1):
        with st.expander(f"Q{i}: {q}"):
            st.markdown("Your Answer:")
            st.write(data["answer"])
            
            cols = st.columns(3)
            cols[0].metric("Confidence", f"{data.get('confidence', 0):.2f}")
            cols[1].metric("Sentiment", f"{data.get('sentiment', 0):.2f}")
            cols[2].metric("Filler Words", str(data.get("filler_count", 0)))
            
            if data.get("suggestions"):
                st.markdown("🎯 Improvement Suggestions:")
                for s in data["suggestions"]:
                    st.info(f"💡 {s}")

    # --- Overall areas for improvement ---
    st.subheader("💪 Areas for Improvement")
    improvements = []
    if avg_confidence < 0.7:
        improvements.append("- Confidence: Speak more assertively and clearly.")
    if total_fillers > 5:
        improvements.append("- Speech Clarity: Reduce filler words like 'um', 'uh', 'like'.")
    if avg_sentiment < 0.2:
        improvements.append("- Positive Tone: Maintain a positive and enthusiastic tone.")

    if improvements:
        for imp in improvements:
            st.markdown(imp)
    else:
        st.success("🌟 Excellent performance! Keep up the strong interview skills.")

    # --- Next steps ---
    st.subheader("📈 Recommended Next Steps")
    st.markdown("""
1. Practice Regularly: Record yourself answering common interview questions.
2. Speech Clarity: Reduce filler words by practicing concise answers.
3. Positive Framing: Keep a confident and upbeat tone.
4. Body Language: Practice posture and gestures while speaking.
5. Mock Interviews: Seek feedback from peers or mentors.
""")

    # --- Reset Button for New Interview ---
    st.write("---")
    if st.button("🔄 Start New Interview"):
        for k in ["answers_by_question", "interview_active", "q_index", "questions", "current_question", "summary_shown"]:
            st.session_state[k] = {} if k == "answers_by_question" else False if k in ["interview_active","summary_shown"] else 0 if k=="q_index" else ""
        st.success("Interview reset. You can start a new session now!")
        st.rerun()