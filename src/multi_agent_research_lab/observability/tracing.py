import json
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton."""
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
    finally:
        span["duration_seconds"] = perf_counter() - started


class TraceWriter:
    """Persists run traces to local files for benchmarking."""

    def __init__(self, run_type: str) -> None:
        self.run_type = run_type
        self.log_dir = Path("logs") / run_type
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def write_trace(self, state: Any) -> Path:
        """Write the full state trace to a JSON file."""
        filename = f"run_{self.timestamp}_{self.run_id}.json"
        filepath = self.log_dir / filename
        
        # Serialize ResearchState if it's a Pydantic model
        if hasattr(state, "model_dump"):
            data = state.model_dump()
        else:
            data = str(state)

        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return filepath
