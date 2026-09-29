import pytest
from langgraph.types import Command
from backend.app.agent.graph import email_agent_graph
from backend.app.database.connection import SessionLocal
from backend.app.database.repository import EmailRepository


def test_agent_graph_interrupt_and_yes_decision():
    email_id = 3
    thread_config = {"configurable": {"thread_id": f"unit_test_email_{email_id}"}}
    
    # 1. Run until interrupt
    email_agent_graph.invoke({"email_id": email_id}, config=thread_config)
    snapshot = email_agent_graph.get_state(thread_config)
    
    assert snapshot.next == ("human_verification",)
    assert len(snapshot.tasks) > 0
    assert len(snapshot.tasks[0].interrupts) > 0
    
    interrupt_val = snapshot.tasks[0].interrupts[0].value
    assert interrupt_val["email_id"] == email_id
    assert interrupt_val["ai_category"] in ["Payroll", "Benefits", "Tax"]

    # 2. Resume with YES
    email_agent_graph.invoke(
        Command(resume={"decision": "YES", "verified_by": "test_agent_runner"}),
        config=thread_config
    )
    final_snapshot = email_agent_graph.get_state(thread_config)
    assert final_snapshot.next == ()
    assert final_snapshot.values["verification_status"] == "approved"
    assert final_snapshot.values["final_category"] == final_snapshot.values["ai_category"]
    assert final_snapshot.values["db_updated"] is True


def test_agent_graph_interrupt_and_no_decision():
    email_id = 4
    thread_config = {"configurable": {"thread_id": f"unit_test_email_{email_id}"}}
    
    # 1. Run until interrupt
    email_agent_graph.invoke({"email_id": email_id}, config=thread_config)
    snapshot = email_agent_graph.get_state(thread_config)
    assert snapshot.next == ("human_verification",)

    # 2. Resume with NO and human correction to 'Tax'
    email_agent_graph.invoke(
        Command(resume={
            "decision": "NO",
            "correct_category": "Tax",
            "feedback": "Test override",
            "verified_by": "test_supervisor"
        }),
        config=thread_config
    )
    final_snapshot = email_agent_graph.get_state(thread_config)
    assert final_snapshot.next == ()
    assert final_snapshot.values["verification_status"] == "corrected"
    assert final_snapshot.values["final_category"] == "Tax"

    # 3. Verify in NeonDB
    db = SessionLocal()
    try:
        repo = EmailRepository(db)
        saved = repo.get_email_by_id(email_id)
        assert saved.verified_category == "Tax"
        assert saved.verification_status == "corrected"
        assert saved.human_feedback == "Test override"
        # Original AI prediction must be preserved
        assert saved.ai_category is not None
    finally:
        db.close()
