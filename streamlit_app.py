# streamlit_app.py - Streamlit UI for customer support

import os
import sys
import json
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

import config
from utils.document_processor import DocumentProcessor
from knowledge_bases.kb_manager import KnowledgeBase, KnowledgeBaseRouter
from conversation.memory_manager import ConversationManager
from utils.response_formatter import ResponseFormatter
from tools.compatibility_checker import CompatibilityChecker, COMPATIBILITY_MATRIX
from tools.diagnostics import DiagnosticsTool, STATUS_DB
from tools.order_lookup import OrderLookupTool, TICKET_DB
from tools.ticket_manager import TicketManager, SLA_MAP
from tools.callback_scheduler import CallbackScheduler
from tools.plan_upgrade import PlanUpgradeCalculator, UPGRADE_CATALOG

# ── Streamlit Cloud secrets support ──────────────────────────────────────────
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ.setdefault("GROQ_API_KEY", st.secrets["GROQ_API_KEY"])
except Exception:
    pass

st.set_page_config(
    page_title="Customer Support System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }

.hero {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    padding: 22px 28px; border-radius: 16px; color: white;
    margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.hero h1 { margin: 0; font-size: 1.7rem; font-weight: 700; }
.hero p  { margin: 4px 0 0; opacity: 0.75; font-size: 0.9rem; }

.product-card {
    border-radius: 12px; padding: 14px 16px; text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    transition: transform 0.2s;
}
.product-card:hover { transform: translateY(-2px); }

.stat-box {
    background: rgba(99,102,241,0.12); border: 1px solid rgba(99,102,241,0.3);
    border-radius: 10px; padding: 10px; text-align: center;
}
.stat-num { font-size: 1.5rem; font-weight: 700; color: #818cf8; }
.stat-lbl { font-size: 0.7rem; color: #64748b; text-transform: uppercase; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #1e1b4b 100%);
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3);
    color: #a5b4fc !important; border-radius: 8px; width: 100%;
    font-size: 0.82rem; transition: all 0.2s; margin-bottom: 2px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(99,102,241,0.25); border-color: #6366f1;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CACHED RESOURCE BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def build_knowledge_bases(api_key: str):
    config.GROQ_API_KEY = api_key
    os.environ["GROQ_API_KEY"] = api_key

    llm = ChatGroq(api_key=api_key, model=config.GROQ_MODEL, temperature=config.LLM_TEMPERATURE)
    processor = DocumentProcessor()

    product_map = {
        "cloud_services": (config.PRODUCT_A_DIR, "CloudStore Pro"),
        "security_products": (config.PRODUCT_B_DIR, "SecureVault AI"),
        "analytics_platform": (config.PRODUCT_C_DIR, "DataFlow Analytics"),
        "project_management": (config.PRODUCT_D_DIR, "TeamFlow Pro"),
    }

    kbs = {}
    for kb_name, (directory, display_name) in product_map.items():
        vs = processor.get_or_create_vector_store(directory, kb_name)
        kbs[kb_name] = KnowledgeBase(vs, display_name, llm=llm)

    router = KnowledgeBaseRouter(kbs, llm=llm)
    formatter = ResponseFormatter(config.COMPANY_NAME, config.SUPPORT_EMAIL, config.SUPPORT_PHONE)
    return kbs, router, formatter


# ═══════════════════════════════════════════════════════════════════════════════
#  LANGGRAPH TOOLS (thin wrappers calling the modular BaseTool classes)
# ═══════════════════════════════════════════════════════════════════════════════

@tool
def check_ticket_status(ticket_id: str) -> str:
    """Look up a support ticket by ID, e.g. TKT-001."""
    return OrderLookupTool().run(ticket_id)

@tool
def calculate_plan_upgrade(query: str) -> str:
    """Show upgrade cost/benefits. Input: 'product | plan', e.g. 'CloudStore Pro | Starter->Business'."""
    return PlanUpgradeCalculator().run(query)

@tool
def generate_support_ticket(query: str) -> str:
    """Create a ticket. Input: 'issue | product | severity'."""
    return TicketManager().run(query)

@tool
def get_system_status(product: str) -> str:
    """Check live status of a product."""
    return DiagnosticsTool().run(product)

@tool
def schedule_callback(query: str) -> str:
    """Book a support callback. Input: 'name | email | time | issue'."""
    return CallbackScheduler().run(query)

@tool
def check_compatibility(query: str) -> str:
    """Check if two products work together. Input: 'Product A, Product B'."""
    return CompatibilityChecker().run(query)


AGENT_TOOLS = [
    check_ticket_status, calculate_plan_upgrade, generate_support_ticket,
    get_system_status, schedule_callback, check_compatibility,
]


# ═══════════════════════════════════════════════════════════════════════════════
#  AI RESPONSE (LangGraph agent + FAISS retrieval)
# ═══════════════════════════════════════════════════════════════════════════════

def get_ai_response(api_key, user_input, router, formatter, memory_mgr, product_filter):
    llm = ChatGroq(api_key=api_key, model=config.GROQ_MODEL, temperature=0.15)

    if product_filter != "All Products":
        kb_key_map = {
            "CloudStore Pro": "cloud_services",
            "SecureVault AI": "security_products",
            "DataFlow Analytics": "analytics_platform",
            "TeamFlow Pro": "project_management",
        }
        kb_key = kb_key_map.get(product_filter)
        if kb_key and kb_key in router.knowledge_bases:
            kb = router.knowledge_bases[kb_key]
        else:
            kb = router.route_query(user_input)
    else:
        kb = router.route_query(user_input)

    docs = kb.retriever.invoke(user_input)
    context = "\n\n".join(d.page_content for d in docs) if docs else "No specific KB context found."

    system = f"""You are an Enterprise Customer Support Agent at {config.COMPANY_NAME}.
You provide accurate, empathetic, and professional support for:
  - CloudStore Pro (cloud storage)
  - SecureVault AI (password & secrets manager)
  - DataFlow Analytics (business intelligence)
  - TeamFlow Pro (project management & collaboration)
{f'Current focus: {product_filter}' if product_filter != 'All Products' else 'Supporting all four products.'}

You have 6 tools available:
  1. check_ticket_status       — look up existing tickets by ID
  2. calculate_plan_upgrade    — show upgrade pricing and benefits
  3. generate_support_ticket   — create a new ticket
  4. get_system_status         — check live service status
  5. schedule_callback         — book a support call
  6. check_compatibility       — verify product integrations

Guidelines:
  - Always search the knowledge base context first before using tools
  - Give numbered step-by-step troubleshooting instructions
  - If you detect a billing or complex issue, offer to create a ticket
  - If the issue needs human escalation, offer a callback
  - Be warm, professional and solution-focused
  - End with: "Is there anything else I can help you with?"

Current date/time: {datetime.now().strftime('%A, %B %d, %Y %H:%M UTC')}"""

    messages = list(memory_mgr.get_langchain_messages()[-10:])
    messages.append(HumanMessage(content=f"Knowledge base context:\n{context}\n\nCustomer message: {user_input}"))

    agent = create_react_agent(llm, AGENT_TOOLS, prompt=system)
    result = agent.invoke({"messages": messages})
    answer = result["messages"][-1].content

    answer = formatter.filter_response(answer)
    return answer, docs


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def init_session():
    defaults = {"messages": [], "tickets": 0, "kb_ready": False}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "memory_mgr" not in st.session_state:
        st.session_state.memory_mgr = ConversationManager(memory_type="buffer")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    init_session()

    st.markdown("""
    <div class="hero">
        <h1>Customer Support System</h1>
        <p>AI-powered enterprise support · FAISS retrieval · LangChain agents · 4 product lines · 6 tools</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## Configuration")
        default_key = os.environ.get("GROQ_API_KEY", "")
        api_key = st.text_input(
            "GROQ API Key",
            value=default_key,
            type="password",
            placeholder="gsk_...",
            help="Get a free key at https://console.groq.com/keys",
        )
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
            config.GROQ_API_KEY = api_key

        st.divider()
        st.markdown("### Product Filter")
        product_filter = st.selectbox(
            "Focus on",
            ["All Products", "CloudStore Pro", "SecureVault AI", "DataFlow Analytics", "TeamFlow Pro"],
        )

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{len(st.session_state.messages) // 2}</div><div class="stat-lbl">Turns</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="stat-box"><div class="stat-num">{st.session_state.tickets}</div><div class="stat-lbl">Tickets</div></div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("### Quick Questions")
        quick = [
            "CloudStore sync stopped working",
            "SecureVault browser extension not filling",
            "How do I set up SSO for SecureVault?",
            "DataFlow dashboard is loading very slowly",
            "Check ticket TKT-005",
            "What's the status of SecureVault AI?",
            "Upgrade CloudStore from Starter to Business",
            "TeamFlow automations not triggering",
            "Are CloudStore and DataFlow compatible?",
            "Schedule a callback for a critical issue",
        ]
        for q in quick:
            if st.button(q, key=f"q_{q[:20]}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                st.rerun()

        st.divider()
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Clear", use_container_width=True):
                st.session_state.messages = []
                st.session_state.memory_mgr.clear()
                st.rerun()
        with col_b:
            if st.session_state.messages:
                chat_md = "\n\n".join(
                    f"**{'You' if m['role'] == 'user' else 'Assistant'}:** {m['content']}"
                    for m in st.session_state.messages
                )
                st.download_button("Export", data=chat_md, file_name="support_chat.md",
                                   mime="text/markdown", use_container_width=True)

    # ── Product cards ────────────────────────────────────────────────────────
    products = [
        ("CloudStore Pro", "#1565c0", "Cloud Storage · API · 99.99% SLA"),
        ("SecureVault AI", "#6a1b9a", "Password Mgr · SSO · Breach Monitor"),
        ("DataFlow Analytics", "#1b5e20", "BI · AutoML · Real-time Streaming"),
        ("TeamFlow Pro", "#b71c1c", "Project Mgmt · Collaboration · OKRs"),
    ]
    cols = st.columns(4)
    for col, (name, color, desc) in zip(cols, products):
        with col:
            st.markdown(
                f'<div class="product-card" style="border-color:{color}44;">'
                f'<b style="color:{color}">{name}</b><br><small style="color:#94a3b8">{desc}</small></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Welcome ──────────────────────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:50px 20px;color:#64748b;">
            <h3>Welcome to Customer Support</h3>
            <p>Describe your issue, ask a technical question, check a ticket, or explore upgrade options.</p>
            <p style="font-size:0.8rem">Powered by Groq · LLaMA 3.3 70B · FAISS Retrieval · LangChain · LangGraph</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Chat history ─────────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Chat input ───────────────────────────────────────────────────────────
    user_input = st.chat_input("Describe your issue or ask anything…")

    if user_input:
        if not api_key:
            st.error("Please enter your GROQ API Key in the sidebar.")
            return

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    kbs, router, formatter = build_knowledge_bases(api_key)
                    memory_mgr = st.session_state.memory_mgr
                    memory_mgr.add_user_message(user_input)

                    response, docs = get_ai_response(
                        api_key, user_input, router, formatter, memory_mgr, product_filter
                    )

                    if "Created" in response and "TKT-" in response:
                        st.session_state.tickets += 1

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    memory_mgr.add_ai_message(response)

                    if docs:
                        with st.expander(f"{len(docs)} KB Chunks Retrieved"):
                            for i, d in enumerate(docs, 1):
                                st.markdown(f"**#{i}** — `{d.metadata.get('source', 'unknown')}`")
                                st.caption(d.page_content[:300] + "…")
                                st.divider()

                except Exception as e:
                    err = f"Error: {e}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})


if __name__ == "__main__":
    main()
