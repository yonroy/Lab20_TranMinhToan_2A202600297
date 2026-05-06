"""LangGraph workflow implementation."""

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.workflow = self.build()

    def build(self) -> Any:
        """Create a LangGraph graph."""
        builder = StateGraph(ResearchState)

        # 1. Add nodes
        builder.add_node("supervisor", SupervisorAgent().run)
        builder.add_node("researcher", ResearcherAgent().run)
        builder.add_node("analyst", AnalystAgent().run)
        builder.add_node("writer", WriterAgent().run)
        builder.add_node("critic", CriticAgent().run)

        # 2. Add edges
        builder.set_entry_point("supervisor")

        # Worker nodes always return to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")
        # Critic runs after writer and returns to supervisor
        builder.add_edge("critic", "supervisor")

        # 3. Add conditional routing from supervisor
        def router(state: ResearchState) -> Literal["researcher", "analyst", "writer", "critic", "__end__"]:
            next_step = state.route_history[-1] if state.route_history else "done"
            if next_step == "done":
                return END
            return next_step

        builder.add_conditional_edges("supervisor", router)

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        # LangGraph returns a dict or model depending on config,
        # but since we used ResearchState as type in StateGraph,
        # it will provide a state-like object.
        result = self.workflow.invoke(state)
        
        # Ensure it returns a ResearchState object
        if isinstance(result, dict):
            return ResearchState.model_validate(result)
        return result
