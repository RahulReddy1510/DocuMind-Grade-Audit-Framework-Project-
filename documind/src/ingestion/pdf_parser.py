from typing import List, Dict, Optional
import pymupdf4llm
import re

class PDFProcessor:
    """
    Handles the ingestion of PDF documents, converting them to structured text
    with metadata suitable for vector database indexing.
    """
    def __init__(self):
        # Regex for detecting common legal clause patterns
        # Matches: "1.", "1.1", "Article 1", "SECTION 2", "(a)", etc.
        self.clause_pattern = re.compile(r'^(?:Article\s+\d+|Section\s+\d+|Clause\s+\d+|\d+\.\d+|\(\w\))', re.IGNORECASE)
        self.header_pattern = re.compile(r'^#+\s+(.*)')

    def parse_pdf(self, file_path: str) -> List[Dict]:
        """
        Parses a PDF file and returns a list of chunks with metadata.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of dicts: { "page_no": int, "section": str, "clause_id": str, "raw_text": str }
        """
        try:
            # Get markdown chunks with page metadata
            md_chunks = pymupdf4llm.to_markdown(file_path, page_chunks=True)
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return []
        
        processed_chunks = []
        
        for chunk in md_chunks:
            page_num = chunk['metadata']['page'] + 1 # 1-indexed for human readability
            text = chunk['text']
            
            # Split page content into semantic blocks (clauses/sections)
            page_clauses = self._split_into_clauses(text, page_num)
            processed_chunks.extend(page_clauses)
            
        return processed_chunks

    def _split_into_clauses(self, text: str, page_num: int) -> List[Dict]:
        """
        Parses markdown text to split by clauses/sections while maintaining context.
        """
        chunks = []
        lines = text.split('\n')
        
        current_clause_id = "General"
        current_section = "General"
        buffer_text = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 1. Check for Headers (Section detection)
            header_match = self.header_pattern.match(line)
            if header_match:
                # If we hit a new header, flush previous buffer
                if buffer_text:
                    self._add_chunk(chunks, page_num, current_section, current_clause_id, buffer_text)
                    buffer_text = []
                
                current_section = header_match.group(1)
                # Reset clause ID on new major section? Depends on document. Keeping it safe.
                # buffer_text.append(line) # Keep header in text? Yes.
            
            # 2. Check for Clause delimiters
            clause_match = self.clause_pattern.match(line)
            if clause_match:
                 # If we hit a new clause, flush previous buffer
                if buffer_text:
                    self._add_chunk(chunks, page_num, current_section, current_clause_id, buffer_text)
                    buffer_text = []
                
                current_clause_id = clause_match.group(0)
            
            buffer_text.append(line)
            
        # Flush remaining buffer
        if buffer_text:
            self._add_chunk(chunks, page_num, current_section, current_clause_id, buffer_text)
            
        return chunks

    def _add_chunk(self, chunks_list: List[Dict], page: int, section: str, clause: str, text_lines: List[str]):
        """Helper to append a chunk."""
        content = "\n".join(text_lines)
        if len(content.strip()) < 10: # Skip noise/tiny chunks
            return
            
        chunks_list.append({
            "page_no": page,
            "section": section,
            "clause_id": clause,
            "raw_text": content
        })

if __name__ == "__main__":
    # Smoke test
    import sys
    if len(sys.argv) > 1:
        processor = PDFProcessor()
        results = processor.parse_pdf(sys.argv[1])
        for r in results[:3]:
            print(r)
