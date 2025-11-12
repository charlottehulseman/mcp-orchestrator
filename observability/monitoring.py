"""
Observability & Monitoring Module

Integrates LangSmith for production observability, tracking, and debugging.
Provides utilities for monitoring tool calls, latency, and errors.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime


def setup_langsmith():
    """
    Setup LangSmith observability for the Boxing Intelligence Platform.
    
    Environment Variables Required:
        LANGCHAIN_TRACING_V2: Set to "true" to enable tracing
        LANGCHAIN_API_KEY: Your LangSmith API key
        LANGCHAIN_PROJECT: Project name (default: "Boxing-Intelligence-Platform")
    
    Returns:
        bool: True if LangSmith is configured, False otherwise
    """
    langsmith_configured = bool(
        os.getenv("LANGCHAIN_TRACING_V2") == "true" and
        os.getenv("LANGCHAIN_API_KEY")
    )
    
    if langsmith_configured:
        project = os.getenv("LANGCHAIN_PROJECT", "Boxing-Intelligence-Platform")
        print(f"📊 LangSmith observability enabled")
        print(f"   Project: {project}")
        print(f"   Dashboard: https://smith.langchain.com/o/{get_org_id()}/projects/p/{project}")
        return True
    else:
        print("⚠️  LangSmith not configured (optional)")
        print("   To enable: export LANGCHAIN_TRACING_V2=true")
        print("   And: export LANGCHAIN_API_KEY='your_key'")
        return False


def get_org_id() -> str:
    """Get LangSmith organization ID from environment or return placeholder."""
    return os.getenv("LANGCHAIN_ORG_ID", "your-org")


class PerformanceMonitor:
    """Monitor and log performance metrics for tool calls and queries."""
    
    def __init__(self):
        self.query_count = 0
        self.tool_calls = {}
        self.errors = []
        self.start_time = datetime.now()
    
    def log_query(self, query: str):
        """Log a user query."""
        self.query_count += 1
        print(f"📝 Query #{self.query_count}: {query[:50]}...")
    
    def log_tool_call(self, tool_name: str, duration_ms: float):
        """Log a tool call with duration."""
        if tool_name not in self.tool_calls:
            self.tool_calls[tool_name] = []
        self.tool_calls[tool_name].append(duration_ms)
        print(f"⚙️  Tool: {tool_name} ({duration_ms:.0f}ms)")
    
    def log_error(self, error: str, context: Dict[str, Any]):
        """Log an error with context."""
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "context": context
        })
        print(f"❌ Error: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        tool_stats = {}
        for tool, durations in self.tool_calls.items():
            tool_stats[tool] = {
                "count": len(durations),
                "avg_ms": sum(durations) / len(durations) if durations else 0,
                "total_ms": sum(durations)
            }
        
        return {
            "runtime_seconds": runtime,
            "total_queries": self.query_count,
            "total_tool_calls": sum(len(v) for v in self.tool_calls.values()),
            "tool_breakdown": tool_stats,
            "errors": len(self.errors),
            "queries_per_minute": (self.query_count / runtime * 60) if runtime > 0 else 0
        }
    
    def print_summary(self):
        """Print performance summary."""
        stats = self.get_stats()
        
        print("\n" + "="*70)
        print("📊 PERFORMANCE SUMMARY")
        print("="*70)
        print(f"Runtime: {stats['runtime_seconds']:.1f}s")
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Total Tool Calls: {stats['total_tool_calls']}")
        print(f"Queries/Min: {stats['queries_per_minute']:.1f}")
        
        if stats['tool_breakdown']:
            print("\n🔧 Tool Usage:")
            for tool, metrics in sorted(
                stats['tool_breakdown'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            ):
                print(f"   {tool}: {metrics['count']} calls, {metrics['avg_ms']:.0f}ms avg")
        
        if stats['errors']:
            print(f"\n❌ Errors: {stats['errors']}")
        
        print("="*70)


# Global monitor instance
_monitor = None


def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def reset_monitor():
    """Reset the performance monitor."""
    global _monitor
    _monitor = PerformanceMonitor()