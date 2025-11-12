#!/usr/bin/env python3
"""
Boxonomics - Boxing Intelligence Platform
Zeabur-inspired design with gradient background and dark cards
"""

import streamlit as st
import asyncio
import time
import os
import base64
from datetime import datetime
from pathlib import Path
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
except ImportError:
    OBSERVABILITY_AVAILABLE = False


# Page configuration
st.set_page_config(
    page_title="Boxonomics",
    page_icon="🥊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def get_base64_image(image_path):
    """Convert image to base64 for CSS background."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None


# Simplified Splash Page Styles
def inject_splash_css(bg_image_base64=None):
    """Inject CSS for sleek, minimal splash page."""
    
    # Background image or fallback gradient
    if bg_image_base64:
        background = f"""
            background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.6)),
                        url(data:image/png;base64,{bg_image_base64});
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        background = """
            background: linear-gradient(135deg, #0A0E27 0%, #1A1F3A 100%);
        """
    
    st.markdown(f"""
    <style>
        /* Remove ALL Streamlit default styling and chrome */
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        header,
        footer {{
            display: none !important;
        }}
        
        /* Force full-screen dark background */
        .stApp {{
            background-color: #000000 !important;
            overflow: hidden;
        }}
        
        .main {{
            padding: 0 !important;
            background-color: transparent !important;
        }}
        
        /* Remove ALL default padding/margins */
        .block-container {{
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }}
        
        .element-container {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        
        div[data-testid="column"] {{
            padding: 0 !important;
        }}
        
        /* Splash Container */
        .splash-container {{
            {background}
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-start;
            padding-left: 8%;
            margin: 0;
            z-index: 1;
        }}
        
        /* Content Wrapper */
        .splash-content {{
            max-width: 700px;
            text-align: left;
        }}
        
        /* Logo/Title */
        .splash-logo {{
            font-size: 7rem;
            font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 50%, #8B0000 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1.5rem;
            letter-spacing: -2px;
            animation: fadeInLeft 0.8s ease-out;
            text-transform: uppercase;
        }}
        
        /* Tagline */
        .splash-tagline {{
            font-size: 1.4rem;
            color: #D0D3DC;
            margin-bottom: 2.5rem;
            font-weight: 300;
            animation: fadeInLeft 1s ease-out;
            line-height: 1.6;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes fadeInLeft {{
            from {{
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{
                box-shadow: 0 8px 25px rgba(255, 59, 59, 0.4);
            }}
            50% {{
                box-shadow: 0 8px 35px rgba(255, 59, 59, 0.7);
            }}
        }}
    </style>
    """, unsafe_allow_html=True)


def show_splash_page():
    """Display the simplified splash/landing page."""
    
    # Try to load the background image
    bg_image_path = "frontend/assets/splash_bg.png"
    bg_image_base64 = get_base64_image(bg_image_path)
    
    # Inject splash CSS
    inject_splash_css(bg_image_base64)
    
    # Splash content
    st.markdown("""
    <div class="splash-container">
        <div class="splash-content">
            <div class="splash-logo">BOXONOMICS</div>
            <div class="splash-tagline">AI-Powered Boxing Intelligence & Analysis Platform</div>
        </div>
    </div>
    
    <style>
        /* Position Start button below description */
        .stButton {
            position: fixed !important;
            left: 8% !important;
            top: 65% !important;
            z-index: 999999 !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 100%) !important;
            color: white !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            padding: 0.75rem 2.75rem !important;
            border: none !important;
            border-radius: 50px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 25px rgba(255, 59, 59, 0.4) !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            animation: fadeInUp 1.5s ease-out, pulse 2s ease-in-out 2s infinite !important;
            min-width: auto !important;
            width: auto !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #B71C1C 0%, #FF3B3B 100%) !important;
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 35px rgba(255, 59, 59, 0.6) !important;
        }
        
        .stButton > button:focus,
        .stButton > button:active {
            background: linear-gradient(135deg, #B71C1C 0%, #FF3B3B 100%) !important;
            box-shadow: 0 6px 20px rgba(255, 59, 59, 0.5) !important;
            outline: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Functional Start button
    if st.button("Get in the Ring", key="start_btn"):
        st.session_state.show_splash = False
        st.rerun()


# Main App CSS (Zeabur-inspired with gradient background)
def inject_main_css():
    """Inject CSS for main chatbot interface - Zeabur style with gradient background."""
    st.markdown("""
<style>
    /* Global Styles - Gradient Background like Zeabur */
    .stApp {
        background: linear-gradient(135deg, #1A0F1F 0%, #0A0E27 25%, #1A1030 50%, #0A0E27 75%, #1A0F1F 100%);
        background-attachment: fixed;
    }
    
    /* Main Container */
    .main {
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Hero Section */
    .hero-section {
        max-width: 1200px;
        margin: 0 auto;
        padding: 3rem 2rem 2rem 2rem;
        text-align: center;
    }
    
    /* Main Header - Match Splash Page Typography */
    .main-header {
        font-size: 4rem;
        font-weight: 400;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Helvetica Neue', Arial, sans-serif;
        text-align: center;
        background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 50%, #8B0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
        letter-spacing: -2px;
        text-transform: uppercase;
    }
    
    .sub-header {
        text-align: center;
        color: #C0C0D0;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        font-weight: 300;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    
    /* Chat Input Container - Above Cards */
    .chat-input-section {
        max-width: 1000px;
        margin: 0 auto 3rem auto;
        padding: 0 2rem;
    }
    
    /* Input styling - Darker background with better contrast */
    .stTextInput > div > div > input {
        background: rgba(30, 30, 45, 0.9) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1.2rem 1.6rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        background: rgba(35, 35, 50, 1) !important;
        box-shadow: 0 0 0 2px rgba(255, 59, 59, 0.4) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #808090 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #FF3B3B 0%, #B71C1C 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 1.2rem 2.5rem !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        box-shadow: 0 4px 12px rgba(255, 59, 59, 0.35) !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #B71C1C 0%, #FF3B3B 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 59, 59, 0.5) !important;
    }
    
    /* Chat Messages - More opaque for better visibility */
    .chat-message {
        padding: 1.75rem;
        border-radius: 16px;
        margin: 1.5rem auto;
        max-width: 1000px;
        background: rgba(25, 25, 40, 0.95);
        border: 1px solid rgba(80, 80, 100, 0.5);
        backdrop-filter: blur(10px);
    }
    
    .user-message {
        border-left: 3px solid #4A9EFF;
    }
    
    .assistant-message {
        border-left: 3px solid #FF3B3B;
    }
    
    .message-role {
        font-weight: 600;
        font-size: 0.85rem;
        color: #B0B0C0;
        margin-bottom: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    
    .message-content {
        color: #FFFFFF;
        line-height: 1.8;
        font-size: 1.05rem;
    }
    
    /* Tool Calls */
    .tool-call {
        background: rgba(139, 0, 0, 0.2);
        border: 1px solid rgba(255, 59, 59, 0.4);
        border-radius: 10px;
        padding: 0.85rem;
        margin: 0.6rem 0;
        font-size: 0.9rem;
        color: #FFFFFF;
    }
    
    .tool-name {
        color: #FF6B6B;
        font-weight: 600;
    }
    
    .tool-server {
        color: #B0B0C0;
        font-size: 0.85rem;
    }
    
    .tool-duration {
        color: #00D084;
        font-weight: 500;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F1219 0%, #1A0F1F 100%);
        border-right: 1px solid rgba(80, 80, 100, 0.3);
    }
    
    /* Server Status Cards - More opaque */
    .server-card {
        background: rgba(25, 25, 40, 0.95);
        border: 1px solid rgba(80, 80, 100, 0.5);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    
    .server-card:hover {
        border-color: rgba(255, 59, 59, 0.7);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 59, 59, 0.25);
    }
    
    .server-card.active {
        border-left: 3px solid #FF3B3B;
    }
    
    .server-name {
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    
    .server-status {
        color: #00D084;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    /* Section Headers */
    .section-header {
        color: #FF3B3B;
        font-size: 1rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Divider */
    hr {
        border-color: rgba(80, 80, 100, 0.3);
        margin: 2rem 0;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #707080;
        font-size: 0.9rem;
        margin-top: 4rem;
        padding: 2rem;
        border-top: 1px solid rgba(80, 80, 100, 0.3);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0A0E27;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(183, 28, 28, 0.5);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #B71C1C;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_platform():
    """Initialize the MCP client and agent (cached)."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Configure all FOUR boxing servers
    server_config = {
        "boxing_analytics": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_data.py")],
        },
        "betting_odds": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_odds.py")],
        },
        "fight_news": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_news.py")],
        },
        "reddit_social": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "reddit.py")],
        }
    }
    
    # Create MCP client
    client = MultiServerMCPClient(server_config)
    
    # Run async initialization
    async def async_init():
        tools = await client.get_tools()
        return tools
    
    tools = asyncio.run(async_init())
    
    # Create agent with all tools
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    agent = llm.bind_tools(tools)
    
    # Create tool map
    tool_map = {tool.name: tool for tool in tools}
    
    return agent, tools, tool_map, client


def display_server_status():
    """Display status of all four servers with modern cards."""
    st.sidebar.markdown('<div class="section-header">Servers</div>', unsafe_allow_html=True)
    
    servers = [
        ("Analytics", "Fighter stats & history", "active"),
        ("Betting", "Odds & value analysis", "active"),
        ("News", "Media coverage", "active"),
        ("Social", "Reddit sentiment", "active"),
    ]
    
    for name, description, status in servers:
        st.sidebar.markdown(
            f'''<div class="server-card {status}">
                <div class="server-name">{name}</div>
                <div class="server-status">● Online</div>
                <div style="color: #808090; font-size: 0.8rem; margin-top: 0.25rem;">{description}</div>
            </div>''',
            unsafe_allow_html=True
        )


def display_metrics():
    """Display performance metrics in modern cards."""
    if OBSERVABILITY_AVAILABLE:
        monitor = get_monitor()
        stats = monitor.get_stats()
        
        st.sidebar.markdown('<div class="section-header">Performance</div>', unsafe_allow_html=True)
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.markdown(
                f'''<div style="text-align: center; padding: 0.75rem; background: rgba(25, 25, 40, 0.95); border-radius: 8px; border: 1px solid rgba(80, 80, 100, 0.5);">
                    <div style="color: #FFFFFF; font-size: 1.5rem; font-weight: 700;">{stats['total_queries']}</div>
                    <div style="color: #B0B0C0; font-size: 0.8rem;">Queries</div>
                </div>''',
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f'''<div style="text-align: center; padding: 0.75rem; background: rgba(25, 25, 40, 0.95); border-radius: 8px; border: 1px solid rgba(80, 80, 100, 0.5);">
                    <div style="color: #FFFFFF; font-size: 1.5rem; font-weight: 700;">{stats['total_tool_calls']}</div>
                    <div style="color: #B0B0C0; font-size: 0.8rem;">Tool Calls</div>
                </div>''',
                unsafe_allow_html=True
            )
        
        if stats['tool_breakdown']:
            st.sidebar.markdown('<div style="margin-top: 1rem; color: #9CA3AF; font-size: 0.85rem; font-weight: 600;">Most Used Tools</div>', unsafe_allow_html=True)
            sorted_tools = sorted(
                stats['tool_breakdown'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5]
            
            for tool, metrics in sorted_tools:
                st.sidebar.markdown(
                    f'<div style="color: #707080; font-size: 0.8rem; margin: 0.25rem 0;">● {tool}: {metrics["count"]}</div>',
                    unsafe_allow_html=True
                )


async def process_query(query: str, agent, tool_map):
    """Process a user query through the agent."""
    
    start_time = time.time()
    
    if OBSERVABILITY_AVAILABLE:
        monitor = get_monitor()
        monitor.log_query(query)
    
    messages = [HumanMessage(content=query)]
    all_tool_calls = []
    
    iteration = 0
    max_iterations = 10
    
    with st.spinner("Analyzing..."):
        while iteration < max_iterations:
            iteration += 1
            
            response = await agent.ainvoke(messages)
            messages.append(response)
            
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    tool_start = time.time()
                    
                    tool = tool_map.get(tool_name)
                    if tool:
                        result = await tool.ainvoke(tool_args)
                    else:
                        result = f"Error: Tool {tool_name} not found"
                    
                    tool_duration = (time.time() - tool_start) * 1000
                    
                    all_tool_calls.append({
                        "name": tool_name,
                        "duration_ms": tool_duration,
                        "server": get_server_for_tool(tool_name)
                    })
                    
                    if OBSERVABILITY_AVAILABLE:
                        monitor.log_tool_call(tool_name, tool_duration)
                    
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call['id']
                    ))
            else:
                break
    
    total_duration = time.time() - start_time
    
    return response.content, all_tool_calls, total_duration


def get_server_for_tool(tool_name: str) -> str:
    """Determine which server a tool belongs to."""
    if any(x in tool_name for x in ['fighter', 'stats', 'compare', 'career', 'upcoming', 'trajectory', 'opponent', 'title']):
        return "Analytics"
    elif any(x in tool_name for x in ['odds', 'betting', 'value', 'predict']):
        return "Betting"
    elif any(x in tool_name for x in ['news', 'hype', 'media', 'press']) and 'reddit' not in tool_name.lower():
        return "News"
    elif any(x in tool_name for x in ['reddit', 'posts', 'buzz', 'sentiment', 'mentions']):
        return "Social"
    else:
        return "Unknown"


def show_main_app():
    """Display the main chatbot interface with Zeabur-inspired design."""
    
    inject_main_css()
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar
    display_server_status()
    display_metrics()
    
    # Add clear history button
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear History", use_container_width=True):
        st.session_state.chat_history = []
        if OBSERVABILITY_AVAILABLE:
            reset_monitor()
        st.rerun()
    
    # Initialize platform
    try:
        with st.spinner("Initializing platform..."):
            agent, tools, tool_map, client = initialize_platform()
        
        st.sidebar.markdown(
            f'<div style="text-align: center; margin-top: 1rem; padding: 0.5rem; background: rgba(0, 208, 132, 0.1); border-radius: 8px; color: #00D084; font-size: 0.85rem;">{len(tools)} tools loaded</div>',
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Failed to initialize platform: {e}")
        st.info("Make sure all environment variables are set:\n- ANTHROPIC_API_KEY")
        return
    
    # Show hero section if no chat history
    show_hero = len(st.session_state.chat_history) == 0
    
    if show_hero:
        # Header
        st.markdown('<div class="hero-section">', unsafe_allow_html=True)
        st.markdown('<h1 class="main-header">BOXONOMICS</h1>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sub-header">Deploy AI-powered boxing intelligence by chatting with specialized MCP servers</p>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Chat input
        st.markdown('<div class="chat-input-section">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "Query",
                value="",
                placeholder="Ask about fighters, odds, news, or community sentiment...",
                key="query_input",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.button("ANALYZE", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        # Chat mode - input at top
        col1, col2 = st.columns([5, 1])
        
        with col1:
            query = st.text_input(
                "Query",
                value="",
                placeholder="Ask about fighters, odds, news, or community sentiment...",
                key="query_input_chat",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.button("ANALYZE", type="primary", use_container_width=True)
    
    # Process query
    if 'submit' in locals() and submit and query:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': query
        })
        
        try:
            response, tool_calls, duration = asyncio.run(
                process_query(query, agent, tool_map)
            )
            
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'tool_calls': tool_calls,
                'duration': duration
            })
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(
                    f'''<div class="chat-message user-message">
                        <div class="message-role">You</div>
                        <div class="message-content">{msg["content"]}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'''<div class="chat-message assistant-message">
                        <div class="message-role">Boxonomics AI</div>
                        <div class="message-content">{msg["content"]}</div>
                    </div>''',
                    unsafe_allow_html=True
                )
                
                if 'tool_calls' in msg and msg['tool_calls']:
                    with st.expander(f"Tool Usage ({len(msg['tool_calls'])} calls)"):
                        for tc in msg['tool_calls']:
                            st.markdown(
                                f'''<div class="tool-call">
                                    <span class="tool-server">[{tc["server"]}]</span> 
                                    <span class="tool-name">{tc["name"]}</span> 
                                    <span class="tool-duration">({tc["duration_ms"]:.0f}ms)</span>
                                </div>''',
                                unsafe_allow_html=True
                            )
                
                if 'duration' in msg:
                    st.caption(f"Response time: {msg['duration']:.2f}s")
    
    # Footer
    if not show_hero:
        st.markdown("---")
    st.markdown(
        '''<div class="footer">
            Boxonomics | Powered by LangChain, MCP & Claude Sonnet 4<br>
            4 Specialized Servers | 25+ Intelligence Tools
        </div>''',
        unsafe_allow_html=True
    )


def main():
    """Main application entry point."""
    
    # Initialize session state for splash
    if 'show_splash' not in st.session_state:
        st.session_state.show_splash = True
    
    # Show splash or main app
    if st.session_state.show_splash:
        show_splash_page()
    else:
        show_main_app()


if __name__ == "__main__":
    main()