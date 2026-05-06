"""Command-line entrypoint for the lab starter."""

import json
import re
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark, run_benchmark_suite
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import TraceWriter, trace_span
from multi_agent_research_lab.services.llm_client import LLMClient

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()

# ---------------------------------------------------------------------------
# Content guardrail
# ---------------------------------------------------------------------------

_BLOCKED_PATTERNS: list[re.Pattern[str]] = [re.compile(p, re.IGNORECASE) for p in [
    # Vũ khí, chất nổ, chất độc
    r"\b(bomb|explosive|detonate|bioweapon|chemical\s+weapon|nerve\s+agent|anthrax|ricin|sarin)\b",
    r"\b(vũ khí|chất nổ|bom|kích nổ|vũ khí sinh học|vũ khí hóa học|chất độc thần kinh)\b",
    # Tấn công, hack, khai thác
    r"\b(hack|exploit|malware|ransomware|ddos|sql\s*injection|zero.?day|botnet|keylogger|rootkit)\b",
    r"\b(tấn công mạng|phần mềm độc hại|khai thác lỗ hổng|đánh cắp dữ liệu)\b",
    # Ma túy, chất cấm
    r"\b(synthesize\s+drug|make\s+(meth|heroin|cocaine|fentanyl)|drug\s+lab)\b",
    r"\b(tổng hợp ma túy|sản xuất ma túy|chế\s+ma túy|methamphetamine)\b",
    # Nội dung tình dục liên quan trẻ em
    r"\b(child\s+(porn|sexual|abuse\s+material)|csam|underage\s+(nude|sex))\b",
    r"\b(khiêu dâm trẻ em|xâm hại tình dục trẻ em)\b",
    # Bạo lực, khủng bỏ
    r"\b(how\s+to\s+kill|how\s+to\s+murder|assassination\s+plan|terrorist\s+attack|genocide)\b",
    r"\b(cách giết người|âm mưu ám sát|tấn công khủng bố|diệt chủng)\b",
    # Gian lận, làm giả tài liệu
    r"\b(fake\s+(passport|id|visa|degree|certificate)|counterfeit\s+money|money\s+laundering)\b",
    r"\b(làm giả hộ chiếu|làm giả chứng chỉ|rửa tiền|tiền giả)\b",
]]

_BLOCKED_MESSAGE = (
    "Yêu cầu của bạn chứa nội dung nhạy cảm hoặc có thể vi phạm pháp luật.\n"
    "Hệ thống từ chối xử lý câu hỏi này.\n\n"
    "Your query contains sensitive or potentially illegal content.\n"
    "The system refuses to process this request."
)


def _check_guardrail(query: str) -> None:
    """Raise typer.Exit if query matches any blocked content pattern."""
    for pattern in _BLOCKED_PATTERNS:
        if pattern.search(query):
            console.print(Panel.fit(_BLOCKED_MESSAGE, title="[red]Blocked[/red]", style="red"))
            raise typer.Exit(code=1)


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline using one LLM call."""

    _init()
    _check_guardrail(query)
    writer = TraceWriter("baseline")
    llm = LLMClient()
    with trace_span("baseline_run", {"query": query}) as span:
        request = ResearchQuery(query=query)
        state = ResearchState(request=request)

        system_prompt = (
            f"You are a knowledgeable research assistant for {request.audience}. "
            "Answer the query concisely and accurately."
        )
        response = llm.complete(system_prompt=system_prompt, user_prompt=query)
        state.final_answer = response.content

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content="Single-agent baseline completion.",
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd,
                },
            )
        )
        state.add_trace_event("completion", {"span": span, "cost_usd": response.cost_usd})

    log_path = writer.write_trace(state)
    console.print(f"[dim]Trace saved to {log_path}[/dim]")
    console.print(Panel.fit(state.final_answer or "(no answer)", title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    _check_guardrail(query)
    writer = TraceWriter("multi_agent")
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        with trace_span("multi_agent_run", {"query": query}) as span:
            result = workflow.run(state)
            result.add_trace_event("workflow_completion", {"span": span})
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    
    log_path = writer.write_trace(result)
    console.print(f"[dim]Trace saved to {log_path}[/dim]")
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    config: Annotated[Path, typer.Option("--config", "-c", help="Path to questions.json")] = Path("configs/questions.json"),
) -> None:
    """Compare baseline vs multi-agent and generate report."""
    _init()
    
    if not config.exists():
        console.print(f"[red]Error:[/red] Config file {config} not found.")
        raise typer.Exit(code=1)

    with open(config, encoding="utf-8") as f:
        data = json.load(f)
        questions = [q["query"] for q in data.get("questions", []) if not q.get("expect_blocked")]

    console.print(f"[bold blue]Starting Benchmark for {len(questions)} queries...[/bold blue]\n")

    # 1. Setup runners
    def baseline_runner(q: str) -> ResearchState:
        writer = TraceWriter("benchmark_baseline")
        llm = LLMClient()
        request = ResearchQuery(query=q)
        state = ResearchState(request=request)
        system_prompt = "You are a research assistant. Provide a concise answer."
        with trace_span("benchmark_baseline", {"query": q}) as span:
            response = llm.complete(system_prompt, q)
            state.final_answer = response.content
            state.agent_results.append(AgentResult(
                agent=AgentName.RESEARCHER,
                content="Baseline",
                metadata={"cost_usd": response.cost_usd or 0.0},
            ))
            state.add_trace_event("completion", {"span": span, "cost_usd": response.cost_usd})
        log_path = writer.write_trace(state)
        console.print(f"  [dim]Trace → {log_path}[/dim]")
        return state

    def multi_agent_runner(q: str) -> ResearchState:
        writer = TraceWriter("benchmark_multi_agent")
        state = ResearchState(request=ResearchQuery(query=q))
        with trace_span("benchmark_multi_agent", {"query": q}) as span:
            result = MultiAgentWorkflow().run(state)
            result.add_trace_event("workflow_completion", {"span": span})
        log_path = writer.write_trace(result)
        console.print(f"  [dim]Trace → {log_path}[/dim]")
        return result

    # 2. Execute runs using the suite
    all_metrics = run_benchmark_suite(questions, baseline_runner, multi_agent_runner)

    # 3. Generate Report
    report_content = render_markdown_report(all_metrics)
    
    report_path = "reports/benchmark_report.md"
    from multi_agent_research_lab.services.storage import LocalArtifactStore
    LocalArtifactStore().write_text("benchmark_report.md", report_content)
    
    console.print(f"\n[bold green]Success![/bold green] Report saved to {report_path}")
    console.print(Panel(report_content, title="Final Benchmark Results"))


if __name__ == "__main__":
    app()
