import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.problems.dynamic import clear_authored
from app.services.repository import repository

client = TestClient(app)

POSTING = {
    "role": "Backend Engineer",
    "job_description": "Build Python API services, design data models, and review code with the team.",
    "interview_focus": "Prioritize API design, data structures, and how the candidate talks about their projects.",
    "difficulty": "medium",
    "dsa_enabled": True,
    "dsa_duration_minutes": 20,
    "project_question_count": 3,
    "fundamentals_question_count": 3,
}

SOLUTION = "import sys\na, b = map(int, sys.stdin.read().split())\nprint(a + b)\n"


@pytest.fixture
def memory_db(monkeypatch):
    monkeypatch.setattr(repository, "db", None)
    monkeypatch.setattr(settings, "admin_access_code", "test-admin-code")
    repository.memory_users.clear()
    repository.memory_sessions.clear()
    repository.memory_interviews.clear()
    clear_authored()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register(role: str, code: str = "") -> dict:
    suffix = uuid.uuid4().hex[:8]
    response = client.post("/api/auth/register", json={
        "name": "Ada Admin" if role == "admin" else "Grace Hopper",
        "email": f"{role}-{suffix}@example.com",
        "password": "password1",
        "role": role,
        "admin_access_code": code,
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_interviewer_signup_requires_the_access_code(memory_db):
    denied = client.post("/api/auth/register", json={
        "name": "No Code", "email": "nocode@example.com", "password": "password1", "role": "admin", "admin_access_code": "wrong",
    })
    assert denied.status_code == 403
    candidate = _register("candidate")
    assert candidate["role"] == "candidate" and candidate["token"]


def test_admin_link_uses_an_authored_problem_and_lists_scores(memory_db):
    admin = _register("admin", "test-admin-code")
    created = client.post("/api/admin/interviews", json=POSTING, headers=_auth(admin["token"]))
    assert created.status_code == 200, created.text
    posting = created.json()
    assert posting["coding_problem"]["slug"].startswith("authored-")
    assert posting["coding_problem"]["title"] == "Pair Sum"
    assert "100 200" not in created.text
    assert "reference_python" not in created.text

    blocked = client.get("/api/admin/interviews", headers=_auth(_register("candidate")["token"]))
    assert blocked.status_code == 403
    assert client.post(f"/api/interviews/{posting['token']}/sessions", json={"resume": "Built APIs.", "preparation_goal": "Practice clear answers."}).status_code == 401

    student = _register("candidate")
    public = client.get(f"/api/interviews/{posting['token']}")
    assert public.status_code == 200
    assert public.json()["role"] == "Backend Engineer"
    assert "coding_problem" not in public.json()

    clear_authored()
    joined = client.post(
        f"/api/interviews/{posting['token']}/sessions",
        json={"resume": "Built two Python web APIs and wrote tests for them.", "preparation_goal": "Explain trade-offs clearly."},
        headers=_auth(student["token"]),
    )
    assert joined.status_code == 200, joined.text
    session_id = joined.json()["session_id"]

    clear_authored()
    dsa = client.post(f"/api/sessions/{session_id}/dsa/start", json={})
    assert dsa.status_code == 200, dsa.text
    body = dsa.json()
    assert body["problem"]["slug"].startswith("authored-")
    assert body["title"] == "Pair Sum"
    assert "100 200" not in dsa.text
    ran = client.post(f"/api/problems/{body['problem_slug']}/run", json={"language": "python", "code": SOLUTION})
    assert ran.status_code == 200 and ran.json()["all_passed"] is True

    submitted = client.post(f"/api/sessions/{session_id}/dsa/submit", json={"language": "python", "code": SOLUTION})
    assert submitted.status_code == 200 and submitted.json()["all_passed"] is True

    section = client.post(f"/api/sessions/{session_id}/section", json={"section": "fundamentals"})
    assert section.status_code == 200, section.text
    finished = False
    for _ in range(12):
        result = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "A process has its own memory; threads share it."})
        assert result.status_code == 200, result.text
        if result.json()["complete"]:
            finished = True
            break
    assert finished
    fundamentals = client.get(f"/api/sessions/{session_id}").json()["round_scores"]["fundamentals"]

    board = client.get(f"/api/admin/interviews/{posting['id']}/attempts", headers=_auth(admin["token"]))
    assert board.status_code == 200, board.text
    row = board.json()[0]
    assert row["name"] == "Grace Hopper"
    assert row["email"] == student["email"]
    assert row["scores"]["dsa"] == submitted.json()["evaluation"]["score"]
    assert row["scores"]["fundamentals"] == fundamentals == 76
    assert row["overall_score"] == round((row["scores"]["dsa"] + fundamentals) / 2)
    assert row["rank"] == 1
    stranger = _register("admin", "test-admin-code")
    assert client.get(f"/api/admin/interviews/{posting['id']}/attempts", headers=_auth(stranger["token"])).status_code == 404
