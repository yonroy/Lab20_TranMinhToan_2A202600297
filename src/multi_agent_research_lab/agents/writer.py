"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        context = f"Research:\n{state.research_notes or ''}\n\nAnalysis:\n{state.analysis_notes or ''}"

        # Build numbered source list so the LLM can cite by index
        sources_block = ""
        if state.sources:
            lines = [
                f"[{i+1}] {doc.title} — {doc.snippet[:200]}"
                for i, doc in enumerate(state.sources)
            ]
            sources_block = "Available Sources (you MUST cite ALL of them using [1], [2], … notation):\n" + "\n".join(lines)

        system_prompt = (
            f"You are a Technical Writer. Produce a clear, well-structured response for {state.request.audience}. "
            "Synthesize ALL provided research and analysis notes. "
            "You MUST reference every numbered source at least once using inline citations like [1], [2], etc. "
            "Do NOT omit any source. If a source is less central, mention it briefly in a supporting sentence."
        )
        user_prompt = (
            f"{sources_block}\n\n"
            f"Context:\n{context}\n\n"
            f"Original Query: {state.request.query}"
        )

        response = self.llm_client.complete(system_prompt, user_prompt)
        state.final_answer = response.content

        # Record result
        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content="Generated final answer.",
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd
                }
            )
        )

        return state
