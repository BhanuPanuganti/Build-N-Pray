from app.core.config import settings


class InterviewLLM:
    def __init__(self) -> None:
        self._model = None

    def _chat(self, prompt: str) -> str:
        if settings.demo_mode:
            return ""
        if not settings.huggingface_api_key:
            raise RuntimeError("HF_TOKEN is required when DEMO_MODE=false")
        if self._model is None:
            from langchain_huggingface import HuggingFaceEndpoint
            self._model = HuggingFaceEndpoint(repo_id=settings.hf_chat_model, huggingfacehub_api_token=settings.huggingface_api_key, max_new_tokens=700, temperature=0.3)
        return self._model.invoke(prompt)

    def questions(self, profile: dict) -> list[str]:
        if settings.demo_mode:
            return [f"Tell me about a project that demonstrates your fit for the {profile['role']} role.", "Describe a difficult technical problem you solved. What was your approach and result?", "How would you collaborate when you disagree with a teammate about a technical decision?"]
        prompt = f"Generate exactly three concise interview questions. Role: {profile['role']}\nJob: {profile['job_description']}\nResume: {profile['resume']}\nGoal: {profile['preparation_goal']}\nOne question per line, no numbering."
        return [line.strip("- 1234567890. ") for line in self._chat(prompt).splitlines() if line.strip()][:3]

    def round_questions(self, profile: dict, round_name: str) -> list[str]:
        if settings.demo_mode:
            library = {
                "technical": [f"Which two requirements in this {profile['role']} job description would you prioritize first, and why?", "Explain a technical choice from your résumé and its trade-offs.", "How would you test and monitor a solution for this role?"],
                "behavioural": ["Tell me about a time you handled a difficult collaboration problem.", "Describe a time you received critical feedback and what you changed.", "How do you communicate risk or a delay to stakeholders?"],
            }
            return library[round_name]
        prompt = f"Create exactly three {round_name} interview questions for the role {profile['role']}. Use this job description: {profile['job_description']}. Use this resume: {profile['resume']}. Return one question per line, no numbering."
        return [line.strip("- 1234567890. ") for line in self._chat(prompt).splitlines() if line.strip()][:3]

    def technical_questions(self, profile: dict, count: int = 3) -> list[str]:
        """Create questions grounded in responsibilities and requirements, not a generic role."""
        if settings.demo_mode:
            return [
                "Please introduce yourself and summarize the technical projects in your resume.",
                "Choose your strongest project from the resume. Explain its architecture, technology stack, your contribution, and the technical trade-offs you made.",
                "Explain a difficult technical problem in one of your resume projects. How did you debug it, test the solution, and measure the result?",
            ][:count]
        prompt = ("You are the technical-interview agent. Generate exactly " + str(count) +
                  " technical interview questions strictly grounded in the candidate resume. Start with a concise self-introduction, then ask about project architecture, technology choices, individual contribution, debugging, testing and trade-offs. "
                  "Do not ask about protected characteristics. One concise question per line, no numbering.\n"
                  f"Role: {profile['role']}\nResume: {profile['resume']}\nRecruiter focus: {profile.get('interview_focus', 'general technical assessment')}")
        return [line.strip("- 1234567890. ") for line in self._chat(prompt).splitlines() if line.strip()][:count]

    def fundamental_questions(self, profile: dict) -> list[str]:
        if settings.demo_mode:
            return ["Explain the difference between a process and a thread.", "How does an HTTP request travel from a browser to a backend API?", "What makes a database index useful, and what trade-off does it create?"]
        prompt = f"Create exactly three technical-fundamentals questions for a {profile['role']} role. Cover core computing concepts relevant to this job description: {profile['job_description']}. One question per line, no numbering."
        return [line.strip("- 1234567890. ") for line in self._chat(prompt).splitlines() if line.strip()][:3]

    def transcribe_audio(self, audio_bytes: bytes) -> str:
        if settings.demo_mode:
            return "Demo mode cannot transcribe audio. Type the answer below to continue."
        if not settings.huggingface_api_key:
            raise RuntimeError("HUGGINGFACE_API_KEY is required for speech transcription")
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=settings.huggingface_api_key)
        result = client.automatic_speech_recognition(audio_bytes, model="openai/whisper-large-v3-turbo")
        return result["text"] if isinstance(result, dict) else str(result)

    def critique(self, question: str, answer: str, profile: dict) -> dict:
        if settings.demo_mode:
            role_terms = [word for word in profile.get("job_description", "").lower().split() if len(word) > 6]
            matched = sum(term.strip(".,:;()") in answer.lower() for term in role_terms[:20])
            score = min(90, 62 + min(matched, 4) * 6 + (6 if len(answer.split()) >= 25 else 0))
            return {"strength": "You gave a direct answer tied to the question.", "improvement": "Add a concrete technical decision, its trade-off, and a measurable result.", "score": score, "role_relevance": "High" if matched >= 2 else "Needs stronger links to the job requirements."}
        prompt = f"You are a fair technical-interview judge. Evaluate only answer content and communication; never identity, appearance, accent, emotion, or a hiring decision. Compare the answer against the responsibilities and requirements below.\nRole: {profile['role']}\nJob description: {profile['job_description']}\nResume: {profile['resume']}\nQuestion: {question}\nAnswer: {answer}\nReturn four lines: SCORE: integer 0-100; STRENGTH: sentence; IMPROVEMENT: sentence; ROLE_RELEVANCE: sentence."
        text = self._chat(prompt)
        result = {"score": 70, "strength": "Answer recorded.", "improvement": "Add specific evidence."}
        for line in text.splitlines():
            if line.startswith("SCORE:"):
                result["score"] = int("".join(c for c in line if c.isdigit()) or "70")
            elif line.startswith("STRENGTH:"):
                result["strength"] = line.split(":", 1)[1].strip()
            elif line.startswith("IMPROVEMENT:"):
                result["improvement"] = line.split(":", 1)[1].strip()
            elif line.startswith("ROLE_RELEVANCE:"):
                result["role_relevance"] = line.split(":", 1)[1].strip()
        return result

    def final_feedback(self, session) -> dict:
        average = round(sum(item["feedback"]["score"] for item in session.answers) / max(len(session.answers), 1))
        by_section = {}
        for answer in session.answers:
            section = answer.get("section", answer.get("round", "technical"))
            by_section.setdefault(section, []).append(answer)
        section_summaries = {section: {"answer_count": len(items), "average_score": round(sum(i["feedback"]["score"] for i in items) / len(items)), "answers": items} for section, items in by_section.items()}
        communication = {"clarity": "Review transcript structure and concise technical explanation.", "answer_structure": "Use introduction, context, action, result, and a clear technical trade-off.", "evidence": "Scores incorporate relevance, detail, and measurable outcomes from each recorded answer."}
        return {"overall_score": average, "summary": f"Completed {len(session.answers)} interview answers for the {session.profile['role']} role.", "section_summaries": section_summaries, "communication_assessment": communication, "next_steps": ["Practice a 60-second project introduction.", "Explain architecture and trade-offs using a clear structure.", "Rehearse concise, two-minute answers."], "integrity_observations": session.proctor_events, "warnings": session.warnings, "disqualified": session.disqualified, "round_scores": session.round_scores, "dsa_result": session.dsa}


llm = InterviewLLM()
