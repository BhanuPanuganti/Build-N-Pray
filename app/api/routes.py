from datetime import timedelta
from fastapi import APIRouter, HTTPException, UploadFile
from app.core.config import settings
from app.domain.schemas import AnswerRequest, DSAAnswerRequest, DSAStartRequest, ProctorEventRequest, StartSessionRequest, RegisterRequest, LoginRequest, VisionObservationRequest, SectionStartRequest
from app.services.repository import repository
from app.services.llm import llm
from app.services.proctoring import record_observation
from app.services.session_store import store
from app.workflows.interview_graph import interview_graph

router = APIRouter(prefix="/api")

@router.post("/auth/register")
def register(request: RegisterRequest):
    try: return repository.create_user(request.name, request.email, request.password)
    except ValueError as exc: raise HTTPException(409, str(exc))

@router.post("/auth/login")
def login(request: LoginRequest):
    user = repository.authenticate(request.email, request.password)
    if not user: raise HTTPException(401, "Invalid email or password")
    return user


def session_or_404(session_id: str):
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.post("/sessions")
def start_session(request: StartSessionRequest):
    profile = request.model_dump()
    questions = interview_graph.invoke({"profile": profile, "questions": []})["questions"]
    if not questions:
        raise HTTPException(502, "Model did not return interview questions")
    session = store.create(profile, questions)
    repository.save_session(session)
    return {"session_id": session.id, "question": questions[0], "question_number": 1, "total_questions": len(questions)}


@router.post("/sessions/{session_id}/answer")
def submit_answer(session_id: str, request: AnswerRequest):
    session = session_or_404(session_id)
    if session.disqualified:
        raise HTTPException(403, "Session has been disqualified after the warning limit was reached")
    if session.current_question >= len(session.questions):
        raise HTTPException(409, "Interview is already complete")
    question = session.questions[session.current_question]
    feedback = llm.critique(question, request.answer, session.profile)
    session.answers.append({"question": question, "answer": request.answer, "feedback": feedback})
    repository.save_session(session)
    session.current_question += 1
    next_question = session.questions[session.current_question] if session.current_question < len(session.questions) else None
    return {"feedback": feedback, "next_question": next_question, "complete": next_question is None}


@router.post("/sessions/{session_id}/section")
def start_section(session_id: str, request: SectionStartRequest):
    session = session_or_404(session_id)
    if request.section == "project":
        session.questions = llm.technical_questions(session.profile, session.profile.get("project_question_count", 3))
    elif request.section == "fundamentals":
        session.questions = llm.fundamental_questions(session.profile)
    else:
        return start_dsa(session_id, DSAStartRequest(difficulty=session.profile.get("difficulty", "medium"), duration_minutes=session.profile.get("dsa_duration_minutes", 20)))
    session.current_question = 0
    repository.save_session(session)
    return {"section": request.section, "question": session.questions[0], "question_number": 1, "total_questions": len(session.questions)}


@router.post("/sessions/{session_id}/transcribe")
async def transcribe_answer(session_id: str, audio: UploadFile):
    session_or_404(session_id)
    text = llm.transcribe_audio(await audio.read())
    return {"transcript": text}


@router.post("/sessions/{session_id}/dsa/start")
def start_dsa(session_id: str, request: DSAStartRequest):
    session = session_or_404(session_id)
    if session.disqualified:
        raise HTTPException(403, "Session has been disqualified after the warning limit was reached")
    problems = {"easy": ("Two Sum", "Return indices of two numbers that add to target."), "medium": ("Longest Substring Without Repeating Characters", "Return the length of the longest substring without repeated characters."), "hard": ("Merge K Sorted Lists", "Merge k sorted linked lists into one sorted list.")}
    title, prompt = problems[request.difficulty]
    session.dsa = {"title": title, "prompt": prompt, "started_at": store.now(), "duration_minutes": request.duration_minutes, "submitted": False}
    return {**session.dsa, "ends_in_seconds": int(timedelta(minutes=request.duration_minutes).total_seconds())}


@router.post("/sessions/{session_id}/dsa/submit")
def submit_dsa(session_id: str, request: DSAAnswerRequest):
    session = session_or_404(session_id)
    if session.disqualified:
        raise HTTPException(403, "Session has been disqualified after the warning limit was reached")
    if not session.dsa:
        raise HTTPException(409, "Start a DSA assessment first")
    session.dsa.update({"submitted": True, "language": request.language, "code_length": len(request.code), "status": "Received for sandboxed evaluation"})
    repository.save_session(session)
    return session.dsa


@router.post("/sessions/{session_id}/proctor-events")
def record_proctor_event(session_id: str, request: ProctorEventRequest):
    session = session_or_404(session_id)
    outcome = record_observation(session, request.event_type.value, request.details)
    outcome["event"]["observed_at"] = store.now()
    repository.save_session(session)
    return {"recorded": True, **outcome}


@router.post("/sessions/{session_id}/vision-observations")
def record_vision_observation(session_id: str, request: VisionObservationRequest):
    """Persist transparent signals; no signal is proof of malpractice."""
    session = session_or_404(session_id)
    outcomes = []
    if request.face_visible is False:
        outcomes.append(record_observation(session, "face_missing", "Face was not detected by the camera."))
    if request.people_count is not None and request.people_count > 1:
        outcomes.append(record_observation(session, "multiple_people", f"Camera detected {request.people_count} people."))
    if request.lighting in {"too_dark", "too_bright"}:
        outcomes.append(record_observation(session, "low_light", f"Lighting observation: {request.lighting}."))
    if request.gaze_away_seconds is not None and request.gaze_away_seconds >= settings.proctor_face_absence_seconds:
        outcomes.append(record_observation(session, "suspicious_gaze", f"Off-screen gaze observed for {request.gaze_away_seconds:.1f} seconds."))
    if request.mouth_motion_seconds is not None:
        session.proctor_events.append({"type": "mouth_motion", "details": f"Mouth motion observed for {request.mouth_motion_seconds:.1f} seconds; requires human review.", "observed_at": store.now(), "source": request.source})
    if not outcomes:
        session.proctor_events.append({"type": "vision_check", "details": "No warning-level observation.", "observed_at": store.now(), "source": request.source})
    for item in outcomes:
        item["event"]["observed_at"] = store.now()
        item["event"]["source"] = request.source
    repository.save_session(session)
    return {"recorded": True, "warnings": session.warnings, "warning_limit": settings.proctor_warning_limit, "disqualified": session.disqualified, "observations": outcomes}


@router.get("/sessions/{session_id}/report")
def report(session_id: str):
    return llm.final_feedback(session_or_404(session_id))
