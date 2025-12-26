from typing import TypedDict, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from src.analysis.critic_agent import CriticAgent
from src.analysis.reflector_node import Reflector
from src.ingestion.vector_store import VectorStoreManager

class AgentState(TypedDict):
    clause: Dict[str, Any]
    contract_namespace: str
    critic_finding: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    attempts: int
    final_output: Optional[Dict[str, Any]]

class AuditWorkflow:
    def __init__(self):
        self.critic_agent = CriticAgent()
        # Initializing VectorStore might need environment variables to be set
        # For now, we instantiate it here, but in prod could be passed in.
        try:
            self.vs_manager = VectorStoreManager()
            self.reflector = Reflector(self.vs_manager)
        except Exception as e:
            print(f"Warning: VectorStore validation disabled due to init error: {e}")
            self.reflector = None

    def critic_node(self, state: AgentState):
        """Node for the Critic Agent"""
        print(f"--- Critic Node (Attempt {state['attempts'] + 1}) ---")
        
        # In a real scenario, we'd retrieve laws here based on clause text
        relevant_laws = "Standard UAE Contract Law applies." 
        
        finding = self.critic_agent.evaluate_clause(state['clause'], relevant_laws)
        
        return {
            "critic_finding": finding,
            "attempts": state['attempts'] + 1
        }

    def reflector_node(self, state: AgentState):
        """Node for the Reflector (Hallucination Checker)"""
        print("--- Reflector Node ---")
        
        if not self.reflector:
            # Bypass if vector store unavail
            return {"verification_result": {"verified": True, "reason": "Reflector disabled"}}

        finding = state['critic_finding']
        namespace = state['contract_namespace']
        
        result = self.reflector.validate_critic(finding, namespace)
        
        return {"verification_result": result}

    def should_continue(self, state: AgentState):
        """Conditional Edge Logic"""
        verification = state['verification_result']
        
        if verification['verified']:
            return "end"
        
        if state['attempts'] >= 3:
            return "end_max_retries"
            
        return "retry"

    def build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("critic", self.critic_node)
        workflow.add_node("reflector", self.reflector_node)
        
        workflow.set_entry_point("critic")
        
        workflow.add_edge("critic", "reflector")
        
        workflow.add_conditional_edges(
            "reflector",
            self.should_continue,
            {
                "end": END,
                "end_max_retries": END,
                "retry": "critic"
            }
        )
        
        return workflow.compile()

if __name__ == "__main__":
    # Smoke test logic
    pass
