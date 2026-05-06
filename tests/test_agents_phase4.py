from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState

def test_researcher_populates_sources_and_notes() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    agent = ResearcherAgent()
    state = agent.run(state)
    
    assert len(state.sources) > 0
    assert state.research_notes is not None
    assert len(state.agent_results) == 1

def test_analyst_requires_notes() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    agent = AnalystAgent()
    state = agent.run(state)
    
    assert any("empty" in e for e in state.errors)

def test_writer_synthesizes_answer() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.research_notes = "Some research"
    state.analysis_notes = "Some analysis"
    agent = WriterAgent()
    state = agent.run(state)
    
    assert state.final_answer is not None
    assert len(state.agent_results) == 1
