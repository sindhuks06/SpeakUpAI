# test_p3.py
from transcribe_audio import transcribe_audio
from db_manager import save_interview_qa, get_previous_qa

user_id = "user1"

# Step 1: Transcribe audio and get confidence
audio_path = "sample_audio.mp3"  # Replace with your audio file
answer_text, confidence = transcribe_audio(audio_path)
print("Transcribed Text:", answer_text)
print("Confidence:", confidence)

# Step 2: Save Q&A with confidence
question = "Explain primary key in a database."
save_interview_qa(user_id, question, answer_text, confidence)
print("Saved Q&A to DB.")

# Step 3: Retrieve last few Q&A
context = get_previous_qa(user_id)
print("Previous Q&A for user:")
print(context)