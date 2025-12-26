from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# Define the Output Schema
class CriticOutput(BaseModel):
    clause_id: str = Field(description="The ID of the clause being analyzed")
    status: str = Field(description="COMPLIANT, VIOLATION, or MISSING")
    law_reference: str = Field(description="Reference to the specific UAE law (e.g., UAE Labor Law Art. 5)")
    reasoning: str = Field(description="Detailed explanation of why it is compliant or a violation")
    source_verification: str = Field(description="The exact quote from the contract text that supports this finding. MUST be creating verbatum.")

class CriticAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.parser = JsonOutputParser(pydantic_object=CriticOutput)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Legal Auditor specializing in UAE Law.
            Your task is to review contract clauses for compliance.
            
            You must output a JSON object with the following fields:
            - clause_id: The ID provided.
            - status: COMPLIANT, VIOLATION, or MISSING (if a required clause is absent).
            - law_reference: Cite the specific UAE law.
            - reasoning: Explain your decision.
            - source_verification: Copy the EXACT text from the clause that you used to make this decision. This is CRITICAL for hallucination checking.
            
            If the clause is compliant, verify it against standard UAE norms.
            If the clause is a violation, explain exactly why based on the provided 'Relevant Laws'.
            """),
            ("user", """
            Clause ID: {clause_id}
            Clause Text: {clause_text}
            
            Relevant Laws (Retrieved):
            {relevant_laws}
            """)
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def evaluate_clause(self, clause_data: Dict[str, Any], relevant_laws: str = "Standard UAE Contract Law principles apply.") -> Dict[str, Any]:
        """
        Evaluates a single clause.
        
        Args:
            clause_data: Dict containing 'clause_id' and 'raw_text'.
            relevant_laws: Context retrieved from the Law Vector DB.
            
        Returns:
            Dict matching CriticOutput schema.
        """
        try:
            result = self.chain.invoke({
                "clause_id": clause_data.get("clause_id", "unknown"),
                "clause_text": clause_data.get("raw_text", ""),
                "relevant_laws": relevant_laws
            })
            return result
        except Exception as e:
            print(f"Error in Critic Agent: {e}")
            return {
                "clause_id": clause_data.get("clause_id"),
                "status": "ERROR",
                "reasoning": str(e),
                "source_verification": ""
            }

if __name__ == "__main__":
    # Smoke Test
    agent = CriticAgent()
    sample_clause = {
        "clause_id": "1.1",
        "raw_text": "The Employee is entitled to 30 days of annual leave."
    }
    # This will fail without an API Key, but shows usage
    # print(agent.evaluate_clause(sample_clause))
