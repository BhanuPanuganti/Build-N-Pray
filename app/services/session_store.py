from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

SECTIONS = ("dsa", "project", "fundamentals")


def _default_sections() -> dict[str, str]:
    return {name: "not_started" for name in SECTIONS}


@dataclass
class Session:
    id: str
    profile: dict
    questions: list[str]
    current_question: int = 0
    answers: list[dict] = field(default_factory=list)
    proctor_events: list[dict] = field(default_factory=list)
    dsa: dict | None = None
    warnings: int = 0
    disqualified: bool = False
    vision_latches: dict[str, bool] = field(default_factory=dict)
    round_index: int = 0
    round_scores: dict = field(default_factory=dict)
    sections: dict[str, str] = field(default_factory=_default_sections)
    active_section: str | None = None
    conversation: dict[str, dict] = field(default_factory=dict)
    report_cache: dict | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    def create(self, profile: dict, questions: list[str]) -> Session:
        session = Session(str(uuid4()), profile, questions)
        if not profile.get("dsa_enabled", True):
            session.sections["dsa"] = "skipped"
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()


store = SessionStore()
