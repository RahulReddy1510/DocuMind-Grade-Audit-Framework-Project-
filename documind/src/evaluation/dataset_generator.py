import json
import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Define Schema for Synthetic Data
class SyntheticContract(BaseModel):
    title: str = Field(description="Title of the contract")
    content: str = Field(description="Full text of the contract, formatted as Markdown")
    known_violations: List[Dict[str, str]] = Field(description="List of inserted violations. Each dict has 'clause_id' and 'expected_violation_type'")

class GoldenDatasetGenerator:
    """
    Generates synthetic legal contracts with inserted known violations 
    to create a 'Golden Dataset' for evaluation.
    """
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.parser = JsonOutputParser(pydantic_object=SyntheticContract)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Legal Data Generator.
            Create a synthetic UAE Employment Contract.
            
            Instructions:
            1. The contract should be about 2-3 pages long (in markdown).
            2. It MUST contain exactly 3 subtle violations of UAE Labor Law.
               - Example 1: Probation period > 6 months.
               - Example 2: Notice period < 30 days.
               - Example 3: Annual leave < 30 days.
            3. Output the result as JSON with:
               - title
               - content (the markdown text)
               - known_violations (list mapping clause ID to the violation type).
            """),
            ("user", "Generate a contract now.")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_sample(self, output_dir: str = "data/golden_dataset"):
        """Generates a single sample and saves it."""
        print("Generating synthetic contract...")
        try:
            data = self.chain.invoke({})
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Save the Text (as PDF simulation - actually just MD for now, or text)
            # For the pipeline, we need PDF. Since generating PDF programmatically is tedious,
            # we will save as Markdown and let the user convert, or mock the parser for this test.
            # For seamlessness, let's save as .md and assume parser handles it or we convert.
            # Actually, `pymupdf4llm` reads PDFs.
            # We'll save the raw text and the ground truth metadata.
            
            safe_title = data['title'].replace(" ", "_").lower()
            
            # Save Content
            with open(f"{output_dir}/{safe_title}.md", "w", encoding="utf-8") as f:
                f.write(data['content'])
                
            # Save Ground Truth
            with open(f"{output_dir}/{safe_title}_truth.json", "w", encoding="utf-8") as f:
                json.dump(data['known_violations'], f, indent=2)
                
            print(f"Generated: {safe_title}")
            return safe_title, data['known_violations']
            
        except Exception as e:
            print(f"Error generating dataset: {e}")
            return None, None

if __name__ == "__main__":
    gen = GoldenDatasetGenerator()
    gen.generate_sample()
