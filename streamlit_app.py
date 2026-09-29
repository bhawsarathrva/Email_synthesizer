import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from langgraph.types import Command

from backend.app.config import settings
from backend.app.database.connection import SessionLocal, test_connection
from backend.app.database.repository import EmailRepository
from backend.app.agent.graph import email_agent_graph
from backend.app.database.inspect_db import inspect_database_schema
from backend.app.database.seed import seed_database

# Page Configuration
st.set_page_config(
    page_title="AI Email Classification Agent | NeonDB & HITL",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sleek Dark Theme CSS
CUSTOM_DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #121826;
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 0 18px;
        border: none !important;
        background-color: transparent;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #f8fafc;
        background-color: rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #6366f1) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }

    /* Metric cards */
    .metric-card {
        background: #121826;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.6);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.16);
    }

    .metric-title {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-number {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.76rem;
        color: #64748b;
        margin-top: 4px;
    }

    /* Category Badges */
    .badge-payroll {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-benefits {
        background: rgba(14, 165, 233, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(14, 165, 233, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-tax {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-pending {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-approved {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-corrected {
        background: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.4);
        padding: 3px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }

    /* Email display box */
    .email-box {
        background: #121826;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .prediction-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.12));
        border: 1px solid rgba(165, 180, 252, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-top: 14px;
        margin-bottom: 20px;
    }
</style>
"""
st.markdown(CUSTOM_DARK_CSS, unsafe_allow_html=True)


# Database Helpers
def get_db_session():
    return SessionLocal()


def fetch_statistics():
    db = get_db_session()
    try:
        repo = EmailRepository(db)
        return repo.get_email_statistics()
    finally:
        db.close()


def fetch_all_emails(status_filter=None, category_filter=None, search=None):
    db = get_db_session()
    try:
        repo = EmailRepository(db)
        emails, total = repo.get_emails(page=1, limit=100, category=category_filter, status=status_filter, search_query=search)
        return emails, total
    finally:
        db.close()


def fetch_email(email_id: int):
    db = get_db_session()
    try:
        repo = EmailRepository(db)
        return repo.get_email_by_id(email_id)
    finally:
        db.close()


# Sidebar: System & Connection Status
with st.sidebar:
    st.markdown("### ⚡ System Status")
    db_res = test_connection()
    if db_res.get("status") == "connected":
        st.success(f"🟢 **NeonDB Connected**\n`{db_res.get('database')}`")
    else:
        st.error(f"🔴 **NeonDB Error**\n{db_res.get('error')}")

    st.info(f"🤖 **Active LLM**\n`{settings.LLM_PROVIDER.upper()}` : `{settings.MODEL_NAME}`")

    st.markdown("---")
    st.markdown("### 🎯 Categories Allowed")
    st.markdown("• **Payroll**: Salary, payslips, wages, bonuses")
    st.markdown("• **Benefits**: Health, 401(k), insurance, leave")
    st.markdown("• **Tax**: Form W-2, TDS, withholding, 1099")

    st.markdown("---")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()


# App Header
st.title("📨 Email Synthesizer & HITL Classification Agent")
st.caption("Production-Ready Agent with Neon PostgreSQL & LangGraph Human-in-the-Loop Verification")

# Top Metrics Row
stats = fetch_statistics()

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Emails</div>
            <div class="metric-number">{stats['total_emails']}</div>
            <div class="metric-sub">NeonDB Records</div>
        </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Payroll</div>
            <div class="metric-number" style="color: #34d399;">{stats['payroll_emails']}</div>
            <div class="metric-sub">Salary & wages</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Benefits</div>
            <div class="metric-number" style="color: #38bdf8;">{stats['benefits_emails']}</div>
            <div class="metric-sub">Health & 401(k)</div>
        </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Tax</div>
            <div class="metric-number" style="color: #c084fc;">{stats['tax_emails']}</div>
            <div class="metric-sub">W-2 & TDS</div>
        </div>
    """, unsafe_allow_html=True)
with col5:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Pending</div>
            <div class="metric-number" style="color: #fbbf24;">{stats['pending_verification']}</div>
            <div class="metric-sub">Needs human review</div>
        </div>
    """, unsafe_allow_html=True)
with col6:
    total_verified = stats['approved'] + stats['corrected']
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Verified</div>
            <div class="metric-number">{total_verified}</div>
            <div class="metric-sub">{stats['approved']} Apprv &bull; {stats['corrected']} Corr</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs
tab_hitl, tab_explorer, tab_analytics, tab_eval, tab_db = st.tabs([
    "🎯 Human-in-the-Loop Verification",
    "📋 Email Explorer",
    "📊 Analytics & Distribution",
    "📈 Model Evaluation",
    "⚙️ Database & System"
])


# ==========================================
# TAB 1: Human-in-the-Loop Verification
# ==========================================
with tab_hitl:
    st.markdown("### 🤖 Classify & Verify Emails")
    st.write("Select an email from your database, let the AI Agent classify it with LangGraph, and verify or correct the outcome.")

    filter_status = st.selectbox(
        "Filter Email List By Status:",
        ["pending", "approved", "corrected", "all"],
        index=0
    )
    actual_status = None if filter_status == "all" else filter_status

    emails_list, _ = fetch_all_emails(status_filter=actual_status)

    if not emails_list:
        st.warning(f"No emails found with status '{filter_status}'. Try changing the filter.")
    else:
        email_options = {
            e.id: f"#{e.id} | [{e.verification_status.upper()}] {e.subject} (From: {e.sender})"
            for e in emails_list
        }
        selected_id = st.selectbox(
            "Select Email to Review:",
            options=list(email_options.keys()),
            format_func=lambda x: email_options[x]
        )

        current_email = fetch_email(selected_id)

        col_left, col_right = st.columns([1.1, 0.9])

        with col_left:
            st.markdown("#### 📧 Email Content")
            st.markdown(f"""
                <div class="email-box">
                    <p><strong>From:</strong> <code>{current_email.sender}</code></p>
                    <p><strong>To:</strong> <code>{current_email.recipient}</code></p>
                    <p><strong>Subject:</strong> <strong>{current_email.subject}</strong></p>
                    <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
                    <p style="white-space: pre-wrap; color: #cbd5e1; font-size: 0.92rem; line-height: 1.6;">{current_email.body}</p>
                </div>
            """, unsafe_allow_html=True)

            status_color = "badge-pending"
            if current_email.verification_status == "approved":
                status_color = "badge-approved"
            elif current_email.verification_status == "corrected":
                status_color = "badge-corrected"

            st.markdown(f"**Current Status:** <span class='{status_color}'>{current_email.verification_status.upper()}</span>", unsafe_allow_html=True)
            if current_email.verified_category:
                st.markdown(f"**Verified Category:** `{current_email.verified_category}`")

        with col_right:
            st.markdown("#### ⚡ AI Agent Actions")

            # Check if this email was already classified in session
            session_key = f"classify_result_{selected_id}"
            
            classify_btn = st.button("🚀 Classify with AI Agent (Ollama gemma4)", type="primary", use_container_width=True)

            if classify_btn:
                with st.spinner("Agent running: fetching context, querying Ollama gemma4:latest..."):
                    thread_config = {"configurable": {"thread_id": f"streamlit_email_{selected_id}"}}
                    initial_state = {"email_id": selected_id}
                    email_agent_graph.invoke(initial_state, config=thread_config)
                    snapshot = email_agent_graph.get_state(thread_config)

                    if snapshot.tasks and snapshot.tasks[0].interrupts:
                        val = snapshot.tasks[0].interrupts[0].value
                        st.session_state[session_key] = val
                    else:
                        st.session_state[session_key] = {
                            "email_id": selected_id,
                            "ai_category": current_email.ai_category or "Payroll",
                            "confidence": current_email.ai_confidence or 0.95,
                            "reasoning": current_email.classification_reason or "Classified by agent."
                        }

            # If classification result exists
            ai_data = st.session_state.get(session_key)
            if not ai_data and current_email.ai_category:
                ai_data = {
                    "email_id": selected_id,
                    "ai_category": current_email.ai_category,
                    "confidence": current_email.ai_confidence or 0.95,
                    "reasoning": current_email.classification_reason or "Classified in previous run."
                }

            if ai_data:
                conf_pct = int(ai_data['confidence'] * 100)
                cat = ai_data['ai_category']
                cat_class = f"badge-{cat.lower()}"

                st.markdown(f"""
                    <div class="prediction-box">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 0.78rem; text-transform: uppercase; color: #94a3b8; font-weight: 600;">Predicted Category</span>
                                <div><span class="{cat_class}" style="font-size: 1.1rem; padding: 4px 14px; margin-top: 4px;">{cat}</span></div>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 0.78rem; text-transform: uppercase; color: #94a3b8; font-weight: 600;">Confidence</span>
                                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #34d399;">{conf_pct}%</div>
                            </div>
                        </div>
                        <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.08);">
                            <span style="font-size: 0.76rem; color: #a5b4fc; font-weight: 600;">AGENT REASONING:</span>
                            <p style="font-size: 0.86rem; color: #e2e8f0; margin-top: 4px; line-height: 1.45;">{ai_data['reasoning']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("### 🧑‍⚖️ Human Decision")
                st.caption("Is this classification correct? Your decision updates NeonDB directly.")

                yes_col, no_col = st.columns(2)
                
                with yes_col:
                    if st.button("✅ YES (Accept AI Label)", use_container_width=True, type="secondary"):
                        thread_config = {"configurable": {"thread_id": f"streamlit_email_{selected_id}"}}
                        resume_payload = {
                            "decision": "YES",
                            "correct_category": None,
                            "feedback": "Approved by human reviewer via Streamlit",
                            "verified_by": "human_reviewer"
                        }
                        try:
                            email_agent_graph.invoke(Command(resume=resume_payload), config=thread_config)
                        except Exception:
                            db = get_db_session()
                            repo = EmailRepository(db)
                            repo.record_human_verification(selected_id, "YES", verified_by="human_reviewer")
                            db.close()

                        st.success(f"✓ Approved! '{cat}' persisted to NeonDB as ground truth.")
                        st.session_state.pop(session_key, None)
                        st.rerun()

                with no_col:
                    show_correction = st.toggle("❌ NO (Override / Correct)", key=f"toggle_no_{selected_id}")

                if show_correction:
                    st.markdown("#### Select Correct Category:")
                    correction_choice = st.radio(
                        "Categories:",
                        ["Payroll", "Benefits", "Tax"],
                        horizontal=True,
                        key=f"radio_cat_{selected_id}"
                    )
                    feedback_text = st.text_input(
                        "Reviewer Feedback (optional):",
                        placeholder=f"e.g. This discusses tax deductions rather than {cat}.",
                        key=f"fb_{selected_id}"
                    )

                    if st.button("💾 Submit Correction to NeonDB", type="primary", use_container_width=True):
                        thread_config = {"configurable": {"thread_id": f"streamlit_email_{selected_id}"}}
                        resume_payload = {
                            "decision": "NO",
                            "correct_category": correction_choice,
                            "feedback": feedback_text or f"Corrected from {cat} to {correction_choice}",
                            "verified_by": "human_supervisor"
                        }
                        try:
                            email_agent_graph.invoke(Command(resume=resume_payload), config=thread_config)
                        except Exception:
                            db = get_db_session()
                            repo = EmailRepository(db)
                            repo.record_human_verification(
                                selected_id, "NO",
                                correct_category=correction_choice,
                                feedback=feedback_text or f"Corrected to {correction_choice}",
                                verified_by="human_supervisor"
                            )
                            db.close()

                        st.success(f"✓ Overridden! Ground truth set to '{correction_choice}'. AI prediction preserved.")
                        st.session_state.pop(session_key, None)
                        st.rerun()


# ==========================================
# TAB 2: Email Database Explorer
# ==========================================
with tab_explorer:
    st.markdown("### 📋 NeonDB Email Explorer")
    
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        search_kw = st.text_input("🔍 Search Subject, Body, or Sender:", placeholder="e.g. salary, 401k, withholding...")
    with col_s2:
        cat_filter = st.selectbox("Category Filter:", ["All", "Payroll", "Benefits", "Tax"])
    with col_s3:
        stat_filter = st.selectbox("Verification Status Filter:", ["All", "pending", "approved", "corrected"])

    c_param = None if cat_filter == "All" else cat_filter
    s_param = None if stat_filter == "All" else stat_filter
    q_param = search_kw.strip() if search_kw else None

    emails_exp, total_count = fetch_all_emails(status_filter=s_param, category_filter=c_param, search=q_param)

    st.write(f"Showing **{len(emails_exp)}** of **{total_count}** matching emails.")

    if emails_exp:
        data_rows = []
        for e in emails_exp:
            data_rows.append({
                "ID": e.id,
                "Sender": e.sender,
                "Subject": e.subject,
                "AI Category": e.ai_category or "Unclassified",
                "Confidence": f"{int(e.ai_confidence * 100)}%" if e.ai_confidence else "--",
                "Verified Category": e.verified_category or "--",
                "Status": e.verification_status,
                "Reviewer": e.verified_by or "--"
            })
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ==========================================
# TAB 3: Analytics & Distribution
# ==========================================
with tab_analytics:
    st.markdown("### 📊 Email & Classification Analytics")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### Category Breakdown")
        cat_df = pd.DataFrame({
            "Category": ["Payroll", "Benefits", "Tax"],
            "Count": [stats['payroll_emails'], stats['benefits_emails'], stats['tax_emails']]
        })
        st.bar_chart(cat_df.set_index("Category"), color="#6366f1")

    with col_chart2:
        st.markdown("#### Verification Status Distribution")
        status_df = pd.DataFrame({
            "Status": ["Pending", "Approved", "Corrected"],
            "Count": [stats['pending_verification'], stats['approved'], stats['corrected']]
        })
        st.bar_chart(status_df.set_index("Status"), color="#10b981")


# ==========================================
# TAB 4: Model Evaluation
# ==========================================
with tab_eval:
    st.markdown("### 📈 Evaluation Metrics (AI Prediction vs. Ground Truth)")
    st.caption("Calculated strictly over human-verified emails stored in NeonDB.")

    db = get_db_session()
    repo = EmailRepository(db)
    eval_metrics = repo.get_evaluation_metrics()
    db.close()

    eval_col1, eval_col2 = st.columns([1, 2])
    with eval_col1:
        acc_pct = int(eval_metrics['accuracy'] * 100)
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; padding: 30px;">
                <div class="metric-title">Overall Accuracy</div>
                <div class="metric-number" style="color: #34d399; font-size: 3rem;">{acc_pct}%</div>
                <div class="metric-sub">{eval_metrics['verified_count']} Verified Emails Evaluated</div>
            </div>
        """, unsafe_allow_html=True)

    with eval_col2:
        metrics_table = [
            {
                "Category": "Payroll",
                "Precision": f"{int(eval_metrics['payroll']['precision'] * 100)}%",
                "Recall": f"{int(eval_metrics['payroll']['recall'] * 100)}%",
                "F1-Score": f"{eval_metrics['payroll']['f1']:.2f}",
                "Support": eval_metrics['payroll']['support']
            },
            {
                "Category": "Benefits",
                "Precision": f"{int(eval_metrics['benefits']['precision'] * 100)}%",
                "Recall": f"{int(eval_metrics['benefits']['recall'] * 100)}%",
                "F1-Score": f"{eval_metrics['benefits']['f1']:.2f}",
                "Support": eval_metrics['benefits']['support']
            },
            {
                "Category": "Tax",
                "Precision": f"{int(eval_metrics['tax']['precision'] * 100)}%",
                "Recall": f"{int(eval_metrics['tax']['recall'] * 100)}%",
                "F1-Score": f"{eval_metrics['tax']['f1']:.2f}",
                "Support": eval_metrics['tax']['support']
            }
        ]
        st.markdown("#### Per-Category Performance")
        st.table(pd.DataFrame(metrics_table))


# ==========================================
# TAB 5: Database & System
# ==========================================
with tab_db:
    st.markdown("### ⚙️ Database & Infrastructure")

    st.markdown("#### NeonDB PostgreSQL Schema")
    if st.button("Inspect Live Schema"):
        schema_info = inspect_database_schema()
        st.json(schema_info)

    st.markdown("---")
    st.markdown("#### Database Seeding")
    st.write("Reset or re-seed the 30 realistic HR emails into NeonDB (10 Payroll, 10 Benefits, 10 Tax).")
    if st.button("🌱 Re-Seed 30 Sample Emails"):
        with st.spinner("Seeding emails into NeonDB..."):
            seed_database(reset=False)
            st.success("Database seeded! Status initialized to pending.")
            st.rerun()
