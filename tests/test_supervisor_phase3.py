from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    agent = SupervisorAgent()
    
    state = agent.run(state)
    
    assert state.route_history[-1] == "researcher"
    assert state.iteration == 1


def test_supervisor_routes_to_analyst_after_research() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.sources = [SourceDocument(title="S1", snippet="content")]
    state.research_notes = "Notes"
    agent = SupervisorAgent()
    
    state = agent.run(state)
    
    assert state.route_history[-1] == "analyst"


def test_supervisor_routes_to_writer_after_analysis() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.sources = [SourceDocument(title="S1", snippet="content")]
    state.research_notes = "Notes"
    state.analysis_notes = "Analysis"
    agent = SupervisorAgent()
    
    state = agent.run(state)
    
    assert state.route_history[-1] == "writer"


def test_supervisor_routes_to_done_at_end() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.sources = [SourceDocument(title="S1", snippet="content")]
    state.research_notes = "Notes"
    state.analysis_notes = "Analysis"
    state.final_answer = "Answer"
    agent = SupervisorAgent()
    
    state = agent.run(state)
    
    assert state.route_history[-1] == "done"


def test_supervisor_enforces_max_iterations() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.iteration = 10  # Assume max is 6
    agent = SupervisorAgent()
    
    state = agent.run(state)
    
    assert state.route_history[-1] == "done"
    assert any("Max iterations" in e for e in state.errors)
