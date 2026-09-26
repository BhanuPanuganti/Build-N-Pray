import json

from fastapi.testclient import TestClient

from app.main import app
from app.services import conversation, interviewer
from app.services.agent import AgentUnavailable, _rate_limit_wait, agent

client = TestClient(app)
PAYLOAD = {
    "candidate_name": "Ada",
    "role": "Backend Engineer",
    "job_description": "Build Java and Python API services and collaborate with a team.",
    "resume": "Built two Python web projects.",
    "preparation_goal": "Practice concise answers.",
    "difficulty": "medium",
}


def _session() -> str:
    return client.post("/api/sessions", json=PAYLOAD).json()["session_id"]


def _answer(session_id: str, text: str) -> dict:
    response = client.post(f"/api/sessions/{session_id}/answer", json={"answer": text})
    assert response.status_code == 200, response.text
    return response.json()


def test_round_follows_up_then_moves_on_and_rates_each_skill():
    session_id = _session()
    started = client.post(f"/api/sessions/{session_id}/section", json={"section": "project"}).json()
    assert started["question"].startswith("Hi, thanks for joining.")
    assert started["topic"] == "Skill 1" and started["history"] == []

    first = _answer(session_id, "I built a Flask API for bookings.")
    assert first["kind"] == "follow_up" and first["topic"] == "Skill 1" and not first["complete"]
    second = _answer(session_id, "We cached reads in Redis and measured p95 latency.")
    assert second["kind"] == "next_topic" and second["topic"] == "Skill 2"

    results = [first, second]
    while not results[-1]["complete"]:
        results.append(_answer(session_id, "A detailed answer with an example."))
    closing = results[-1]
    assert closing["next_question"] is None and closing["closing"] == "Thanks, that is all for this round."
    assert len(results) <= started["total_questions"]

    summary = client.get(f"/api/sessions/{session_id}").json()
    assert summary["sections"]["project"] == "completed" and summary["voice_progress"] is None
    assert summary["round_scores"]["project"] == 76

    report = client.get(f"/api/sessions/{session_id}/report").json()
    verdict = report["round_verdicts"]["project"]
    assert [s["skill"] for s in verdict["skills"]] == ["Skill 1", "Skill 2", "Skill 3"]
    assert verdict["rated_by"] == "agent"
    answers = report["section_summaries"]["project"]["answers"]
    assert answers[0]["kind"] == "opening" and answers[1]["kind"] == "follow_up"
    assert all(a["topic"] for a in answers)


def test_interviewer_picks_up_what_the_candidate_mentions():
    session_id = _session()
    client.post(f"/api/sessions/{session_id}/section", json={"section": "fundamentals"})
    probed = _answer(session_id, "Mostly I write Java services at work.")
    assert probed["kind"] == "probe_mention"
    assert probed["topic"] == "Object-oriented design"
    progress = client.get(f"/api/sessions/{session_id}").json()["voice_progress"]
    assert progress["topic"] == "Object-oriented design" and progress["question_number"] == 2


def test_refresh_resumes_mid_conversation_with_history():
    session_id = _session()
    first = client.post(f"/api/sessions/{session_id}/section", json={"section": "project"}).json()
    reply = _answer(session_id, "I built a Flask API.")
    resumed = client.post(f"/api/sessions/{session_id}/section", json={"section": "project"}).json()
    assert resumed["question"] == reply["next_question"] != first["question"]
    assert resumed["question_number"] == 2
    assert resumed["history"] == [{"question": first["question"], "answer": "I built a Flask API.", "topic": "Skill 1"}]


def test_switching_rounds_keeps_each_conversation():
    session_id = _session()
    client.post(f"/api/sessions/{session_id}/section", json={"section": "project"})
    project_next = _answer(session_id, "I built a Flask API.")["next_question"]
    client.post(f"/api/sessions/{session_id}/section", json={"section": "fundamentals"})
    back = client.post(f"/api/sessions/{session_id}/section", json={"section": "project"}).json()
    assert back["question"] == project_next and len(back["history"]) == 1


def test_round_score_falls_back_to_answers_when_rating_fails(monkeypatch):
    def unavailable(*args, **kwargs):
        raise AgentUnavailable("down")

    monkeypatch.setattr(conversation.interviewer, "rate_round", unavailable)
    session_id = _session()
    client.post(f"/api/sessions/{session_id}/section", json={"section": "project"})
    while not _answer(session_id, "An answer.")["complete"]:
        pass
    summary = client.get(f"/api/sessions/{session_id}").json()
    assert summary["round_scores"]["project"] == 80
    assert client.get(f"/api/sessions/{session_id}/report").json()["round_verdicts"]["project"]["rated_by"] == "answer_average"


def test_a_move_outside_the_budget_is_asked_again(monkeypatch):
    prompts: list[str] = []

    def chat(system, user, max_tokens, temperature):
        prompts.append(user)
        decision = "follow_up" if len(prompts) == 1 else "next_topic"
        return json.dumps({
            "assessment": {"score": 60, "signal": "partial", "strength": "", "improvement": ""},
            "topic_verdict": {"level": "developing", "note": ""},
            "decision": decision, "new_topic": "", "reply": f"Reply for {decision}?",
        })

    monkeypatch.setattr(agent, "_chat", chat)
    state = {
        "topics": [{"skill": "A", "why": "", "status": "current"}, {"skill": "B", "why": "", "status": "upcoming"}],
        "current": 0, "follow_ups": 2, "probes": 2,
        "turns": [{"topic": 0, "question": "Tell me about A?", "answer": None}],
    }
    result = interviewer.next_turn(PAYLOAD, "project", state, "An answer.", ("next_topic",), turns_left=3)
    assert result["decision"] == "next_topic" and result["reply"] == "Reply for next_topic?"
    assert "You chose follow_up, which the budget does not allow" in prompts[1]


def test_per_minute_limits_wait_but_daily_limits_fail_fast():
    assert round(_rate_limit_wait("429 Too Many Requests ... Please try again in 12.645s."), 3) == 13.145
    assert _rate_limit_wait("429 Too Many Requests ... Please try again in 1m2s.") is None
    assert _rate_limit_wait("429 Too Many Requests ... Please try again in 1h2m3.5s.") is None
    assert _rate_limit_wait("Error code: 429 - [{'error': {'details': [{'retryDelay': '22s'}]}}]") == 22.5
    assert _rate_limit_wait("404 Not Found") is None


def _state(**overrides) -> dict:
    state = {
        "topics": [{"skill": "A", "status": "current"}, {"skill": "B", "status": "upcoming"}],
        "current": 0, "follow_ups": 0, "probes": 0,
    }
    return {**state, **overrides}


def test_budget_limits_what_the_interviewer_may_do():
    assert conversation._allowed(_state(), turns_left=3) == ("follow_up", "probe_mention", "next_topic")
    assert conversation._allowed(_state(follow_ups=2, probes=2), turns_left=3) == ("next_topic",)
    assert conversation._allowed(_state(), turns_left=0) == ("wrap_up",)
    last_topic = _state(topics=[{"skill": "A", "status": "covered"}, {"skill": "B", "status": "current"}], current=1)
    assert "wrap_up" in conversation._allowed(last_topic, turns_left=2)


def test_out_of_budget_choices_are_bent_back():
    assert conversation._next_move("follow_up", ("wrap_up",), _state()) == "wrap_up"
    no_more = _state(topics=[{"skill": "A", "status": "current"}], probes=2)
    assert conversation._next_move("next_topic", ("follow_up", "wrap_up"), no_more) == "follow_up"
    assert conversation._next_move("next_topic", ("follow_up", "wrap_up"), _state(topics=[{"skill": "A", "status": "current"}])) == "probe_mention"
