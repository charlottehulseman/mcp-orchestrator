#!/usr/bin/env python3
"""
Boxonomics - Boxing Intelligence Platform
Sleek black and red design matching splash page aesthetic
"""

import streamlit as st
import asyncio
import time
import base64
from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, ToolMessage

# Try to import observability
try:
    from observability.monitoring import get_monitor, reset_monitor
    OBSERVABILITY_AVAILABLE = True
except Exception:
    OBSERVABILITY_AVAILABLE = False


# -------------------- Page configuration --------------------
st.set_page_config(
    page_title="Boxonomics",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def get_base64_image(image_path: str):
    """Convert image to base64 for CSS background."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None


# -------------------- Splash Page Styles --------------------
def inject_splash_css(bg_image_base64: str | None = None):
    """Inject CSS for sleek, minimal splash page."""
    if bg_image_base64:
        background = f"""
            background: linear-gradient(rgba(0,0,0,0.40), rgba(0,0,0,0.60)),
                        url(data:image/png;base64,{bg_image_base64});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        background = """
            background: linear-gradient(135deg, #0A0E27 0%, #1A1F3A 100%);
        """

    css = """
    <style>
        /* Hide Streamlit chrome on splash */
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        header, footer { display: none !important; }

        .stApp { background-color: #000 !important; overflow: hidden; }
        .main { padding: 0 !important; background-color: transparent !important; }
        .block-container { padding: 0 !important; margin: 0 !important; max-width: 100% !important; }
        .element-container { margin: 0 !important; padding: 0 !important; }
        div[data-testid="column"] { padding: 0 !important; }

        .splash-container {
            %BACKGROUND%
            position: fixed; inset: 0;
            width: 100vw; height: 100vh;
            display: flex; flex-direction: column;
            justify-content: center; align-items: flex-start;
            padding-left: 8%; z-index: 1;
        }
        .splash-content { max-width: 700px; text-align: left; }
        .splash-logo {
            font-size: 7rem; font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 50%, #8B0000 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; margin-bottom: 1.5rem; letter-spacing: -2px;
            animation: fadeInLeft 0.8s ease-out; text-transform: uppercase;
        }
        .splash-tagline {
            font-size: 1.4rem; color: #D0D3DC; margin-bottom: 2.5rem;
            font-weight: 300; animation: fadeInLeft 1s ease-out; line-height: 1.6;
        }

        /* Scope styling to the start_btn via its key class */
        .st-key-start_btn [data-testid="stButton"] {
            position: fixed !important;
            left: 8% !important;
            top: 65% !important;
            z-index: 2147483647 !important;
            width: auto !important;
            pointer-events: auto !important;
        }
        .st-key-start_btn [data-testid="stButton"] > button {
            background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 100%) !important;
            color: #fff !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            padding: 0.75rem 2.75rem !important;
            border: none !important;
            border-radius: 50px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 25px rgba(255,59,59,0.4) !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            animation: fadeInUp 1.5s ease-out, pulse 2s ease-in-out 2s infinite !important;
            white-space: nowrap !important;
        }
        .st-key-start_btn [data-testid="stButton"] > button:hover {
            background: linear-gradient(135deg, #B71C1C 0%, #FF3B3B 100%) !important;
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 35px rgba(255,59,59,0.6) !important;
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes fadeInLeft { from { opacity:0; transform:translateX(-50px);} to { opacity:1; transform:none; } }
        @keyframes fadeInUp { from { opacity:0; transform:translateY(30px);} to { opacity:1; transform:none; } }
        @keyframes pulse {
            0%, 100% { box-shadow: 0 8px 25px rgba(255, 59, 59, 0.4); }
            50%      { box-shadow: 0 8px 35px rgba(255, 59, 59, 0.7); }
        }
    </style>
    """.replace("%BACKGROUND%", background)

    st.markdown(css, unsafe_allow_html=True)


def show_splash_page():
    """Display the simplified splash/landing page."""
    bg_image_path = "frontend/assets/splash_bg.png"
    bg_image_base64 = get_base64_image(bg_image_path)
    inject_splash_css(bg_image_base64)

    st.markdown(
        """
        <div class="splash-container">
          <div class="splash-content">
            <div class="splash-logo">BOXONOMICS</div>
            <div class="splash-tagline">AI-Powered Boxing Intelligence &amp; Analysis Platform</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Get in the Ring", key="start_btn", type="primary"):
        st.session_state.show_splash = False
        st.rerun()


# -------------------- Main App CSS --------------------
def inject_main_css():
    """Inject CSS for main chatbot interface."""
    st.markdown(
        """
        <style>
        /* App backdrop */
        .stApp {
        background: linear-gradient(to bottom right, #191C20 70%, #8c1616);
        background-attachment: fixed;
        }
        .main { max-width: 1400px; margin: 0 auto; }

        /* Hero */
        .hero-section { max-width: 1200px; margin: 0 auto; padding: 3rem 2rem 2rem; text-align: center; }
        .main-header {
        font-size: 4rem; font-weight: 100;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
        text-align: center;
        background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 50%, #8B0000 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 1rem; letter-spacing: -1.5px; text-transform: uppercase;
        }
        .sub-header { text-align:center; color:#D0D3DC; font-size:1.1rem; margin-bottom:2.5rem; font-weight:300; max-width:700px; margin-left:auto; margin-right:auto; line-height:1.6; }

        /* Layout */
        .chat-area { padding-right: 1rem; }
        .chat-input-section { max-width: 1000px; margin: 0 auto 3rem; padding: 0; }

        /* Input */
        .stTextInput > div > div > input {
        background:#2C2D3D !important; color:#FFF !important; border:none !important;
        padding:0.95rem 1.6rem 2rem !important; font-size:1rem !important; line-height:1.5 !important;
        border-radius:12px !important; transition:all .3s ease !important; font-weight:300 !important; height:56px !important;
        box-sizing:border-box !important; vertical-align:middle !important;
        }
        .stTextInput > div > div { border-radius:12px !important; border-color:#717395 !important; }
        .stTextInput > div { border-radius:12px !important; border-color:#717395 !important; }
        .stTextInput > div > div > input:focus { background:#353647 !important; box-shadow:0 0 0 2px rgba(14,165,233,.3) !important; }
        .stTextInput > div > div > input::placeholder { color:rgba(255,255,255,.7) !important; font-weight:300 !important; }

        /* ANALYZE button */
        button[data-testid="stBaseButton-primary"]{
        background:linear-gradient(135deg,#FF3B3B 0%,#B71C1C 100%) !important;
        color:#fff !important; border:none !important; border-radius:12px !important;

        height:56px !important; padding:0 24px !important; min-width:140px !important;

        font-weight:600 !important; font-size:.95rem !important; text-transform:uppercase !important; letter-spacing:.08em !important;

        display:inline-flex !important; align-items:center !important; justify-content:center !important;
        white-space:nowrap !important; word-break:keep-all !important;

        box-sizing:border-box !important; transition:all .3s ease !important;
        box-shadow:0 4px 12px rgba(255,59,59,.35) !important;
        }
        button[data-testid="stBaseButton-primary"]:hover{
        background:linear-gradient(135deg,#B71C1C 0%,#FF3B3B 100%) !important;
        transform:translateY(-2px) !important; box-shadow:0 6px 20px rgba(255,59,59,.5) !important;
        }

        /* Messages */
        .chat-message {
        padding:1.75rem; border-radius:16px; margin:1rem auto; max-width:1000px;
        background:rgba(20,20,25,.98); border:1px solid rgba(60,60,70,.4); backdrop-filter:blur(10px);
        }
        .user-message { border-left:3px solid #4A81CC; }
        .assistant-message { border-left:3px solid #B71C1C; }

        .message-role { font-weight:600; font-size:.85rem; color:#909099; margin-bottom:.9rem; text-transform:uppercase; letter-spacing:1.2px; }
        .message-content { color:#E8E8ED; line-height:1.8; font-size:1.05rem; font-weight:300; }

        /* Tool call chips */
        .tool-call {
        background:rgba(74,129,204,.15); border:1px solid rgba(74,129,204,.3);
        border-radius:10px; padding:.85rem; margin:.6rem 0; font-size:.9rem; color:#E8E8ED;
        }
        .tool-name { color:#4A81CC; font-weight:600; }
        .tool-server { color:#909099; font-size:.85rem; }
        .tool-duration { color:#00D084; font-weight:500; }

        /* Sidebar skin */
        [data-testid="stSidebar"] { background:#000; border-right:1px solid rgba(60,60,70,.3); }

        /* Examples left rail */
        .examples-wrap { background:#20232D; border-radius:14px; padding:12px; height:100%; }
        .examples-sticky { position:sticky; top:75px; }
        .examples-title { color:#9aa7bd; font-weight:700; font-size:.9rem; text-transform:uppercase; letter-spacing:1px; margin:4px 0 10px 2px; }

        .block-container :not([data-testid="stSidebar"]) button[data-testid="stBaseButton-secondary"]{
        width:100%; text-align:left; background:#2A2E4F !important; color:#4A81CC !important;
        border:1px solid rgba(255,255,255,.06) !important; border-radius:12px !important;
        padding:12px !important; box-shadow:none !important; font-weight:500 !important;
        line-height:1.35 !important; white-space:normal !important; word-break:break-word !important; min-height:84px;
        }
        .block-container :not([data-testid="stSidebar"]) button[data-testid="stBaseButton-secondary"] p{
        margin:0 !important; white-space:normal !important; word-break:break-word !important; line-height:1.35 !important;
        }
        .block-container :not([data-testid="stSidebar"]) button[data-testid="stBaseButton-secondary"]:hover{
        filter:brightness(1.06); transform:translateY(-1px);
        }

        /* Footer & misc */
        .footer { text-align:center; color:#606069; font-size:.9rem; margin-top:4rem; padding:2rem; border-top:1px solid rgba(60,60,70,.3); }
        ::-webkit-scrollbar{ width:10px; } ::-webkit-scrollbar-track{ background:#000; }
        ::-webkit-scrollbar-thumb{ background:rgba(183,28,28,.5); border-radius:5px; }
        ::-webkit-scrollbar-thumb:hover{ background:#B71C1C; }
        .stSpinner > div { border-top-color:#FF3B3B !important; }

        /* Expander (Tool Usage) theming + caption color */
        .streamlit-expanderHeader{ background-color:rgba(20,20,25,.5) !important; color:#fff !important; border:1px solid rgba(60,60,70,.35) !important; border-radius:8px !important; }
        .streamlit-expanderHeader:hover{ background-color:rgba(30,30,35,.7) !important; border-color:rgba(255,59,59,.3) !important; }
        .streamlit-expanderContent{ background-color:rgba(15,15,20,.95) !important; border:1px solid rgba(60,60,70,.35) !important; border-top:none !important; }
        [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color:#FFF !important; opacity:1 !important; }

        /* Prevent white background on <details> when expanded in some themes */
        div[data-testid="stExpander"] > details { background: transparent !important; }
        div[data-testid="stExpander"] > details > summary {
        background-color: rgba(20,20,25,.55) !important; color:#FFF !important;
        border:1px solid rgba(60,60,70,.35) !important; border-radius:10px !important;
        }
        div[data-testid="stExpander"] > details[open] > summary {
        background-color: rgba(20,20,25,.75) !important;
        }
        div[data-testid="stExpander"] > div[role="region"]{
        background-color:rgba(15,15,20,.95) !important; border:1px solid rgba(60,60,70,.35) !important; border-top:none !important;
        }
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span,
        div[data-testid="stExpander"] label,
        div[data-testid="stExpander"] button { color:#FFF !important; }
        
        [data-testid="stToolbar"],
        .stAppToolbar {
            background-color: #191C20 !important;
            color: #ffffff !important;
            border-bottom: 1px solid rgba(255,255,255,0.1) !important;
        }

        /* Ensure toolbar icons and menu dots are visible on black */
        [data-testid="stToolbar"] svg,
        [data-testid="stToolbar"] div,
        [data-testid="stToolbar"] button,
        [data-testid="stToolbar"] span {
            color: #ffffff !important;
            fill: #ffffff !important;
        }

        header, [data-testid="stHeader"] {
            box-shadow: none !important;
            background: transparent !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -------------------- Platform Init --------------------
@st.cache_resource
def initialize_platform():
    """Initialize platform with environment variables passed to subprocesses."""
    project_root = Path(__file__).parent.parent
    
    # Build environment dict to pass to subprocesses
    env_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
        "ODDS_API_KEY": os.getenv("ODDS_API_KEY", ""),
        "NEWS_API_KEY": os.getenv("NEWS_API_KEY", ""),
        "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID", ""),
        "REDDIT_CLIENT_SECRET": os.getenv("REDDIT_CLIENT_SECRET", ""),
        "REDDIT_USER_AGENT": os.getenv("REDDIT_USER_AGENT", "boxonomics/1.0"),
        "PYTHONPATH": str(project_root),
    }
    
    server_config = {
        "boxing_analytics": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_data.py")],
            "env": env_vars,  # Pass environment variables
        },
        "betting_odds": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_odds.py")],
            "env": env_vars,  # Pass environment variables
        },
        "fight_news": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_news.py")],
            "env": env_vars,  # Pass environment variables
        },
        "reddit_social": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "reddit.py")],
            "env": env_vars,  # Pass environment variables
        },
    }
    
    client = MultiServerMCPClient(server_config)
    
    async def async_init(): 
        return await client.get_tools()
    
    tools = asyncio.run(async_init())
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    agent = llm.bind_tools(tools)
    tool_map = {t.name: t for t in tools}
    
    return agent, tools, tool_map, client


def display_server_status():
    st.sidebar.markdown('<div class="section-header">Servers</div>', unsafe_allow_html=True)
    servers = [
        ("Analytics", "Fighter stats & history", "active"),
        ("Betting", "Odds & value analysis", "active"),
        ("News", "Media coverage", "active"),
        ("Social", "Reddit sentiment", "active"),
    ]
    for name, desc, status in servers:
        st.sidebar.markdown(
            f'''<div class="server-card {status}">
                   <div class="server-name">{name}</div>
                   <div class="server-status">● Online</div>
                   <div style="color:#808090;font-size:.8rem;margin-top:.25rem;">{desc}</div>
                </div>''',
            unsafe_allow_html=True
        )


def display_metrics():
    if not OBSERVABILITY_AVAILABLE:
        return
    monitor = get_monitor()
    stats = monitor.get_stats()
    st.sidebar.markdown('<div class="section-header">Performance</div>', unsafe_allow_html=True)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(
            f'''<div style="text-align:center;padding:.75rem;background:rgba(20,20,25,.98);border-radius:8px;border:1px solid rgba(60,60,70,.4);">
                    <div style="font-size:1.5rem;font-weight:700;">{stats['total_queries']}</div>
                    <div style="font-size:.8rem;">Queries</div>
                </div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(
            f'''<div style="text-align:center;padding:.75rem;background:rgba(20,20,25,.98);border-radius:8px;border:1px solid rgba(60,60,70,.4);">
                    <div style="font-size:1.5rem;font-weight:700;">{stats['total_tool_calls']}</div>
                    <div style="font-size:.8rem;">Tool Calls</div>
                </div>''', unsafe_allow_html=True)
    if stats['tool_breakdown']:
        st.sidebar.markdown('<div style="margin-top:1rem;color:#909099;font-size:.85rem;font-weight:600;">Most Used Tools</div>', unsafe_allow_html=True)
        for tool, metrics in sorted(stats['tool_breakdown'].items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
            st.sidebar.markdown(f'<div style="color:#707080;font-size:.8rem;margin:.25rem 0;">● {tool}: {metrics["count"]}</div>', unsafe_allow_html=True)


async def process_query(query: str, agent, tool_map):
    start_time = time.time()
    if OBSERVABILITY_AVAILABLE:
        get_monitor().log_query(query)

    msgs = [HumanMessage(content=query)]
    tool_calls = []
    iteration, max_iterations = 0, 10

    with st.spinner("Analyzing..."):
        while iteration < max_iterations:
            iteration += 1
            resp = await agent.ainvoke(msgs)
            msgs.append(resp)
            if hasattr(resp, "tool_calls") and resp.tool_calls:
                for tc in resp.tool_calls:
                    tool_name = tc["name"]
                    args = tc["args"]
                    t0 = time.time()
                    tool = tool_map.get(tool_name)
                    result = await tool.ainvoke(args) if tool else f"Error: Tool {tool_name} not found"
                    dt_ms = (time.time() - t0) * 1000
                    tool_calls.append({
                        "name": tool_name,
                        "duration_ms": dt_ms,
                        "server": get_server_for_tool(tool_name),
                    })
                    if OBSERVABILITY_AVAILABLE:
                        get_monitor().log_tool_call(tool_name, dt_ms)
                    msgs.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            else:
                break

    return resp.content, tool_calls, (time.time() - start_time)


def get_server_for_tool(tool_name: str) -> str:
    if any(x in tool_name for x in ['fighter','stats','compare','career','upcoming','trajectory','opponent','title']): return "Analytics"
    if any(x in tool_name for x in ['odds','betting','value','predict']): return "Betting"
    if any(x in tool_name for x in ['news','hype','media','press']) and 'reddit' not in tool_name.lower(): return "News"
    if any(x in tool_name for x in ['reddit','posts','buzz','sentiment','mentions']): return "Social"
    return "Unknown"


# --- Examples helpers ---
def _set_query_from_example(text: str, input_key: str):
    # pre-seed the current input widget (created later) before it mounts
    st.session_state[input_key] = text

EXAMPLES = [
    "Compare Tyson Fury vs Oleksandr Usyk - who has the advantage?",
    "Give me a complete breakdown of Gervonta Davis's career and fighting style",
    "Is Devin Haney's career on an upward or downward trajectory?",
    "What are the betting odds for upcoming heavyweight fights and where's the best value?",
    "Based on their stats and betting odds, predict the outcome of Fury vs Usyk",
    "Should I bet on Crawford in his next fight based on historical performance?",
    "What's the latest boxing news and which fights are generating the most hype?",
    "What is the boxing community on Reddit saying about Canelo?",
]

def render_example_cards(input_key: str):
    st.markdown('<div class="examples-wrap examples-sticky">', unsafe_allow_html=True)
    st.markdown('<div class="examples-title">Examples</div>', unsafe_allow_html=True)
    for i, q in enumerate(EXAMPLES):
        st.button(
            q, key=f"example_{i}", use_container_width=True,
            on_click=_set_query_from_example, args=(q, input_key)
        )
    st.markdown('</div>', unsafe_allow_html=True)


# -------------------- Main App --------------------
def show_main_app():
    inject_main_css()


    # chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # seed to force remount of the input after submit
    if "input_seed" not in st.session_state:
        st.session_state["input_seed"] = 0
    current_key = f"query_input_chat_{st.session_state['input_seed']}"

    display_server_status()
    display_metrics()

    st.sidebar.markdown("---")
    if st.sidebar.button("Clear History", use_container_width=True):
        st.session_state["chat_history"] = []
        if OBSERVABILITY_AVAILABLE:
            reset_monitor()
        st.rerun()

    # init platform
    try:
        with st.spinner("Initializing platform..."):
            agent, tools, tool_map, _client = initialize_platform()
        st.sidebar.markdown(
            f'<div style="text-align:center;margin-top:1rem;padding:.5rem;background:rgba(0,208,132,.1);border-radius:8px;color:#00D084;font-size:.85rem;">{len(tools)} tools loaded</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Failed to initialize platform: {e}")
        st.info("Make sure all environment variables are set:\n- ANTHROPIC_API_KEY")
        return

    show_hero = len(st.session_state["chat_history"]) == 0
    if show_hero:
        st.markdown('<div class="hero-section">', unsafe_allow_html=True)
        st.markdown('<h1 class="main-header">BOXONOMICS</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Deploy AI-powered boxing intelligence by chatting with specialized MCP servers</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # two-column layout: left examples, right chat
    left, right = st.columns([2, 6], gap="large")

    with left:
        render_example_cards(input_key=current_key)


    with right:
        st.markdown('<div class="chat-area">', unsafe_allow_html=True)

        # --- conversation history ---
        if st.session_state["chat_history"]:
            st.markdown("---")
            for msg in st.session_state["chat_history"]:
                if msg["role"] == "user":
                    st.markdown(
                        f'''<div class="chat-message user-message">
                                <div class="message-role">You</div>
                                <div class="message-content">{msg["content"]}</div>
                            </div>''',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'''<div class="chat-message assistant-message">
                                <div class="message-role">Boxonomics AI</div>
                                <div class="message-content">{msg["content"]}</div>
                            </div>''',
                        unsafe_allow_html=True,
                    )
                    if msg.get("tool_calls"):
                        with st.expander(f"Tool Usage ({len(msg['tool_calls'])} calls)"):
                            for tc in msg["tool_calls"]:
                                st.markdown(
                                    f'''<div class="tool-call">
                                            <span class="tool-server">[{tc["server"]}]</span>
                                            <span class="tool-name">{tc["name"]}</span>
                                            <span class="tool-duration">({tc["duration_ms"]:.0f}ms)</span>
                                        </div>''',
                                    unsafe_allow_html=True,
                                )
                    if "duration" in msg:
                        st.caption(f"Response time: {msg['duration']:.2f}s")

        # --- input row under messages ---
        st.markdown('<div class="chat-input-section">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1.4])

        with c1:
            query = st.text_input(
                "Query",
                placeholder="Ask about fighters, odds, news, or community sentiment...",
                key=current_key,                    # <-- dynamic key mounts a fresh widget each time
                label_visibility="collapsed",
            )
        with c2:
            submit = st.button("ANALYZE", type="primary")

        if submit:
            q = st.session_state.get(current_key, "").strip()
            if q:
                # append user
                st.session_state["chat_history"].append({"role": "user", "content": q})
                try:
                    response, tool_calls, duration = asyncio.run(
                        process_query(q, agent, tool_map)
                    )
                    st.session_state["chat_history"].append({
                        "role": "assistant",
                        "content": response,
                        "tool_calls": tool_calls,
                        "duration": duration,
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

            # force the input to remount blank on next run
            st.session_state["input_seed"] += 1
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if not show_hero:
        st.markdown("---")
    st.markdown(
        '''<div class="footer">
            Boxonomics | Powered by LangChain, MCP &amp; Claude Sonnet 4<br>
            4 Specialized Servers | 25+ Intelligence Tools
        </div>''',
        unsafe_allow_html=True,
    )


def main():
    if "show_splash" not in st.session_state:
        st.session_state["show_splash"] = True
    if st.session_state["show_splash"]:
        show_splash_page()
    else:
        show_main_app()


if __name__ == "__main__":
    main()
