"""MongoDB persistence with an in-memory fallback for local demos."""
import hashlib
import os
from datetime import datetime, timezone
from app.core.config import settings


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${value.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return password_hash(password, bytes.fromhex(salt)) == stored


class Repository:
    def __init__(self):
        self.memory_users: dict[str, dict] = {}
        self.memory_sessions: dict[str, dict] = {}
        self.db = None
        self.connection_error: str | None = None
        if settings.mongodb_uri:
            try:
                from pymongo import MongoClient
                database_name = settings.mongodb_database.strip().replace(" ", "_")
                self.db = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)[database_name]
            except Exception as exc:
                # Keep the demo/test application usable when Atlas DNS or credentials are unavailable.
                self.connection_error = str(exc)
                self.db = None

    def create_user(self, name: str, email: str, password: str) -> dict:
        user = {"name": name, "email": email.lower(), "password_hash": password_hash(password), "created_at": datetime.now(timezone.utc).isoformat()}
        if self.db is not None:
            if self.db.users.find_one({"email": user["email"]}):
                raise ValueError("Email already exists")
            self.db.users.insert_one(user)
        else:
            if user["email"] in self.memory_users: raise ValueError("Email already exists")
            self.memory_users[user["email"]] = user
        return {"name": user["name"], "email": user["email"]}

    def authenticate(self, email: str, password: str) -> dict | None:
        email = email.lower()
        user = self.db.users.find_one({"email": email}) if self.db is not None else self.memory_users.get(email)
        if user and verify_password(password, user["password_hash"]):
            return {"name": user["name"], "email": user["email"]}
        return None

    def save_session(self, session) -> None:
        data = {"id": session.id, "profile": session.profile, "answers": session.answers, "proctor_events": session.proctor_events, "warnings": session.warnings, "disqualified": session.disqualified, "round_scores": session.round_scores, "dsa": session.dsa}
        if self.db is not None: self.db.sessions.update_one({"id": session.id}, {"$set": data}, upsert=True)
        else: self.memory_sessions[session.id] = data


repository = Repository()
