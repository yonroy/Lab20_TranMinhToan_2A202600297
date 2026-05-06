"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None) -> None:
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        query = state.request.query
        
        # 1. Search for sources
        sources = self.search_client.search(query, max_results=state.request.max_sources)
        state.sources.extend(sources)

        # 2. Compile notes from snippets
        notes_parts = []
        for doc in sources:
            notes_parts.append(f"Source: {doc.title}\n{doc.snippet}")
        
        state.research_notes = "\n\n".join(notes_parts)

        # 3. Record result
        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=f"Found {len(sources)} sources.",
                metadata={"source_count": len(sources)}
            )
        )
        
        return state
