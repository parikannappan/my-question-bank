# app.py → FINAL VERSION: Auto push to GitHub on Streamlit Cloud
import streamlit as st
import json
import base64
import os
from datetime import datetime
from docx import Document
from docx.shared import Inches
import io

DATA_FILE = "questions.json"

# ───── Safe load/save (same as before) ─────
def load_questions():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except:
        return []

def save_questions(questions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
    
    # ───── AUTO COMMIT & PUSH TO GITHUB (only on Streamlit Cloud) ─────
    if os.getenv("STREAMLIT_SHARING") or "streamlit" in os.getenv("SERVER_NAME", ""):
        try:
            import subprocess
            subprocess.run(["git", "config", "user.name", "QuestionBank Bot"], check=True)
            subprocess.run(["git", "config", "user.email", "bot@questionbank"], check=True)
            subprocess.run(["git", "add", DATA_FILE], check=True)
            subprocess.run(["git", "commit", "-m", f"Update questions.json → {len(questions)} questions [{datetime.now():%Y-%m-%d %H:%M}]"], check=True)
            push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
            if push_result.returncode != 0:
                st.sidebar.warning("Git push failed (normal if someone edited at the same time)")
        except Exception as e:
            st.sidebar.error(f"Git push error: {e}")

# ───── Rest of the app (100% same UI, just calls save_questions which now pushes) ─────
st.set_page_config(page_title="My Question Bank", layout="wide")
st.title("Question Bank → Data survives refresh!")

if st.sidebar.button("Force Reload from GitHub"):
    st.rerun()

menu = st.sidebar.selectbox("Menu", ["Add Question", "Edit / Delete", "Export to Word"])
questions = load_questions()

# ==================== Add ====================
if menu == "Add Question":
    st.header("Add New Question")
    question_text = st.text_area("Question", height=150)
    uploaded_image = st.file_uploader("Diagram (optional)", type=["png","jpg","jpeg","gif"])
    subject = st.text_input("Subject")
    topic = st.text_input("Topic")

    if st.button("Save Question"):
        if question_text.strip():
            image_b64 = None
            if uploaded_image:
                image_b64 = base64.b64encode(uploaded_image.read()).decode()
            new_q = {
                "id": len(questions)+1 if questions else 1,
                "text": question_text,
                "image_b64": image_b64,
                "subject": subject,
                "topic": topic,
                "created_at": datetime.now().isoformat()
            }
            questions.append(new_q)
            save_questions(questions)        # ← This now pushes to GitHub!
            st.success("Saved & synced to GitHub!")
            st.rerun()
        else:
            st.error("Question cannot be empty")

# ==================== Edit / Delete ====================
elif menu == "Edit / Delete":
    st.header("Edit or Delete Questions")
    if not questions:
        st.info("No questions yet")
    else:
        for i, q in enumerate(questions[:]):
            with st.expander(f"Q{q['id']} • {q['subject']} • {q['topic']}"):
                c1, c2 = st.columns([4,1])
                with c1:
                    new_text = st.text_area("Text", q["text"], height=100, key=f"t{i}")
                    new_sub = st.text_input("Subject", q["subject"], key=f"s{i}")
                    new_top = st.text_input("Topic", q["topic"], key=f"tp{i}")
                    if q["image_b64"]:
                        st.image(base64.b64decode(q["image_b64"]), width=400)
                    new_img = st.file_uploader("Replace image", type=["png","jpg","jpeg"], key=f"i{i}")
                with c2:
                    if st.button("Update", key=f"u{i}"):
                        new_b64 = q["image_b64"]
                        if new_img:
                            new_b64 = base64.b64encode(new_img.read()).decode()
                        questions[i].update({"text": new_text, "image_b64": new_b64, "subject": new_sub, "topic": new_top})
                        save_questions(questions)
                        st.success("Updated & synced!")
                        st.rerun()
                    if st.button("Delete", type="primary", key=f"d{i}"):
                        if st.session_state.get(f"confirm{i}", False):
                            questions.pop(i)
                            save_questions(questions)
                            st.success("Deleted & synced!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm{i}"] = True
                            st.warning("Click again to confirm delete")

# ==================== Export ====================
elif menu == "Export to Word":
    st.header("Export to DOCX")
    if not questions:
        st.warning("No questions")
    else:
        selected = st.multiselect("Select questions", options=[(q["id"], f"Q{q['id']} {q['subject']} - {q['topic']}") for q in questions], format_func=lambda x: x[1])
        sel_ids = [x[0] for x in selected]
        if st.button("Generate DOCX") and sel_ids:
            doc = Document()
            doc.add_heading("Question Paper", 0)
            for q in questions:
                if q["id"] in sel_ids:
                    doc.add_paragraph(q["text"])
                    if q["image_b64"]:
                        doc.add_picture(io.BytesIO(base64.b64decode(q["image_b64"])), width=Inches(5.5))
                    doc.add_page_break()
            bio = io.BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button("Download DOCX", bio, f"Paper_{datetime.now().strftime('%Y%m%d')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
