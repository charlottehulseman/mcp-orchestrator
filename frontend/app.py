#!/usr/bin/env python3
"""
Boxonomics - DIAGNOSTIC VERSION
Tests one server at a time to find the issue
"""

import streamlit as st
import asyncio
import time
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(str(Path(__file__).parent.parent))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, ToolMessage

st.set_page_config(page_title="Boxonomics - Diagnostic", page_icon="🥊", layout="wide")

st.title("🥊 Boxonomics - Diagnostic Mode")
st.markdown("---")

# Show environment status
st.subheader("Environment Variables")
env_vars = {
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    "ODDS_API_KEY": os.getenv("ODDS_API_KEY"),
    "NEWS_API_KEY": os.getenv("NEWS_API_KEY"),
    "REDDIT_CLIENT_ID": os.getenv("REDDIT_CLIENT_ID"),
}

for key, value in env_vars.items():
    if value:
        st.success(f"✅ {key} is set ({value[:10]}...)")
    else:
        st.warning(f"⚠️ {key} is NOT set")

st.markdown("---")

# Test file paths
st.subheader("File System Check")
project_root = Path(__file__).parent.parent

st.info(f"Project root: `{project_root}`")
st.info(f"Current working directory: `{Path.cwd()}`")

# Check for database
db_path = project_root / "data" / "boxing_data.db"
if db_path.exists():
    size_kb = db_path.stat().st_size / 1024
    st.success(f"✅ Database found: `{db_path}` ({size_kb:.2f} KB)")
else:
    st.error(f"❌ Database NOT found at: `{db_path}`")
    
    # Try to find it
    st.info("Searching for database...")
    for path in [
        Path.cwd() / "data" / "boxing_data.db",
        Path("/mount/src/mcp-orchestrator/data/boxing_data.db"),
        Path(__file__).parent / "data" / "boxing_data.db",
    ]:
        if path.exists():
            st.info(f"Found at: `{path}`")
        else:
            st.warning(f"Not at: `{path}`")

# Check MCP server files
st.markdown("---")
st.subheader("MCP Server Files")
server_files = [
    "mcp_servers/boxing_data.py",
    "mcp_servers/boxing_odds.py",
    "mcp_servers/boxing_news.py",
    "mcp_servers/reddit.py",
]

for server_file in server_files:
    server_path = project_root / server_file
    if server_path.exists():
        st.success(f"✅ Found: `{server_file}`")
    else:
        st.error(f"❌ Missing: `{server_file}`")

st.markdown("---")

# Test ONE server initialization
st.subheader("Testing Boxing Analytics Server")

@st.cache_resource
def test_single_server():
    """Test just the analytics server"""
    server_config = {
        "boxing_analytics": {
            "transport": "stdio",
            "command": "python",
            "args": [str(project_root / "mcp_servers" / "boxing_data.py")]
        }
    }
    
    try:
        st.info("Creating MCP client...")
        client = MultiServerMCPClient(server_config)
        
        st.info("Getting tools from server...")
        
        async def async_init():
            return await client.get_tools()
        
        tools = asyncio.run(async_init())
        
        if tools:
            st.success(f"✅ Server initialized successfully! Loaded {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                st.write(f"  - {tool.name}")
            if len(tools) > 5:
                st.write(f"  ... and {len(tools) - 5} more")
            return True, tools
        else:
            st.error("❌ Server returned no tools")
            return False, None
            
    except Exception as e:
        st.error(f"❌ Server failed to initialize:")
        st.error(f"Error: {e}")
        
        import traceback
        st.code(traceback.format_exc())
        
        return False, None

if st.button("🔍 Test Server Initialization", type="primary"):
    st.cache_resource.clear()
    with st.spinner("Testing..."):
        success, tools = test_single_server()
    
    if success:
        st.success("🎉 Server works! The issue is likely with one of the OTHER servers.")
        st.info("Next steps: Test betting, news, and reddit servers individually")
    else:
        st.error("Server failed. Check the error details above.")

st.markdown("---")
st.subheader("Recommendations")

st.markdown("""
**If database is missing:**
1. Check `.gitignore` - make sure `data/boxing_data.db` is NOT ignored
2. Run: `git add -f data/boxing_data.db`
3. Commit and push

**If server files are missing:**
1. Make sure `mcp_servers/` directory is in your repo
2. Commit and push all server files

**If environment variables are missing:**
1. Go to Streamlit Cloud → Settings → Secrets
2. Add missing keys in TOML format

**If server crashes:**
1. Check the error traceback above
2. Look for `ModuleNotFoundError` → missing dependency in requirements.txt
3. Look for `FileNotFoundError` → wrong file paths
4. Look for `KeyError` → missing API keys
""")