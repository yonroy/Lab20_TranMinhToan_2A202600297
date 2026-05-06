# Phase Execution Plan - Lab 20

## Scope and objective

- Build a complete baseline + multi-agent research pipeline in 120 minutes.
- Keep architecture clear: supervisor orchestration, role separation, shared state contract, and traceability.
- Produce final deliverables: trace evidence + benchmark report + failure mode notes.

## Global constraints

- Timebox: 120 minutes.
- Search provider: Tavily API.
- Keep guardrails enabled: max iterations, timeout, retry/fallback.
- Maintain logs per run type:
  - logs/baseline/
  - logs/multi_agent/

## Phase 1 (0-15 min) - Setup and baseline sanity

### Goal

- Ensure environment runs.
- Freeze state/handoff contract early to avoid rework.

### Tasks

1. Environment and dependencies
- Install package: pip install -e ".[llm,dev]"
- Verify .env has OPENAI_API_KEY and TAVILY_API_KEY.

2. Quick tests for contract sanity
- Run focused tests:
  - pytest tests/test_config.py -q
  - pytest tests/test_state.py -q

3. Baseline smoke run
- Run:
  - python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"

4. Confirm state contract fields
- Review shared state in src/multi_agent_research_lab/core/state.py
- Confirm required fields exist and are stable:
  - request, iteration, route_history
  - sources, research_notes, analysis_notes, final_answer
  - agent_results, trace, errors

### Expected output

- Baseline command returns valid response string.
- Core state contract is agreed and unchanged for later phases.

### Done criteria

- Baseline CLI runs without crash.
- test_config + test_state pass.

## Phase 2 (15-35 min) - Service layer (LLM + search)

### Goal

- Implement reliable service clients before orchestration.

### Tasks

1. LLM client implementation
- File: src/multi_agent_research_lab/services/llm_client.py
- Implement real completion call.
- Add timeout + retry.
- Return usage metadata for benchmark (tokens, estimated cost).

2. Tavily search client implementation
- File: src/multi_agent_research_lab/services/search_client.py
- Integrate Tavily API.
- Normalize records into SourceDocument.
- Add fallback behavior when provider fails.

3. Unit-level validation
- Run service smoke checks via CLI or minimal tests.

### Expected output

- LLM and search calls work with real APIs.
- SourceDocument list is structured and reusable by agents.

### Done criteria

- No StudentTodoError in service layer paths used by baseline/multi-agent.
- Search returns at least 1 source for a normal research query.

## Phase 3 (35-55 min) - Supervisor routing policy

### Goal

- Implement deterministic routing and stop condition.

### Tasks

1. Supervisor logic
- File: src/multi_agent_research_lab/agents/supervisor.py
- Route order policy:
  - missing sources/research_notes -> researcher
  - missing analysis_notes -> analyst
  - missing final_answer -> writer
  - else -> done

2. Guardrails
- Enforce max_iterations from settings.
- Record route history every decision.
- Add safe fallback when repeated worker errors occur.

3. Test update/validation
- Keep existing tests green.
- Add or adjust tests if needed for route behavior.

### Expected output

- Supervisor can decide next step consistently.
- Loop cannot run forever.

### Done criteria

- Route decisions are traceable in state.route_history.
- Stop condition works.

## Phase 4 (55-85 min) - Worker agents implementation

### Goal

- Implement role-specific behavior for researcher, analyst, writer.

### Tasks

1. Researcher
- File: src/multi_agent_research_lab/agents/researcher.py
- Use search client and produce research_notes + sources.

2. Analyst
- File: src/multi_agent_research_lab/agents/analyst.py
- Produce analysis_notes from research evidence.

3. Writer
- File: src/multi_agent_research_lab/agents/writer.py
- Produce final_answer for target audience.

4. Agent result tracking
- Push outputs to state.agent_results for later benchmarking/debug.

### Expected output

- Each agent writes only role-owned fields.
- Final answer quality is better than raw baseline for complex prompts.

### Done criteria

- Multi-agent run can progress through all worker roles.
- State fields update correctly after each role.

## Phase 5 (85-100 min) - Workflow orchestration

### Goal

- Wire supervisor and workers into executable graph.

### Tasks

1. Build workflow graph
- File: src/multi_agent_research_lab/graph/workflow.py
- Implement build() and run() with conditional transitions.

2. CLI integration validation
- File: src/multi_agent_research_lab/cli.py
- Validate multi-agent command returns final state payload.

### Expected output

- End-to-end orchestration works from CLI.

### Done criteria

- Command runs:
  - python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"
- Workflow exits with done state.

## Phase 6 (100-112 min) - Tracing and logging folders

### Goal

- Persist runtime traces separately for baseline and multi-agent.

### Tasks

1. File-based tracing
- File: src/multi_agent_research_lab/observability/tracing.py
- Add trace writer helper with run_id + timestamp records.

2. Log folder structure
- Ensure directories are auto-created:
  - logs/baseline/
  - logs/multi_agent/

3. CLI/workflow hooks
- Baseline path writes to logs/baseline.
- Multi-agent path writes to logs/multi_agent.

### Expected output

- Every run produces a trace file in correct folder.

### Done criteria

- You can open latest run logs and inspect step-level events.

## Phase 7 (112-120 min) - Benchmark and submission artifacts

### Goal

- Produce required artifacts for grading and review.

### Tasks

1. Benchmark execution
- Files:
  - src/multi_agent_research_lab/evaluation/benchmark.py
  - src/multi_agent_research_lab/evaluation/report.py
- Compare baseline vs multi-agent on:
  - latency_seconds
  - estimated_cost_usd
  - quality_score
  - citation_coverage

2. Report completion
- File: reports/benchmark_report.md
- Include short conclusion: where multi-agent helps and where it is overkill.

3. Final checks
- Run all tests:
  - pytest -q
- Capture trace screenshot or trace file evidence.

### Expected output

- Complete benchmark report with practical recommendation.

### Done criteria

- Deliverables ready:
  - repo code
  - trace evidence
  - benchmark report
  - failure mode explanation

## Fast command checklist

1. pip install -e ".[llm,dev]"
2. pytest tests/test_config.py tests/test_state.py -q
3. python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"
4. python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"
5. pytest -q

## Risk management

- API timeout/rate limit:
  - Use retries and fallback response.
- Infinite loop risk:
  - Enforce max_iterations and done condition.
- Missing evidence quality:
  - Require minimum source count before writer stage.
- Last-minute instability:
  - Freeze scope in final 15 minutes, fix blockers only.
