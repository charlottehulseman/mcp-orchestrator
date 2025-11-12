# LangChain MCP Integration Showcase

> A production-ready demonstration of integrating Model Context Protocol (MCP) servers with LangChain and LangGraph for intelligent agent orchestration.

## 🎯 Overview

This project showcases how to build a **multi-agent system** using:
- **3 custom MCP servers** with different transport types (stdio, SSE)
- **LangGraph orchestration** for intelligent tool selection
- **Production-grade patterns**: error handling, retries, circuit breakers
- **Full observability** with LangSmith tracing

[Include architecture diagram image]

## 🥊 What Makes This Unique?

Unlike typical weather/calculator demos, this project features:
- **Boxing Analytics Engine** - Statistical analysis of fighters, predictions, career timelines
- **GitHub Code Search** - Find relevant repositories and issues
- **Data Analysis** - SQL queries and visualizations

This combination demonstrates:
✅ Domain expertise integration
✅ Multiple transport types (stdio, SSE)
✅ Real-world data synthesis
✅ Production-ready error handling

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/langchain-mcp-boxing

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize databases
python scripts/init_databases.py

# Start MCP servers (in separate terminals)
python mcp_servers/boxing_server.py
python mcp_servers/github_server.py
python mcp_servers/data_server.py

# Run the CLI
python cli.py interactive
```

## 📐 Architecture

[Detailed architecture diagram]

### MCP Servers

#### 1. Boxing Analytics Server (stdio)
Provides comprehensive boxing data and analysis:
- `get_fighter_stats(name)` - Fighter records, KO rates, titles
- `compare_fighters(fighter1, fighter2)` - Statistical matchup analysis
- `upcoming_fights(date_range)` - Scheduled bouts with odds
- `fighter_career_timeline(name)` - Career progression analysis
- `search_fighters(query)` - Find fighters by criteria

**Data Sources:** TheSportsDB API + Custom SQLite database with 100+ fighters, 500+ historical fights

#### 2. GitHub Integration Server (SSE)
Developer-focused code search:
- `search_repos(query, language)` - Find repositories
- `get_repo_info(owner, repo)` - Detailed repo information
- `search_issues(repo, query)` - Issue and PR search
- `get_trending_repos(language)` - Trending projects

**Transport:** Server-Sent Events (SSE) for real-time updates

#### 3. Data Analysis Server (stdio)
SQL queries and visualizations:
- `execute_sql(query)` - Safe, read-only SQL execution
- `visualize_data(query, chart_type)` - Generate charts
- `get_schema(table)` - Database schema inspection
- `aggregate_stats(table, metric)` - Statistical aggregations

**Safety:** SQL injection protection, query timeouts, row limits

## 🎬 Demo Video

[Link to 5-minute demo video]

**Video Contents:**
1. Architecture overview (1 min)
2. Simple query demo (1 min)
3. Complex multi-tool workflow (1 min)
4. Code walkthrough (1 min)
5. Production features (1 min)

## 💪 Production Features

### Error Handling
- ✅ Exponential backoff retry logic
- ✅ Circuit breakers for failing services
- ✅ Graceful degradation with caching
- ✅ Comprehensive error messages

### Observability
- ✅ Full LangSmith tracing
- ✅ Per-tool performance metrics
- ✅ Health check endpoints
- ✅ Structured logging with structlog

### Resilience
- ✅ Timeout management (per-tool and global)
- ✅ Rate limit handling
- ✅ Connection retry logic
- ✅ Cache-first strategies

## 📊 Example Queries
```python
# Fighter analysis
"Tell me about Muhammad Ali's career"

# Head-to-head comparison
"Who would win: Muhammad Ali vs Mike Tyson? Give me a statistical analysis."

# Multi-domain query
"Find me Python boxing prediction models on GitHub and show me knockout factors in my data"

# Data analysis
"Show me a chart of knockout rates by weight class"
```

## 🏗️ Project Structure