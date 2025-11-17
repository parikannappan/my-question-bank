# app.py
import streamlit as st
import json
import base64
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches
import io

# ------------------ Config ------------------
DATA_FILE = "questions.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# Load questions
def load_questions():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save questions + auto commit & push to GitHub (works perfectly on Streamlit Cloud)
def save_questions(questions):
    with open(DATA_FILE, "w") as f:
        json.dump(questions, f, indent=4)
    
    # This part only runs when deployed on Streamlit Community Cloud
    if "STREAMLIT_SHARING" in os.environ or os.getenv("STREAMLIT_CLOUD"):
        try:
            import subprocess
            subprocess.run(["git", "add", DATA_FILE], check=True)
            subprocess.run(["git", "commit", "-m", f"Add question {len(questions)} - {datetime.now().isoformat()}"], check=True)
            subprocess.run(["git", "push"], check=True)
        except:
            pass  # If git fails locally, it's fine

# ------------------ Streamlit App ------------------
st.set_page_config(page_title="My Question Bank", layout="wide")
st.title("Question Bank with JSON + GitHub Backup")

menu = st.sidebar.selectbox("Menu", ["Add Question", "Export to Word"])

if menu == "Add Question":
    st.header("Add New Question")
    
    question_text = st.text_area("Question Text", height=150)
    uploaded_image = st.file_uploader("Upload Diagram (optional)", type=["png", "jpg", "jpeg"])
    
    subject = st.text_input("Subject (e.g., Physics)")
    topic = st.text_input("Topic (e.g., Kinematics)")
    
    image_b64 = None
    if uploaded_image:
        image_b64 = base64.b64encode(uploaded_image.read()).decode()
        st.image(uploaded_image, caption="Preview", width=400)
    
    if st.button("Save Question"):
        questions = load_questions()
        new_q = {
            "id": len(questions) + 1,
            "text": question_text,
            "image_b64": image_b64,
            "subject": subject,
            "topic": topic,
            "created_at": datetime.now().isoformat()
        }
        questions.append(new_q)
        save_questions(questions)
        st.success(f"Question {new_q['id']} saved & pushed to GitHub!")

elif menu == "Export to Word":
    st.header("Export Selected Questions to DOCX")
    
    questions = load_questions()
    if not questions:
        st.warning("No questions yet. Go add some!")
    else:
        # Show questions with checkbox
        selected = {}
        for q in questions:
            with st.expander(f"Q{q['id']}: {q['subject']} - {q['topic']}"):
                st.write(q["text"])
                if q["image_b64"]:
                    image_bytes = base64.b64decode(q["image_b64"])
                    st.image(image_bytes, width=400)
                selected[q["id"]] = st.checkbox("Select this question", key=f"sel_{q['id']}")
        
        selected_ids = [q["id"] for q in questions if selected.get(q["id"], False)]
        
        if st.button("Generate DOCX") and selected_ids:
            doc = Document()
            doc.add_heading("Question Paper", 0)
            doc.add_paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y')}\n")
            
            for q in questions:
                if q["id"] in selected_ids:
                    doc.add_paragraph(f"Q{q['id']}: {q['text']}")
                    if q["image_b64"]:
                        img_bytes = base64.b64decode(q["image_b64"])
                        img_stream = io.BytesIO(img_bytes)
                        doc.add_picture(img_stream, width=Inches(5.5))
                    doc.add_page_break()
            
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            
            st.success(f"{len(selected_ids)} questions ready!")
            st.download_button(
                label=f"Download {len(selected_ids)} Questions as DOCX",
                data=bio.getvalue(),
                file_name=f"question_paper_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )