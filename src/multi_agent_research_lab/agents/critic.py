"""Critic agent: fact-checking and citation coverage review."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        if not state.final_answer:
            state.errors.append("Critic: no final_answer to review.")
            return state

        # 1. Citation coverage check — match either [index] or title substring
        cited = sum(
            1 for i, doc in enumerate(state.sources)
            if f"[{i+1}]" in state.final_answer or doc.title.lower()[:30] in state.final_answer.lower()
        )
        total = len(state.sources)
        coverage = round(cited / total, 2) if total > 0 else 0.0

        # 2. LLM-based hallucination/weak-evidence check
        system_prompt = (
            "You are a rigorous fact-checker. Your job is to:\n"
            "1. Identify any claims in the answer that are unsupported, overstated, or potentially hallucinated.\n"
            "2. Flag any sources that were NOT cited or referenced in the answer.\n"
            "3. If citation coverage is below 80%, explicitly list the uncited sources and explain what information was missed.\n"
            "Be specific and critical. Do NOT say 'No issues found' if citation coverage is below 80% or if any source is uncited."
        )
        uncited_sources = [
            doc for i, doc in enumerate(state.sources)
            if f"[{i+1}]" not in state.final_answer and doc.title.lower()[:30] not in state.final_answer.lower()
        ]
        sources_summary = "\n".join(
            f"- {'[UNCITED] ' if doc in uncited_sources else '[cited]  '}{doc.title}: {doc.snippet[:200]}"
            for doc in state.sources
        )
        user_prompt = (
            f"Citation Coverage: {coverage:.0%} ({cited}/{total} sources cited)\n"
            f"{'⚠ WARNING: ' + str(len(uncited_sources)) + ' sources were NOT cited in the answer.' if uncited_sources else ''}\n\n"
            f"Sources:\n{sources_summary}\n\n"
            f"Final Answer:\n{state.final_answer}\n\n"
            f"Review the answer. Flag uncited sources and unsupported claims."
        )
        critique = self.llm_client.complete(system_prompt, user_prompt)

        # 3. Record result with citation coverage metadata
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=critique.content,
                metadata={
                    "citation_coverage": coverage,
                    "cited_sources": cited,
                    "total_sources": total,
                    "uncited_titles": [doc.title for doc in uncited_sources],
                    "input_tokens": critique.input_tokens,
                    "output_tokens": critique.output_tokens,
                    "cost_usd": critique.cost_usd,
                },
            )
        )

        return state