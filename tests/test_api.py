from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
PAYLOAD = {"candidate_name": "Ada", "role": "Engineer", "job_description": "Build Python API services and collaborate with a team.", "resume": "Built two Python web projects.", "preparation_goal": "Practice concise answers.", "difficulty": "medium"}


def test_full_demo_flow():
    started = client.post("/api/sessions", json=PAYLOAD)
    assert started.status_code == 200
    session_id = started.json()["session_id"]
    answer = client.post(f"/api/sessions/{session_id}/answer", json={"answer": "I built an API and improved response time."})
    assert answer.status_code == 200
    dsa = client.post(f"/api/sessions/{session_id}/dsa/start", json={"difficulty": "easy", "duration_minutes": 5})
    assert dsa.status_code == 200
    submitted = client.post(f"/api/sessions/{session_id}/dsa/submit", json={"code": "def two_sum(): pass", "language": "python"})
    assert submitted.status_code == 200
    report = client.get(f"/api/sessions/{session_id}/report")
    assert report.status_code == 200
    assert report.json()["dsa_result"]["submitted"] is True
