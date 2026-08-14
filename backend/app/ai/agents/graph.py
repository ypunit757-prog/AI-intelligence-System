"""LangGraph-based agent with hard safety limits.

Graph shape: intent -> planner -> tool_selection -> tool_execution
             -> observation -> validation -> final_answer

Safety: max_iterations, per-tool timeout (enforced in app/tools),
max tool calls, and max total execution time are all enforced here,
independent of what the LLM "decides" to do.
"""
import asyncio
import time
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph

from app.ai.llm.factory import get_llm
from app.ai.llm.interface import ChatMessage
from app.tools.registry import (
    CalculatorInput,
    DocumentSearchInput,
    TOOL_REGISTRY,
    calculator_tool,
    document_search_tool,
)

MAX_ITERATIONS = 5
MAX_TOOL_CALLS = 8
MAX_TOTAL_SECONDS = 60


class AgentState(TypedDict):
    question: str
    user_id: str
    messages: list[ChatMessage]
    iterations: int
    tool_calls: Annotated[list[dict], "accumulated tool call records"]
    final_answer: str
    start_time: float


AGENT_SYSTEM_PROMPT = """You are a tool-using assistant. You may call \
`calculator` for arithmetic or `document_search` to search the user's \
uploaded documents. Decide whether a tool is needed; if not, answer \
directly. Never claim you executed a tool you did not actually call. \
You cannot run shell commands or arbitrary code."""


async def intent_node(state: AgentState) -> AgentState:
    state["messages"] = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}, {"role": "user", "content": state["question"]}]
    return state


async def planner_node(state: AgentState) -> AgentState:
    # Simple heuristic planner: looks for obvious tool triggers. A more
    # sophisticated version would ask the LLM to emit a structured
    # tool-call decision (function calling) — left as a follow-up
    # iteration to keep this graph provider-agnostic.
    q = state["question"].lower()
    state["planned_tool"] = None
    if any(ch.isdigit() for ch in q) and any(op in q for op in ["+", "-", "*", "/", "calculate", "sum", "product"]):
        state["planned_tool"] = "calculator"
    elif "document" in q or "file" in q or "search" in q or "uploaded" in q:
        state["planned_tool"] = "document_search"
    return state


async def tool_execution_node(state: AgentState) -> AgentState:
    if len(state["tool_calls"]) >= MAX_TOOL_CALLS:
        return state
    if time.monotonic() - state["start_time"] > MAX_TOTAL_SECONDS:
        return state

    tool = state.get("planned_tool")
    start = time.monotonic()
    output: dict[str, Any] = {}
    status = "ok"
    try:
        if tool == "calculator":
            output = await asyncio.wait_for(calculator_tool(CalculatorInput(expression=state["question"])), timeout=15)
        elif tool == "document_search":
            output = await asyncio.wait_for(
                document_search_tool(DocumentSearchInput(query=state["question"]), user_id=state["user_id"]), timeout=15
            )
    except asyncio.TimeoutError:
        status = "timeout"
        output = {"error": "tool timed out"}
    except Exception as e:  # defense in depth — never let a tool crash the graph
        status = "error"
        output = {"error": str(e)}

    latency_ms = int((time.monotonic() - start) * 1000)
    if tool:
        state["tool_calls"].append({"tool": tool, "output": output, "latency_ms": latency_ms, "status": status})
        state["messages"].append({"role": "tool", "content": str(output)})
    return state


async def validation_node(state: AgentState) -> AgentState:
    state["iterations"] += 1
    return state


async def final_answer_node(state: AgentState) -> AgentState:
    llm = get_llm()
    answer = await llm.generate(state["messages"])
    state["final_answer"] = answer
    return state


def _should_continue(state: AgentState) -> str:
    if state["iterations"] >= MAX_ITERATIONS:
        return "final_answer"
    if time.monotonic() - state["start_time"] > MAX_TOTAL_SECONDS:
        return "final_answer"
    if state.get("planned_tool") and len(state["tool_calls"]) < 1:
        return "tool_execution"
    return "final_answer"


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("intent", intent_node)
    graph.add_node("planner", planner_node)
    graph.add_node("tool_execution", tool_execution_node)
    graph.add_node("validation", validation_node)
    graph.add_node("final_answer", final_answer_node)

    graph.set_entry_point("intent")
    graph.add_edge("intent", "planner")
    graph.add_conditional_edges("planner", _should_continue, {"tool_execution": "tool_execution", "final_answer": "final_answer"})
    graph.add_edge("tool_execution", "validation")
    graph.add_conditional_edges("validation", _should_continue, {"tool_execution": "tool_execution", "final_answer": "final_answer"})
    graph.add_edge("final_answer", END)

    return graph.compile()


async def run_agent(question: str, user_id: str) -> dict:
    app_graph = build_agent_graph()
    initial_state: AgentState = {
        "question": question,
        "user_id": user_id,
        "messages": [],
        "iterations": 0,
        "tool_calls": [],
        "final_answer": "",
        "start_time": time.monotonic(),
    }
    result = await app_graph.ainvoke(initial_state)
    return {"answer": result["final_answer"], "tool_calls": result["tool_calls"]}
