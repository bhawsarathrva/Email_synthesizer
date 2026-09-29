import logging
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.app.agent.state import EmailClassificationState
from backend.app.agent.nodes import (
    fetch_email_node,
    classify_email_node,
    prepare_verification_node,
    human_verification_node,
    human_correction_node,
    determine_final_category_node,
    update_database_node,
)

logger = logging.getLogger("email_agent.graph")


def route_after_human_verification(
    state: EmailClassificationState,
) -> Literal["human_correction", "determine_final_category"]:
    """Conditional edge routing based on human decision (YES vs NO)."""
    decision = (state.get("human_decision") or "YES").upper()
    if decision == "NO":
        return "human_correction"
    return "determine_final_category"


def build_email_classification_graph():
    """Builds and compiles the Email Classification LangGraph workflow."""
    workflow = StateGraph(EmailClassificationState)

    # 1. Add Nodes
    workflow.add_node("fetch_email", fetch_email_node)
    workflow.add_node("classify_email", classify_email_node)
    workflow.add_node("prepare_verification", prepare_verification_node)
    workflow.add_node("human_verification", human_verification_node)
    workflow.add_node("human_correction", human_correction_node)
    workflow.add_node("determine_final_category", determine_final_category_node)
    workflow.add_node("update_database", update_database_node)

    # 2. Add Edges
    workflow.add_edge(START, "fetch_email")
    workflow.add_edge("fetch_email", "classify_email")
    workflow.add_edge("classify_email", "prepare_verification")
    workflow.add_edge("prepare_verification", "human_verification")

    # Conditional Branch from Human Verification
    workflow.add_conditional_edges(
        "human_verification",
        route_after_human_verification,
        {
            "human_correction": "human_correction",
            "determine_final_category": "determine_final_category",
        },
    )

    workflow.add_edge("human_correction", "determine_final_category")
    workflow.add_edge("determine_final_category", "update_database")
    workflow.add_edge("update_database", END)

    # Use MemorySaver checkpointer for managing paused/resumed threads
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


# Global compiled graph singleton with checkpointer
email_agent_graph = build_email_classification_graph()
