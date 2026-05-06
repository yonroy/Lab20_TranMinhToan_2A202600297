"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from rich.console import Console

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

_console = Console()

Runner = Callable[[str], ResearchState]


BenchmarkResult = tuple[ResearchState, BenchmarkMetrics]

def run_benchmark(run_name: str, query: str, runner: Runner) -> BenchmarkResult:
    """Measure latency, cost, and citation coverage for a run."""
    short_q = query[:60] + "..." if len(query) > 60 else query
    _console.print(f"  [cyan]▶[/cyan] [{run_name}] Running: [italic]{short_q}[/italic]")
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    _console.print(f"  [green]✓[/green] [{run_name}] Done in {latency:.2f}s")

    # Calculate metrics from state
    total_cost = 0.0
    citation_coverage = 0.0
    
    # 1. Sum up cost from agent results
    for result in state.agent_results:
        total_cost += result.metadata.get("cost_usd") or 0.0
        
        # Capture citation coverage if current result is from Critic
        if "citation_coverage" in result.metadata:
            citation_coverage = result.metadata["citation_coverage"]

    # 2. Logic to determine quality or citation coverage if critic didn't run
    # (Simplified for the benchmark: uses critic coverage if available)
    
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=None,  # Typically assigned after manual or LLM-as-judge review
        notes=f"History: {' -> '.join(state.route_history)}. Sources: {len(state.sources)}."
    )
    return state, metrics

def run_benchmark_suite(questions: list[str], baseline_runner: Runner, multi_agent_runner: Runner) -> list[BenchmarkMetrics]:
    """Run comparison benchmarks for a list of questions."""
    all_metrics = []
    for i, query in enumerate(questions, 1):
        _console.print(f"\n[bold yellow]Query {i}/{len(questions)}:[/bold yellow] {query[:80]}")
        # Run baseline
        _, metrics_b = run_benchmark("Baseline", query, baseline_runner)
        all_metrics.append(metrics_b)
        
        # Run multi-agent
        _, metrics_m = run_benchmark("Multi-Agent", query, multi_agent_runner)
        all_metrics.append(metrics_m)
    return all_metrics
