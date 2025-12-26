# 🎤 SpeakUpAI — Adaptive Speech Therapy Assistant

SpeakUpAI is an AI-powered speech therapy assistant that helps users practice pronunciation, fluency, and confidence through adaptive questioning and real-time feedback. It is designed for use by speech therapists, students, and individuals practicing oral communication.

## 🌟 Features

### 🎧 Voice Interaction
- Users can **listen to each question** using built-in audio playback.
- Users can speak in answers.

### 🧠 Adaptive Questioning
- Questions adjust dynamically based on the user's resume.
- Repetitive questions are avoided using session logic.
- GPT-4o provides natural and context-aware evaluation.

### 📊 Smart Feedback
- Feedback is personalized and focused on:
  - Filler Words Used
  - Sentiment Score
  - Tone
  - Confidence

### 🎨 Enhanced Modern UI/UX
Recent UI improvements include:

| Enhancement | Description |
|------------|-------------|
| ✅ Background image | Creates visual depth & brand identity |
| ✅ Dark navy headings | High contrast and professional tone |
| ✅ Hover animations | Smooth UI feedback for interaction |
| ✅ Elevated cards | Clean container for content visibility |
| ✅ Sticky header | Persistent title during scroll |
| ✅ Improved fonts | Cleaner and more readable |
| ✅ Better audio styling | Player is now clearly visible |
| ✅ Soft shadows | Adds depth & premium feel |

---

## 🛠️ Tech Stack

| Component | Technology |
|----------|-------------|
| Frontend | Streamlit (custom CSS for UI) |
| Backend | Python |
| AI Model | GPT-4o |
| Audio | Streamlit native audio playback |
| Session Logic | Python session state |
Contributor fork for portfolio visibility


---

## 📂 Project Structure

SpeakUpAI/
│
├── app.py
├── ai_logic.py
├── config.py
├── db_manager.py
├── analysis_schema.py
├── system_prompts.py
├── demo_reset.py
├── transcribe_audio.py
├── audio_utils.py
├── user_data.json
├── background.jpg
├── test_p3.py
│
├── data/
│   └── question_bank.json
│
├── utils/
│   ├── ai_helpers.py
│   └── feedback.py
│
├── assets/          (exists but currently unused?)
│
├── requirements.txt
├── README.md
├── .env
└── __pycache__/
