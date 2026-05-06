"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with detailed analysis."""
    lines = [
        "# Benchmark Report",
        "",
        "This report compares the performance of the single-agent baseline against the multi-agent orchestration pipeline.",
        "",
        "## Metrics Summary",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality (Est) | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "N/A" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.4f}"
        quality = "N/A" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |")
    
    lines.extend([
        "",
        "## Analysis",
        "",
        "### Key Findings",
        "- **Latency**: Multi-agent systems typically exhibit higher latency due to sequential agent reasoning and intermediate orchestration overhead.",
        "- **Cost**: Multi-agent runs involve more token exchanges (supervisor instructions, agent handoffs), increasing API costs compared to a single-shot prompt.",
        "- **Traceability**: Multi-agent runs provide rich state logs and role separation, making it easier to debug failures in the research phase vs. the writing phase.",
        "",
        "### Recommendation",
        "Use **Multi-Agent** for complex, high-stakes research tasks where citation accuracy and depth are critical. Use **Baseline** for simple queries where speed and cost-efficiency are prioritized."
    ])
    return "\n".join(lines) + "\n"
