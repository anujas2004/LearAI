# summarizer.py
from transformers import pipeline
import re
from collections import Counter
import pyttsx3

# ---------------- MODEL ----------------
# T5-small for free summarization + simplification
summarizer = pipeline("summarization", model="t5-small")

STOPWORDS = {
    "the", "is", "are", "was", "were", "this", "that", "from",
    "with", "into", "about", "their", "there", "which", "have",
    "has", "had", "will", "would", "could", "should", "can",
    "also", "such", "these", "those", "than", "then", "them"
}

# ---------------- CLEAN TEXT ----------------
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

# ---------------- SUMMARY WITH BULLETS ----------------
def generate_summary(text):
    text = clean_text(text)
    if len(text) < 50:
        return {"summary": "Please provide more text for a meaningful summary.", "bullets": []}

    # Summarize text
    result = summarizer(
        text,
        max_length=180,
        min_length=80,
        num_beams=4,
        length_penalty=1.2,
        do_sample=False
    )
    summary_text = result[0]["summary_text"]

    # Split into sentences
    sentences = [s.strip() for s in re.split(r"\.|\n", summary_text) if len(s.strip()) > 15]

    # Deduplicate sentences
    unique_sentences = list(dict.fromkeys(sentences))

    # First few sentences as bullets (4-6)
    bullets = unique_sentences[:6]

    # Reconstruct cleaned summary
    summary_clean = ". ".join(unique_sentences)

    return {"summary": summary_clean, "bullets": bullets}

# ---------------- TITLE ----------------
def generate_title(summary):
    return " ".join(summary.split()[:2]).title()

# ---------------- KEYWORDS ----------------
def extract_keywords(text, top_n=6):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    common = Counter(words).most_common(top_n)
    return [w[0] for w in common]

# ---------------- WORD COUNT ----------------
def word_count(text):
    return len(text.split())

def reading_time(words):
    return round(words / 200, 2)

# ---------------- TEXT TO SPEECH ----------------
def speak_text(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
