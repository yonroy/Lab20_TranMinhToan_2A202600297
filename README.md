# Lab 20: Multi-Agent Research System

**Tran Minh Toan — 2A202600297**

Hệ thống nghiên cứu đa agent được xây dựng trên **LangGraph**, gồm pipeline: Supervisor → Researcher → Analyst → Writer → Critic, kèm content guardrail, tracing, và benchmark so sánh với single-agent baseline.

## Architecture

```text
User Query
   |
   v  (content guardrail)
Supervisor  ──────────────────────────────────────────┐
   │                                                  │
   ├──► Researcher  (SearchClient → Tavily / fallback)│
   │        │ sources, research_notes                 │
   │        └──► Supervisor                           │
   │                                                  │
   ├──► Analyst     (LLMClient → OpenAI)              │
   │        │ analysis_notes                          │
   │        └──► Supervisor                           │
   │                                                  │
   ├──► Writer      (LLMClient → OpenAI)              │
   │        │ final_answer + inline citations         │
   │        └──► Supervisor                           │
   │                                                  │
   └──► Critic      (citation coverage + fact-check)  │
            │ citation_coverage metadata              │
            └──► Supervisor ──► END ◄─────────────────┘
                                 │
                          TraceWriter (logs/)
                          BenchmarkReport (reports/)
```

### Agents

| Agent | Vai trò | Output |
|---|---|---|
| **Supervisor** | Điều phối, routing, guardrail vòng lặp | `route_history` |
| **Researcher** | Tìm kiếm tài liệu qua Tavily API | `sources`, `research_notes` |
| **Analyst** | Trích xuất key claims, so sánh quan điểm, flag weak evidence | `analysis_notes` |
| **Writer** | Viết câu trả lời có inline citation `[1]`, `[2]`, ... | `final_answer` |
| **Critic** | Kiểm tra citation coverage và hallucination | metadata `citation_coverage` |

### Guardrails

- **Content guardrail**: regex blocking vũ khí, malware, ma túy, bạo lực, nội dung tình dục trẻ em, làm giả tài liệu (Tiếng Anh + Tiếng Việt).
- **Iteration cap**: dừng khi `iteration >= max_iterations` (default 6).
- **Error cap**: dừng khi có ≥ 3 lỗi liên tiếp từ worker.
- **Retry**: LLMClient và SearchClient đều dùng `tenacity` (exponential backoff, 3 lần).
- **Fallback**: cả hai client tự động trả về kết quả cục bộ khi API key thiếu hoặc lỗi mạng.

## Cấu trúc repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Supervisor, Researcher, Analyst, Writer, Critic
│   ├── core/                # Config (pydantic-settings), State, Schemas, Errors
│   ├── graph/               # LangGraph workflow (StateGraph)
│   ├── services/            # LLMClient (OpenAI), SearchClient (Tavily), Storage
│   ├── evaluation/          # Benchmark suite, Markdown report renderer
│   ├── observability/       # TraceWriter (JSON logs), trace_span, logging config
│   └── cli.py               # CLI: baseline | multi-agent | benchmark
├── configs/
│   ├── lab_default.yaml     # Runtime config overrides
│   └── questions.json       # Benchmark questions (expect_blocked flag)
├── logs/                    # Auto-generated trace JSON files per run
├── reports/
│   └── benchmark_report.md  # Auto-generated benchmark comparison
├── tests/                   # Unit + integration tests
├── docs/                    # Lab guide, rubric, design notes
├── pyproject.toml
├── Dockerfile
└── Makefile
```

## Quickstart

### 1. Tạo môi trường

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -e ".[llm,dev]"
cp .env.example .env
```

### 2. Cấu hình API keys

Mở `.env` và điền:

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...        # optional, dùng fallback nếu thiếu
LANGSMITH_API_KEY=...          # optional
OPENAI_MODEL=gpt-4o-mini       # default
MAX_ITERATIONS=6
TIMEOUT_SECONDS=60
```

### 3. Chạy tests

```bash
make test
# hoặc
pytest tests/ -v
```

### 4. Chạy baseline (single-agent)

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "What is GraphRAG and how does it improve retrieval-augmented generation?"
```

Trace được lưu tại `logs/baseline/run_<timestamp>_<id>.json`.

### 5. Chạy multi-agent pipeline

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "How do multi-agent systems improve the quality of AI research pipelines?"
```

Trace được lưu tại `logs/multi_agent/run_<timestamp>_<id>.json`.

### 6. Chạy benchmark đầy đủ

```bash
python -m multi_agent_research_lab.cli benchmark \
  --config configs/questions.json
```

- Chạy tất cả câu hỏi có `expect_blocked: false` qua cả hai pipeline.
- Kiểm tra guardrail cho câu có `expect_blocked: true`, ghi log vào `logs/benchmark_guardrail/`.
- Xuất report tại `reports/benchmark_report.md`.

## Logs & Tracing

Mỗi lần chạy tạo file JSON tại `logs/<run_type>/run_<timestamp>_<run_id>.json` chứa toàn bộ `ResearchState`:

```json
{
  "request": { "query": "...", "audience": "...", "max_sources": 5 },
  "sources": [...],
  "research_notes": "...",
  "analysis_notes": "...",
  "final_answer": "...",
  "agent_results": [
    { "agent": "researcher", "content": "Found 5 sources.", "metadata": {...} },
    { "agent": "analyst", "content": "...", "metadata": { "cost_usd": 0.0012 } },
    { "agent": "writer", "content": "...", "metadata": { "cost_usd": 0.0031 } },
    { "agent": "critic", "content": "...", "metadata": { "citation_coverage": 0.8 } }
  ],
  "route_history": ["researcher", "analyst", "writer", "critic", "done"],
  "iteration": 5,
  "errors": []
}
```

## Dependencies chính

| Package | Mục đích |
|---|---|
| `langgraph` | Xây dựng StateGraph workflow |
| `openai` | LLM completions |
| `pydantic-settings` | Config từ `.env` |
| `tenacity` | Retry / exponential backoff |
| `typer` + `rich` | CLI + terminal UI |

## References

- [Building effective agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/guides/chat-completions)
- [Tavily Search API](https://docs.tavily.com/)

