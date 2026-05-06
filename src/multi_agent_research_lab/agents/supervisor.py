"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Implements deterministic routing policy and guardrails.
        - missing sources/research_notes -> researcher
        - missing analysis_notes -> analyst
        - missing final_answer -> writer
        - else -> done
        """
        settings = get_settings()

        # Guardrail: stop if max iterations exceeded
        if state.iteration >= settings.max_iterations:
            state.errors.append(f"Max iterations ({settings.max_iterations}) exceeded.")
            state.record_route("done")
            return state

        # Check for repeated errors from workers
        if state.errors and len(state.errors) >= 3:
            state.record_route("done")
            return state

        # Routing logic
        next_route = "done"

        critic_ran = any(r.agent.value == "critic" for r in state.agent_results)

        if not state.sources or not state.research_notes:
            next_route = "researcher"
        elif not state.analysis_notes:
            next_route = "analyst"
        elif not state.final_answer:
            next_route = "writer"
        elif not critic_ran:
            next_route = "critic"
        else:
            next_route = "done"

        state.record_route(next_route)
        return state
