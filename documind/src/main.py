import argparse
import os
import sys
from dotenv import load_dotenv

from src.ingestion.pdf_parser import PDFProcessor
from src.ingestion.vector_store import VectorStoreManager
from src.analysis.langgraph_workflow import AuditWorkflow
from src.reporting.summarizer_agent import SummarizerAgent

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="DocuMind: Legal Contract Auditor")
    parser.add_argument("pdf_path", help="Path to the PDF contract to audit")
    parser.add_argument("--namespace", help="Pinecone namespace for this contract", default=None)
    parser.add_argument("--skip-ingest", action="store_true", help="Skip ingestion if already indexed")
    
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        sys.exit(1)
        
    contract_name = os.path.basename(pdf_path).replace(".pdf", "")
    namespace = args.namespace or f"contract_{contract_name.lower().replace(' ', '_')}"
    
    print(f"--- Starting DocuMind Audit for: {contract_name} ---")
    
    # --- PHASE 1: INGESTION ---
    if not args.skip_ingest:
        print("\n[Phase 1] Ingesting Document...")
        try:
            processor = PDFProcessor()
            chunks = processor.parse_pdf(pdf_path)
            print(f"Parsed {len(chunks)} chunks.")
            
            vs_manager = VectorStoreManager(namespace=namespace)
            vs_manager.upsert_chunks(chunks)
            print("Ingestion Complete.")
        except Exception as e:
            print(f"Ingestion failed: {e}")
            sys.exit(1)
    else:
        print("\n[Phase 1] Skipping Ingestion (User Requested)")

    # --- PHASE 2: AUDIT LOOP ---
    print("\n[Phase 2] Running Critic-Reflector Audit Loop...")
    workflow = AuditWorkflow()
    app = workflow.build_graph()
    
    # Ideally, we iterate over all clauses. For CLI demo, we'll fetch all chunks 
    # (or you'd use a separate logic to list clauses to check).
    # Here we simulate valid clauses to check by re-reading the PDF structure momentarily
    # or assuming we check a specific list. 
    # For this implementation, let's re-parse to get the clause list to iterate over.
    processor = PDFProcessor()
    chunks = processor.parse_pdf(pdf_path)
    
    # Filter for chunks that look like clause definitions
    clauses_to_check = [c for c in chunks if c['clause_id'] != "General"]
    print(f"identified {len(clauses_to_check)} specific clauses to audit.")
    
    audit_findings = []
    
    for i, clause in enumerate(clauses_to_check):
        print(f"Analyzing Clause {clause['clause_id']} ({i+1}/{len(clauses_to_check)})...")
        
        initial_state = {
            "clause": clause,
            "contract_namespace": namespace,
            "critic_finding": None,
            "verification_result": None,
            "attempts": 0,
            "final_output": None
        }
        
        try:
            # Run the LangGraph
            final_state = app.invoke(initial_state)
            
            # Extract finding from final state (critic_finding is the last output)
            if final_state.get('critic_finding'):
                audit_findings.append(final_state['critic_finding'])
                
        except Exception as e:
            print(f"Error auditing clause {clause['clause_id']}: {e}")

    # --- PHASE 3: REPORTING ---
    print("\n[Phase 3] Generating Compliance Report...")
    summarizer = SummarizerAgent()
    report_md = summarizer.generate_report(contract_name, audit_findings)
    
    output_filename = f"audit_report_{contract_name}.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"Done! Report saved to: {output_filename}")

if __name__ == "__main__":
    main()
