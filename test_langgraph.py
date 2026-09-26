from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    val: int

def err_node(state: State):
    raise ValueError("Testing Error")

graph = StateGraph(State)
graph.add_node("err", err_node)
graph.add_edge(START, "err")
graph.add_edge("err", END)
compiled = graph.compile()

try:
    compiled.invoke({"val": 1})
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Exception Type:", type(e))
