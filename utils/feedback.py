from textblob import TextBlob

FILLER_WORDS = ["um", "uh", "like", "you know"]

def analyze_text(text):
    fillers_used = sum(text.lower().count(word) for word in FILLER_WORDS)
    sentiment = TextBlob(text).sentiment.polarity
    if sentiment > 0.1:
        tone = "Positive/Confident"
    elif sentiment < -0.1:
        tone = "Negative/Uncertain"
    else:
        tone = "Neutral"
    confidence = max(0, 10 - fillers_used)
    return {"tone": tone, "fillers": fillers_used, "confidence": confidence}
