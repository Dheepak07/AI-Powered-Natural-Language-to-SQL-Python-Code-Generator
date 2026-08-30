"""
frontend/app.py
Streamlit application — NL2SQL AI Code Generator
Run: streamlit run frontend/app.py
"""
from __future__ import annotations

import sys
import os

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import datetime

from config.settings import settings
from src.ai.chain import NL2SQLChain
from src.db.connector import test_connection
from src.db.executor import execute_query
from src.validation.sql_validator import SQLValidator
from src.utils.logger import get_logger

logger = get_logger("frontend.app")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NL2SQL · AI Code Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    .stCodeBlock { font-size: 0.82rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border-left: 4px solid #6c63ff;
        margin-bottom: 0.5rem;
    }
    .tag {
        display: inline-block;
        background: #e8e3ff;
        color: #3c35a5;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []          # list of past question dicts
if "chain" not in st.session_state:
    st.session_state.chain = None
if "db_ok" not in st.session_state:
    st.session_state.db_ok = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.shields.io/badge/NL2SQL-AI%20Powered-6c63ff?style=for-the-badge",
        use_container_width=True,
    )
    st.markdown("### ⚙️ Configuration")

    # DB Status
    if st.button("🔌 Test DB Connection"):
        with st.spinner("Connecting…"):
            st.session_state.db_ok = test_connection()
    status_icon = "✅" if st.session_state.db_ok else "❌"
    st.markdown(f"**Database:** {status_icon} {'Connected' if st.session_state.db_ok else 'Not connected'}")

    st.divider()
    st.markdown("### 💡 Sample Questions")
    sample_questions = [
        "Show top 10 customers by total revenue",
        "Monthly revenue trend for 2024",
        "Which product categories have the highest sales?",
        "Average order value by customer segment",
        "Which sales reps closed the most orders?",
        "Customers who haven't ordered in 90 days",
        "Revenue split by region",
        "Top 5 products by profit margin",
        "Return rate by product category",
        "Payment mode breakdown",
    ]
    for q in sample_questions:
        if st.button(q, key=f"sq_{q[:20]}", use_container_width=True):
            st.session_state["prefill_question"] = q

    st.divider()
    st.markdown("### 📋 Query History")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-10:])):
            with st.expander(f"{item['timestamp']} · {item['question'][:40]}…", expanded=False):
                st.code(item["sql"], language="sql")
    else:
        st.caption("No queries yet.")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🔍 AI-Powered NL → SQL & Python Code Generator")
st.caption(
    "Enter a business question in plain English. The AI will generate a SQL query, "
    "Pandas code, an explanation, and a visualisation recommendation."
)

st.divider()

# ── Input ──────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill_question", "")
question = st.text_area(
    "Your business question",
    value=prefill,
    placeholder="e.g. Show top 10 customers by total revenue",
    height=80,
)

col_btn1, col_btn2, _ = st.columns([1, 1, 5])
generate_clicked = col_btn1.button("✨ Generate", type="primary", use_container_width=True)
clear_clicked = col_btn2.button("🗑 Clear", use_container_width=True)

if clear_clicked:
    st.rerun()

# ── Pipeline ──────────────────────────────────────────────────────────────────
if generate_clicked and question.strip():
    # Initialise chain (singleton per session)
    if st.session_state.chain is None:
        with st.spinner("Loading AI engine…"):
            try:
                st.session_state.chain = NL2SQLChain()
            except EnvironmentError as e:
                st.error(f"⚠️ {e}")
                st.stop()

    chain: NL2SQLChain = st.session_state.chain

    with st.spinner("🤖 Thinking…"):
        ai_resp = chain.run(question.strip())

    if not ai_resp.is_valid:
        st.error(f"AI generation failed: {ai_resp.parse_error}")
        st.expander("Raw AI response").write(ai_resp.raw_response)
        st.stop()

    # ── Validate SQL ──────────────────────────────────────────────────────────
    validator = SQLValidator(known_tables=chain.schema_tables)
    val_result = validator.validate(ai_resp.sql, schema_tables=chain.schema_tables)

    # ── Layout: 3 tabs ────────────────────────────────────────────────────────
    tab_sql, tab_py, tab_results = st.tabs(["📝 SQL Query", "🐍 Python / Pandas", "📊 Results"])

    with tab_sql:
        st.markdown("#### Generated SQL")
        if val_result.warnings:
            for w in val_result.warnings:
                st.warning(f"⚠️ {w}")
        if not val_result.valid:
            st.error(f"❌ SQL Validation Failed: {val_result.error_summary}")
        else:
            st.success("✅ SQL passed validation")

        st.code(ai_resp.sql, language="sql")

        st.markdown("#### Explanation")
        st.info(ai_resp.explanation)

        st.markdown("#### Recommended Visualisation")
        viz = ai_resp.visualization
        cols = st.columns(4)
        chart_icon = {
            "bar": "📊", "line": "📈", "pie": "🥧",
            "scatter": "⚬", "table": "📋", "heatmap": "🟥",
        }.get(viz.chart_type, "📊")
        cols[0].metric("Chart type", f"{chart_icon} {viz.chart_type.title()}")
        cols[1].metric("X-axis", viz.x_axis or "—")
        cols[2].metric("Y-axis", viz.y_axis or "—")
        st.caption(f"💡 {viz.rationale}")

    with tab_py:
        st.markdown("#### Python / Pandas Code")
        st.markdown(
            "_Assumes SQL result is available as `df` (a Pandas DataFrame). "
            "Extend this code for dashboards, exports, or further analysis._"
        )
        full_pandas = f"""import pandas as pd
from sqlalchemy import create_engine, text

# ── Database connection ────────────────────────────────────────────────
engine = create_engine(
    "mysql+pymysql://USER:PASSWORD@localhost:3306/ecommerce_db"
)

# ── Execute SQL and load into DataFrame ───────────────────────────────
sql = \"\"\"{ai_resp.sql}\"\"\"
df = pd.read_sql(text(sql), con=engine.connect())

# ── AI-generated analysis code ────────────────────────────────────────
{ai_resp.pandas_code}
"""
        st.code(full_pandas, language="python")

        st.markdown("#### Copy-paste snippet (analysis only)")
        st.code(ai_resp.pandas_code, language="python")

    with tab_results:
        if not st.session_state.db_ok:
            st.warning("Database is not connected. Click **Test DB Connection** in the sidebar.")
        elif not val_result.valid:
            st.error("Cannot execute: SQL failed validation.")
        else:
            if st.button("▶️ Execute SQL against MySQL"):
                with st.spinner("Running query…"):
                    qr = execute_query(val_result.cleaned_sql)
                if qr.success:
                    st.success(
                        f"✅ {qr.rows_returned} rows returned in {qr.execution_time_ms:.0f} ms"
                    )
                    st.dataframe(qr.data, use_container_width=True, height=400)

                    # Download
                    csv = qr.data.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Download CSV",
                        data=csv,
                        file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.error(f"Query failed: {qr.error}")

    # ── Save to history ───────────────────────────────────────────────────────
    st.session_state.history.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "question": question.strip(),
        "sql": ai_resp.sql,
    })

elif generate_clicked and not question.strip():
    st.warning("Please enter a question first.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<small>Built with ❤️ · Streamlit · LangChain · Anthropic Claude · MySQL · "
    "Portfolio project by <b>Dheepak P.L.M.</b></small>",
    unsafe_allow_html=True,
)
