from typing import Dict, Any
from src.ingestion.vector_store import VectorStoreManager

class Reflector:
    """
    Validates the Critic's findings by performing a 'Reverse Lookup' 
    against the verified source text in the Vector Database.
    """
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store

    def validate_critic(self, critic_output: Dict[str, Any], contract_namespace: str) -> Dict[str, Any]:
        """
        Checks if the 'source_verification' quote actually exists in the contract.
        
        Args:
            critic_output: The JSON output from the Critic Agent.
            contract_namespace: The Pinecone namespace for the specific contract.
            
        Returns:
            Dict: { "verified": bool, "reason": str }
        """
        source_quote = critic_output.get("source_verification", "").strip()
        status = critic_output.get("status")

        # Case 1: Missing Clause - No source expected
        if status == "MISSING":
            return {"verified": True, "reason": "Clause marked as missing, no source expected."}

        # Case 2: No quote provided for an existing clause
        if not source_quote:
            return {
                "verified": False, 
                "reason": "Critic failed to provide a source verification quote."
            }

        # Case 3: Verify the quote
        # We search for the EXACT quote in the vector DB.
        # Ideally, we'd use a sparse search (BM25) for exact matching, 
        # but dense embedding similarity is a good proxy if threshold is high.
        
        matches = self.vector_store.query_similarity(source_quote, top_k=1)
        
        if not matches:
             return {
                "verified": False, 
                "reason": "No matching text found in the document."
            }

        top_match = matches[0]
        score = top_match['score']
        
        # Threshold: 0.90 is usually safe for "this text exists" with high overlap
        # Adjust based on embedding model. OpenAI v3-small is usually normalized.
        SIMILARITY_THRESHOLD = 0.85 
        
        if score < SIMILARITY_THRESHOLD:
            return {
                "verified": False,
                "reason": f"Quote verification failed. Nearest match similarity: {score:.2f}. potential hallucination."
            }
            
        return {"verified": True, "reason": "Source verified in document."}
