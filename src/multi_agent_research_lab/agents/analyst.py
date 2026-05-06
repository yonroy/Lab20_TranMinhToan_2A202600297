"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        if not state.research_notes:
            state.errors.append("Analyst ran but research_notes were empty.")
            return state

        system_prompt = (
            "You are a Senior Analyst. Your task is to extract key claims, "
            "compare viewpoints, and flag weak evidence from the provided research notes."
        )
        user_prompt = f"Research Notes:\n{state.research_notes}"

        response = self.llm_client.complete(system_prompt, user_prompt)
        state.analysis_notes = response.content

        # Record result
        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content="Analyzed research notes.",
                metadata={
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                    "cost_usd": response.cost_usd
                }
            )
        )

        return state
