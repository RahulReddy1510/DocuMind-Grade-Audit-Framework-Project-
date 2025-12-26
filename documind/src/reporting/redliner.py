from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class AutoRedliner:
    """
    Generates suggested revisions for clauses that violate the law.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Legal Expert. 
            Your task is to rewrite a contract clause to be compliant with the cited UAE Law.
            
            Rules:
            1. Maintain the original intent of the clause as much as possible.
            2. Only change what is necessary to remove the violation.
            3. Use formal legal language.
            4. Output ONLY the rewritten clause text. No markdown, no explanations.
            """),
            ("user", """
            Original Clause: "{clause_text}"
            Violation Reasoning: "{reasoning}"
            Cited Law: "{law_reference}"
            
            Rewritten Clause:
            """)
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_fix(self, finding: Dict[str, Any]) -> str:
        """
        Generates a compliant version of the clause.
        """
        if finding.get("status") != "VIOLATION":
            return ""
            
        try:
            return self.chain.invoke({
                "clause_text": finding.get("source_verification", "") or "Text unavailable",
                "reasoning": finding.get("reasoning", ""),
                "law_reference": finding.get("law_reference", "")
            })
        except Exception as e:
            print(f"Error generating redline: {e}")
            return "Error generating suggestion."
