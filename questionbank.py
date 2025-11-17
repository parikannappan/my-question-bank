# app.py  (or questionbank.py)  → Updated version with Edit, Delete & Auto-refresh
import streamlit as st
import json
import base64
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches
import io

DATA_FILE = "questions.json"

# ────────────────── Safe JSON handling ──────────────────
def load_questions():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []

def save_questions(questions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)

# ────────────────── Streamlit App ──────────────────
st.set_page_config(page_title="My Question Bank", layout="wide")
st.title("Question Bank → Now with Edit & Delete")

# Force reload data button (useful if you edited JSON on GitHub)
if st.sidebar.button("🔄 Force Reload from GitHub"):
    st.experimental_rerun()

menu = st.sidebar.selectbox("Menu", ["Add New Question", "View / Edit / Delete", "Export to Word"])

questions = load_questions()

# ────────────────── 1. Add New Question ──────────────────
if menu == "Add New Question":
    st.header("Add New Question")
    question_text = st.text_area("Question Text", height=150)
    uploaded_image = st.file_uploader("Upload Diagram (optional)", type=["png", "jpg", "jpeg", "gif"])
    subject = st.text_input("Subject")
    topic = st.text_input("Topic")

    if st.button("Save Question"):
        if question_text.strip():
            image_b64 = None
            if uploaded_image:
                image_b64 = base64.b64encode(uploaded_image.read()).decode()

            new_q = {
                "id": len(questions) + 1 if questions else 1,
                "text": question_text,
                "image_b64": image_b64,
                "subject": subject,
                "topic": topic,
                "created_at": datetime.now().isoformat()
            }
            questions.append(new_q)
            save_questions(questions)
            st.success(f"Question {new_q['id']} saved!")
            st.experimental_rerun()          # ← Auto-refresh!
        else:
            st.error("Question text cannot be empty")

# ────────────────── 2. View / Edit / Delete ──────────────────
elif menu == "View / Edit / Delete":
    st.header("Edit or Delete Questions")
    if not questions:
        st.info("No questions yet. Go add some!")
    else:
        for i, q in enumerate(questions[:]):  # copy to avoid modification issues
            with st.expander(f"Q{q['id']} • {q['subject']} • {q['topic']} • Click to edit/delete"):
                col1, col2 = st.columns([4, 1])
                with col1:
                    new_text = st.text_area("Question", q["text"], height=120, key=f"text_{q['id']}")
                    new_subject = st.text_input("Subject", q["subject"], key=f"sub_{q['id']}")
                    new_topic = st.text_input("Topic", q["topic"], key=f"top_{q['id']}")
                    
                    # Image preview + replace option
                    if q["image_b64"]:
                        st.image(base64.b64decode(q["image_b64"]), width=400)
                    new_image = st.file_uploader("Replace image (optional)", type=["png","jpg","jpeg","gif"], key=f"img_{q['id']}")

                with col2:
                    if st.button("Update", key=f"upd_{q['id']}"):
                        new_b64 = None
                        if new_image:
                            new_b64 = base64.b64encode(new_image.read()).decode()
                        elif q["image_b64"] and not new_image:
                            new_b64 = q["image_b64"]   # keep old image

                        questions[i] = {
                            "id": q["id"],
                            "text": new_text,
                            "image_b64": new_b64,
                            "subject": new_subject,
                            "topic": new_topic,
                            "created_at": q["created_at"]
                        }
                        save_questions(questions)
                        st.success("Updated!")
                        st.experimental_rerun()

                    if st.button("Delete", type="primary", key=f"del_{q['id']}"):
                        if st.session_state.get(f"confirm_{q['id']}", False):
                            questions.pop(i)
                            save_questions(questions)
                            st.success("Deleted!")
                            st.experimental_rerun()
                        else:
                            st.session_state[f"confirm_{q['id']}"] = True
                            st.warning("Click Delete again to confirm")

# ────────────────── 3. Export to Word ──────────────────
elif menu == "Export to Word":
    st.header("Export Selected Questions")
    if not questions:
        st.warning("No questions to export")
    else:
        selected_ids = []
        for q in questions:
            if st.checkbox(f"Q{q['id']}: {q['subject']} – {q['topic']}", key=f"export_{q['id']}"):
                selected_ids.append(q["id"])
                st.write(q["text"])
                if q["image_b64"]:
                    st.image(base64.b64decode(q["image_b64"]), width=500)

        if st.button("Generate DOCX") and selected_ids:
            doc = Document()
            doc.add_heading("Question Paper", 0)
            for q in questions:
                if q["id"] in selected_ids:
                    doc.add_paragraph(q["text"], style="Intense Quote")
                    if q["image_b64"]:
                        img_stream = io.BytesIO(base64.b64decode(q["image_b64"]))
                        doc.add_picture(img_stream, width=Inches(5.5))
                    doc.add_page_break()

            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button(
                "Download DOCX",
                data=bio,
                file_name=f"QuestionPaper_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
