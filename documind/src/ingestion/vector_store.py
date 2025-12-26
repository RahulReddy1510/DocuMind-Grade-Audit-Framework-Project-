import os
import time
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm

class VectorStoreManager:
    """
    Manages interactions with Pinecone Vector Database.
    Handles index creation, deletion, and document upsertion.
    """
    def __init__(self, index_name: str = "documind-index", namespace: str = "default"):
        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.pc = Pinecone(api_key=self.api_key)
        self.index_name = index_name
        self.namespace = namespace
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # Efficient for legal text
        self.dimension = 1536 # OpenAI embedding dimension

        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        """Checks if index exists, creates it if not."""
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.index_name}")
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
            except Exception as e:
                print(f"Failed to create index: {e}")
                raise

    def upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100):
        """
        Embeds and upserts chunks into Pinecone.
        
        Args:
            chunks: List of structured chunks from PDFProcessor.
            batch_size: Number of vectors to upsert in one batch.
        """
        print(f"Upserting {len(chunks)} chunks to namespace '{self.namespace}'...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare texts for embedding
            texts = [c['raw_text'] for c in batch]
            
            try:
                # Generate Embeddings
                embeds = self.embeddings.embed_documents(texts)
                
                # Prepare Vectors
                vectors = []
                for j, chunk in enumerate(batch):
                    # Create a unique ID: contract_id + hash or just sequential for now
                    # Ideally, clause_id should be part of the ID for deduplication
                    vector_id = f"{self.namespace}_{chunk['page_no']}_{i+j}" 
                    
                    metadata = {
                        "page_no": chunk['page_no'],
                        "section": chunk['section'],
                        "clause_id": chunk['clause_id'],
                        "raw_text": chunk['raw_text']
                    }
                    
                    vectors.append({
                        "id": vector_id,
                        "values": embeds[j],
                        "metadata": metadata
                    })
                
                # Upsert to Pinecone
                self.index.upsert(vectors=vectors, namespace=self.namespace)
                
            except Exception as e:
                print(f"Error upserting batch {i}: {e}")

    def query_similarity(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Queries the vector DB for similar content.
        """
        query_embedding = self.embeddings.embed_query(query)
        
        response = self.index.query(
            namespace=self.namespace,
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return response['matches']

if __name__ == "__main__":
    # Smoke test requires API keys, so wrapping in try/except or just defining class
    print("VectorStoreManager defined.")
