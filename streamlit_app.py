import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
from app.services.documents import extract_text
from app.services.llm import llm
from app.services.proctoring import add_warning, check_lighting
from app.services.session_store import store
from app.services.repository import repository

st.set_page_config(page_title="BNB Interview Coach", page_icon="🎯", layout="wide")
ROUNDS = ["Technical", "Behavioural"]
PASS_SCORE = 60


def init_state():
    for key, value in {"session": None, "backend_session_id": None, "round": 0, "question": 0, "complete": False, "answer_text": "", "user": None, "section": "dashboard", "technical_started_at": None, "sections": {"dsa": "not_started", "project": "not_started", "fundamentals": "not_started"}}.items():
        st.session_state.setdefault(key, value)


def current_round():
    return ROUNDS[st.session_state.round]


def process_warning(kind, detail):
    session = st.session_state.session
    result = add_warning(session, kind, detail)
    repository.save_session(session)
    if result["disqualified"]:
        st.session_state.complete = True
        st.error("Interview ended after three integrity warnings.")
    else:
        st.warning(f"Warning {result['warnings']} of 3: {detail}")


def begin(profile):
    response = requests.post("http://127.0.0.1:8000/api/sessions", json=profile, timeout=10)
    response.raise_for_status()
    payload = response.json()
    questions = [payload["question"]]
    session = store.create(profile, questions)
    st.session_state.backend_session_id = payload["session_id"]
    session.dsa = {"enabled": profile["dsa_enabled"], "title": "Two Sum", "prompt": "Given numbers and a target, return indices of two values whose sum equals target.", "duration_minutes": profile["dsa_duration_minutes"], "submitted": not profile["dsa_enabled"]}
    st.session_state.session = session
    st.session_state.round = 0
    st.session_state.question = 0
    st.session_state.section = "dashboard"
    st.session_state.sections = {"dsa": "not_started" if profile["dsa_enabled"] else "skipped", "project": "not_started", "fundamentals": "not_started"}
    repository.save_session(session)


def next_round():
    session = st.session_state.session
    st.session_state.round += 1
    st.session_state.question = 0
    if st.session_state.round >= len(ROUNDS):
        st.session_state.complete = True
        return
    name = current_round().lower()
    session.questions = llm.round_questions(session.profile, name)


init_state()
st.title("🎯 BNB AI Interview Coach")
st.caption("Practice demo: all proctoring signals are transparent observations, not conclusive evidence of misconduct.")

with st.sidebar:
    st.subheader("Account")
    if not st.session_state.user:
        mode = st.radio("Account action", ["Login", "Create account"], label_visibility="collapsed")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if mode == "Create account":
            name = st.text_input("Name")
            if st.button("Create account"):
                try:
                    st.session_state.user = repository.create_user(name, email, password)
                    st.rerun()
                except ValueError as exc: st.error(str(exc))
        elif st.button("Login"):
            st.session_state.user = repository.authenticate(email, password)
            if st.session_state.user: st.rerun()
            else: st.error("Invalid credentials")
    else: st.success(f"Logged in: {st.session_state.user['name']}")

if not st.session_state.user:
    st.info("Log in or create an account to begin.")
elif not st.session_state.session:
    st.subheader("Interview setup")
    col1, col2 = st.columns(2)
    with col1:
        resume = st.file_uploader("Upload résumé", type=["pdf", "docx", "txt"])
        role = st.text_input("Target role", "Software Engineer")
        goal = st.text_area("How do you want to prepare?", "Practice technical communication and DSA.")
        focus = st.text_area("Recruiter question focus", "Prioritize the role responsibilities, project architecture, and required technologies.")
    with col2:
        jd = st.file_uploader("Upload job description", type=["pdf", "docx", "txt"])
        name = st.text_input("Candidate name")
        include_dsa = st.checkbox("Include a timed DSA question in the technical interview", value=True)
        difficulty = st.selectbox("DSA difficulty", ["easy", "medium", "hard"], index=1)
        dsa_minutes = st.slider("DSA time limit (minutes)", min_value=5, max_value=90, value=20, disabled=not include_dsa)
        project_count = st.selectbox("Project technical question count", [3, 4, 5], index=0)
        fundamentals_count = st.selectbox("Fundamentals question count", [3, 4, 5], index=0)
    if st.button("Start setup check", type="primary"):
        if not resume or not jd or not name:
            st.error("Upload both documents and provide the candidate name.")
        else:
            profile = {"candidate_name": name, "user_email": st.session_state.user["email"], "role": role, "resume": extract_text(resume), "job_description": extract_text(jd), "preparation_goal": goal, "interview_focus": focus, "project_question_count": project_count, "fundamentals_question_count": fundamentals_count, "difficulty": difficulty, "dsa_enabled": include_dsa, "dsa_duration_minutes": dsa_minutes}
            if len(profile["resume"]) < 10 or len(profile["job_description"]) < 30:
                st.error("The uploaded documents did not contain enough extractable text.")
            else:
                try:
                    begin(profile)
                    st.rerun()
                except requests.RequestException:
                    st.error("Start the FastAPI backend on port 8000 before launching an assessment.")
else:
    session = st.session_state.session
    if st.session_state.section == "dashboard":
        st.header("Your interview map")
        done = sum(s in {"completed", "skipped"} for s in st.session_state.sections.values())
        st.progress(done / 3, text=f"{done} of 3 sections finished")
        cards = [("dsa", "1. DSA", "Timed coding challenge with difficulty, time-limit, and hint settings."), ("project", "2. Project technical", "Questions grounded in projects from your resume."), ("fundamentals", "3. Technical fundamentals", "Core concepts required for the target role.")]
        cols = st.columns(3)
        for col, (key, title, description) in zip(cols, cards):
            with col:
                st.subheader(title); st.write(description); status = st.session_state.sections[key]; st.caption(f"Status: {status.replace('_', ' ').title()}")
                if status not in {"completed", "skipped"} and st.button("Start" if status == "not_started" else "Resume", key=f"start_{key}"):
                    st.session_state.sections[key] = "in_progress"
                    st.link_button("Open secure live assessment", f"http://127.0.0.1:8000/assessment.html?session_id={st.session_state.backend_session_id}&section={key}")
                if status == "not_started" and st.button("Skip", key=f"skip_{key}"):
                    st.session_state.sections[key] = "skipped"; repository.save_session(session); st.rerun()
        st.stop()
    st.progress(st.session_state.round / len(ROUNDS), text=f"Round {st.session_state.round + 1} of {len(ROUNDS)}: {current_round()}")
    left, right = st.columns([2, 1])
    with right:
        st.subheader("Camera and mic")
        photo = st.camera_input("Camera permission / lighting check")
        if photo:
            check = check_lighting(photo)
            st.info(f"Lighting: {check.lighting}")
            if check.warning:
                st.warning("Improve lighting before continuing.")
        audio = st.audio_input("Record an answer")
        if audio and st.button("Transcribe recording"):
            st.session_state.answer_text = llm.transcribe_audio(audio.getvalue())
        st.subheader("Assessment monitoring")
        st.caption("Camera and browser integrity checks run automatically during the assessment. Candidates cannot edit or submit monitoring events.")
    with left:
        if st.session_state.section in {"project", "fundamentals"} and st.session_state.technical_started_at:
            elapsed = datetime.now(timezone.utc) - st.session_state.technical_started_at
            remaining = max(timedelta(), timedelta(minutes=30) - elapsed)
            st.info(f"Voice interview time remaining: {str(remaining).split('.')[0]}")
            if remaining == timedelta():
                st.session_state.sections[st.session_state.section] = "completed"
                st.session_state.section = "dashboard"
                st.warning("The 30-minute interview limit has ended.")
                st.rerun()
        if st.session_state.complete:
            report = llm.final_feedback(session)
            if session.disqualified:
                st.error("Result: disqualified after three integrity warnings.")
            else:
                st.success("Interview complete")
            st.json(report)
        elif st.session_state.section == "dsa" and not session.dsa["submitted"]:
            st.subheader("Technical interview - DSA question")
            st.caption(f"This is the first question in your technical interview. Time limit: {session.dsa['duration_minutes']} minutes.")
            st.write(session.dsa["prompt"])
            code = st.text_area("Write Python code", height=260, placeholder="def two_sum(numbers, target):\n    ...")
            if st.button("Submit DSA solution", type="primary"):
                score = 75 if len(code.strip()) >= 30 else 40
                session.dsa.update({"submitted": True, "code_length": len(code), "score": score})
                session.round_scores["DSA"] = score
                if score < PASS_SCORE:
                    st.session_state.complete = True
                    st.error("The technical-interview DSA question did not meet the qualification threshold.")
                else:
                    st.session_state.sections["dsa"] = "completed"; st.session_state.section = "dashboard"
                st.rerun()
        else:
            question = session.questions[st.session_state.question]
            st.subheader(f"{st.session_state.section.title()} question {st.session_state.question + 1} of {len(session.questions)}")
            st.write(question)
            st.caption("Voice only: record your answer. Typing is disabled for technical sections.")
            if not audio:
                st.warning("Record an answer using the microphone to continue.")
            text = st.session_state.answer_text
            if audio and st.button("Transcribe and submit voice answer", type="primary"):
                text = llm.transcribe_audio(audio.getvalue())
                if text.startswith("Demo mode"):
                    st.error("Speech-to-text requires DEMO_MODE=false and a valid Hugging Face token.")
                    st.stop()
                feedback = llm.critique(question, text, session.profile)
                session.answers.append({"section": st.session_state.section, "question": question, "answer": text, "feedback": feedback, "submitted_at": store.now()})
                st.session_state.answer_text = ""
                st.info(f"Score: {feedback['score']}. {feedback['improvement']}")
                st.session_state.question += 1
                if st.session_state.question >= len(session.questions):
                    scores = [a["feedback"]["score"] for a in session.answers if a.get("section") == st.session_state.section]
                    score = round(sum(scores) / len(scores))
                    session.round_scores[st.session_state.section] = score
                    st.session_state.sections[st.session_state.section] = "completed"
                    st.session_state.section = "dashboard"
                st.rerun()
