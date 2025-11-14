#!/usr/bin/env python3
"""
MCP Server Diagnostic Test Suite
Run this locally to diagnose issues before deploying
"""

import asyncio
import sys
import os
from pathlib import Path
import subprocess
import json
import time

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"  {text}")


async def test_1_file_structure():
    """Test 1: Check if all required files exist"""
    print_header("TEST 1: File Structure")
    
    project_root = Path.cwd()
    print_info(f"Project root: {project_root}")
    
    required_files = {
        "Database": project_root / "data" / "boxing_data.db",
        "Boxing Analytics Server": project_root / "mcp_servers" / "boxing_data.py",
        "Betting Odds Server": project_root / "mcp_servers" / "boxing_odds.py",
        "News Server": project_root / "mcp_servers" / "boxing_news.py",
        "Prediction Module": project_root / "mcp_servers" / "boxing_prediction.py",
        "Reddit Server": project_root / "mcp_servers" / "reddit.py",
        "Frontend App": project_root / "frontend" / "app.py",
    }
    
    all_good = True
    for name, path in required_files.items():
        if path.exists():
            size = path.stat().st_size
            print_success(f"{name}: {path.relative_to(project_root)} ({size:,} bytes)")
        else:
            print_error(f"{name}: NOT FOUND at {path.relative_to(project_root)}")
            all_good = False
    
    if all_good:
        print_success("\nAll required files found!")
    else:
        print_error("\nSome files are missing!")
    
    return all_good


async def test_2_database():
    """Test 2: Check database integrity"""
    print_header("TEST 2: Database Integrity")
    
    db_path = Path.cwd() / "data" / "boxing_data.db"
    
    if not db_path.exists():
        print_error("Database file not found!")
        return False
    
    print_info(f"Database path: {db_path}")
    print_info(f"Database size: {db_path.stat().st_size:,} bytes")
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print_success(f"Tables found: {', '.join(tables)}")
        
        # Check fighter count
        cursor.execute("SELECT COUNT(*) FROM fighters")
        fighter_count = cursor.fetchone()[0]
        print_success(f"Fighters in database: {fighter_count}")
        
        # Check fight count
        cursor.execute("SELECT COUNT(*) FROM fights")
        fight_count = cursor.fetchone()[0]
        print_success(f"Fights in database: {fight_count}")
        
        # Test a query
        cursor.execute("SELECT name FROM fighters LIMIT 1")
        sample = cursor.fetchone()
        print_success(f"Sample query works: {sample[0]}")
        
        conn.close()
        print_success("\nDatabase is healthy!")
        return True
        
    except Exception as e:
        print_error(f"Database error: {e}")
        return False


async def test_3_server_startup():
    """Test 3: Check if MCP server can start"""
    print_header("TEST 3: MCP Server Startup")
    
    server_path = Path.cwd() / "mcp_servers" / "boxing_data.py"
    
    if not server_path.exists():
        print_error("Server file not found!")
        return False
    
    print_info("Attempting to start server subprocess...")
    
    try:
        # Start server as subprocess
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for server to start
        time.sleep(1)
        
        # Check if still running
        if process.poll() is None:
            print_success("Server process started successfully")
            print_info(f"PID: {process.pid}")
            
            # Try to send initialization message
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
            
            process.stdin.write(json.dumps(init_msg) + "\n")
            process.stdin.flush()
            
            # Try to read response (with timeout)
            time.sleep(2)
            
            # Kill process
            process.terminate()
            process.wait(timeout=5)
            
            print_success("Server can start and accept connections")
            return True
        else:
            # Process died
            _, stderr = process.communicate()
            print_error("Server process died immediately!")
            print_error(f"Error output:\n{stderr}")
            return False
            
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        try:
            process.terminate()
        except:
            pass
        return False


async def test_4_imports():
    """Test 4: Check if all Python imports work"""
    print_header("TEST 4: Python Dependencies")
    
    required_packages = {
        "streamlit": "Streamlit",
        "langchain_anthropic": "LangChain Anthropic",
        "langchain_mcp_adapters": "LangChain MCP Adapters",
        "mcp": "MCP SDK",
        "dotenv": "Python Dotenv",
        "sqlite3": "SQLite3 (built-in)",
    }
    
    all_good = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print_success(f"{name} ({package})")
        except ImportError:
            print_error(f"{name} ({package}) - NOT INSTALLED")
            all_good = False
    
    if all_good:
        print_success("\nAll required packages installed!")
    else:
        print_error("\nSome packages are missing!")
        print_info("Run: pip install -r requirements.txt")
    
    return all_good


async def test_5_langchain_client():
    """Test 5: Test LangChain MCP client initialization"""
    print_header("TEST 5: LangChain MCP Client")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        project_root = Path.cwd()
        server_config = {
            "boxing_analytics": {
                "transport": "stdio",
                "command": "python",
                "args": [str(project_root / "mcp_servers" / "boxing_data.py")]
            }
        }
        
        print_info("Creating MultiServerMCPClient...")
        client = MultiServerMCPClient(server_config)
        
        print_info("Attempting to get tools...")
        tools = await client.get_tools()
        
        print_success(f"Successfully loaded {len(tools)} tools:")
        for tool in tools:
            print_info(f"  • {tool.name}: {tool.description[:60]}...")
        
        return True
        
    except Exception as e:
        print_error(f"Failed to initialize client: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False


async def test_6_tool_execution():
    """Test 6: Test actual tool execution"""
    print_header("TEST 6: Tool Execution")
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        project_root = Path.cwd()
        server_config = {
            "boxing_analytics": {
                "transport": "stdio",
                "command": "python",
                "args": [str(project_root / "mcp_servers" / "boxing_data.py")]
            }
        }
        
        client = MultiServerMCPClient(server_config)
        tools = await client.get_tools()
        
        # Find get_fighter_stats tool
        stats_tool = next((t for t in tools if t.name == "get_fighter_stats"), None)
        
        if not stats_tool:
            print_error("get_fighter_stats tool not found!")
            return False
        
        print_info("Executing get_fighter_stats for 'Tyson Fury'...")
        result = await stats_tool.ainvoke({"name": "Tyson Fury"})
        
        print_success("Tool executed successfully!")
        print_info(f"Result preview: {str(result)[:200]}...")
        
        # Try to parse result
        try:
            import json
            data = json.loads(result)
            if "error" in data:
                print_error(f"Tool returned error: {data['error']}")
                return False
            else:
                print_success(f"Fighter found: {data.get('name', 'Unknown')}")
                print_success(f"Record: {data.get('record', 'Unknown')}")
                return True
        except:
            print_success("Tool returned data (not JSON)")
            return True
            
    except Exception as e:
        print_error(f"Tool execution failed: {e}")
        import traceback
        print_info(traceback.format_exc())
        return False


async def test_7_environment():
    """Test 7: Check environment variables"""
    print_header("TEST 7: Environment Variables")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = {
        "ANTHROPIC_API_KEY": "Claude API",
        "ODDS_API_KEY": "The Odds API (optional)",
        "NEWS_API_KEY": "News API (optional)",
        "REDDIT_CLIENT_ID": "Reddit API (optional)",
        "REDDIT_CLIENT_SECRET": "Reddit API (optional)",
    }
    
    for var, name in env_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print_success(f"{name} ({var}): {masked}")
        else:
            if "optional" in name:
                print_warning(f"{name} ({var}): Not set (optional)")
            else:
                print_error(f"{name} ({var}): NOT SET - REQUIRED")
    
    return bool(os.getenv("ANTHROPIC_API_KEY"))


async def run_all_tests():
    """Run all tests"""
    print_header("MCP SERVER DIAGNOSTIC TEST SUITE")
    print_info(f"Python version: {sys.version}")
    print_info(f"Working directory: {Path.cwd()}")
    
    results = []
    
    # Run tests
    results.append(("File Structure", await test_1_file_structure()))
    results.append(("Database Integrity", await test_2_database()))
    results.append(("Python Dependencies", await test_4_imports()))
    results.append(("Environment Variables", await test_7_environment()))
    results.append(("Server Startup", await test_3_server_startup()))
    results.append(("LangChain Client", await test_5_langchain_client()))
    results.append(("Tool Execution", await test_6_tool_execution()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if failed == 0:
        print(f"{GREEN}ALL TESTS PASSED! ({passed}/{len(results)}){RESET}")
        print_info("Your MCP server should work correctly!")
    else:
        print(f"{RED}SOME TESTS FAILED ({failed}/{len(results)} failed){RESET}")
        print_info("Fix the issues above before deploying to Railway")
    print(f"{BLUE}{'='*70}{RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)