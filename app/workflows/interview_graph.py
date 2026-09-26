from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from app.services.llm import llm


class InterviewState(TypedDict):
    profile: dict
    questions: list[str]


def generate_questions(state: InterviewState) -> InterviewState:
    return {"questions": llm.questions(state["profile"])}


graph = StateGraph(InterviewState)
graph.add_node("generate_questions", generate_questions)
graph.add_edge(START, "generate_questions")
graph.add_edge("generate_questions", END)
interview_graph = graph.compile()
