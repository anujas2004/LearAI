import streamlit as st
from summarizer import (
    generate_summary,
    generate_title,
    extract_keywords,
    word_count,
    reading_time,
    speak_text
)
from PyPDF2 import PdfReader
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import json
import io

st.set_page_config(page_title="LearAI", layout="centered")

st.title("📘 LearAI – Free AI Study Assistant")
st.write("Simplify, summarize, and manage your study notes using Generative AI")

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "summary" not in st.session_state:
    st.session_state.summary = ""

if "bullets" not in st.session_state:
    st.session_state.bullets = []

if "title" not in st.session_state:
    st.session_state.title = ""

if "keywords" not in st.session_state:
    st.session_state.keywords = []

if "analytics" not in st.session_state:
    st.session_state.analytics = {}

# ---------------- CLEAR HISTORY CALLBACK (FIX) ----------------
def clear_history():
    st.session_state.history = []
    st.session_state.summary = ""
    st.session_state.bullets = []
    st.session_state.title = ""
    st.session_state.keywords = []
    st.session_state.analytics = {}

# ---------------- SIDEBAR ----------------
st.sidebar.title("📚 Summary History")

search_query = st.sidebar.text_input("🔍 Search summaries")

filtered_history = [
    item for item in st.session_state.history
    if search_query.lower() in item["title"].lower()
]

if filtered_history:
    for i, item in enumerate(filtered_history):
        if st.sidebar.button(
            f"{item['title']} ({item['timestamp']})",
            key=f"history_{i}"
        ):
            st.session_state.summary = item["summary"]
            st.session_state.bullets = item["bullets"]
            st.session_state.title = item["title"]
            st.session_state.keywords = item["keywords"]
            st.session_state.analytics = item["analytics"]
else:
    st.sidebar.info("No summaries found.")

# ---- Save history as JSON ----
if st.session_state.history:
    json_data = json.dumps(st.session_state.history, indent=4)
    st.sidebar.download_button(
        "💾 Download History (JSON)",
        json_data,
        file_name="LearAI_History.json",
        mime="application/json"
    )

# ---- Clear history (SINGLE CLICK FIXED) ----
st.sidebar.button(
    "🗑 Clear History",
    on_click=clear_history
)

# ---------------- INPUT ----------------
input_mode = st.radio("📥 Input type", ["Text Input", "Upload PDF"])
text_data = ""

if input_mode == "Text Input":
    text_data = st.text_area("📚 Enter your study material", height=260)
else:
    pdf = st.file_uploader("📄 Upload PDF", type=["pdf"])
    if pdf:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text_data += page.extract_text() or ""
        st.success("PDF text extracted successfully")

# ---------------- GENERATE ----------------
if st.button("✨ Generate Summary"):
    if not text_data.strip():
        st.warning("Please provide text or upload a PDF.")
    else:
        with st.spinner("Generating summary with free AI..."):
            result = generate_summary(text_data)

            original_words = word_count(text_data)
            summary_words = word_count(result["summary"])
            reduction = round(
                ((original_words - summary_words) / original_words) * 100, 2
            )

            analytics = {
                "original_words": original_words,
                "summary_words": summary_words,
                "reduction_percent": reduction,
                "reading_time": reading_time(summary_words)
            }

            summary_data = {
                "title": generate_title(result["summary"]),
                "summary": result["summary"],
                "bullets": result["bullets"],
                "keywords": extract_keywords(text_data),
                "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "analytics": analytics
            }

            # Save current
            st.session_state.summary = summary_data["summary"]
            st.session_state.bullets = summary_data["bullets"]
            st.session_state.title = summary_data["title"]
            st.session_state.keywords = summary_data["keywords"]
            st.session_state.analytics = analytics

            # Add to history
            st.session_state.history.insert(0, summary_data)

# ---------------- DISPLAY ----------------
if st.session_state.summary:

    st.subheader("📝 Generated Title")
    st.write(st.session_state.title)

    st.subheader("📄 Summary")
    st.write(st.session_state.summary)

    if st.button("🔊 Read Summary Aloud"):
        speak_text(st.session_state.summary)

    st.subheader("📌 Important Points")
    for b in st.session_state.bullets:
        st.write("•", b)

    st.subheader("🔑 Keywords")
    st.write(", ".join(st.session_state.keywords))

    st.subheader("📊 Analytics")
    st.info(f"Original Words: {st.session_state.analytics['original_words']}")
    st.info(f"Summary Words: {st.session_state.analytics['summary_words']}")
    st.success(f"Word Reduction: {st.session_state.analytics['reduction_percent']}%")
    st.info(f"Estimated Reading Time: {st.session_state.analytics['reading_time']} minutes")

    # ---------------- PDF DOWNLOAD ----------------
    buffer = io.BytesIO()
    pdf_doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph(st.session_state.title, styles["Title"]))
    content.append(Paragraph("<br/>Summary:<br/>" + st.session_state.summary, styles["Normal"]))
    content.append(Paragraph("<br/><b>Important Points:</b>", styles["Heading2"]))

    for b in st.session_state.bullets:
        content.append(Paragraph("• " + b, styles["Normal"]))

    pdf_doc.build(content)
    buffer.seek(0)

    st.download_button(
        "📄 Download as PDF",
        buffer,
        file_name="LearAI_Output.pdf",
        mime="application/pdf"
    )
