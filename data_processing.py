# src/data_processing.py
import pdfplumber
from pathlib import Path
from typing import List, Dict
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import DocumentChunk, QueryCategory

class DocumentProcessor:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        
    def extract_pdf_text(self, pdf_path: Path) -> Dict:
        """Extract text with metadata from PDF"""
        print(f"  📄 Processing: {pdf_path.name}")
        
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pages.append({
                        "page_number": i + 1,
                        "content": text
                    })
            
        return {
            "source": pdf_path.name,
            "pages": pages,
            "total_pages": len(pages)
        }
    
    def chunk_document(self, doc: Dict, chunk_size: int = 500, overlap: int = 50) -> List[DocumentChunk]:
        """Smart chunking with context preservation"""
        chunks = []
        
        for page in doc["pages"]:
            text = page["content"]
            words = text.split()
            
            # Create overlapping chunks
            for i in range(0, len(words), chunk_size - overlap):
                chunk_text = " ".join(words[i:i + chunk_size])
                
                # Skip very short chunks
                if len(chunk_text) < 50:
                    continue
                
                # Categorize based on keywords
                category = self._categorize_chunk(chunk_text)
                
                chunks.append(
                    DocumentChunk(
                        text=chunk_text,
                        source=doc["source"],
                        page=page["page_number"],
                        chunk_id=len(chunks),
                        category=category
                    )
                )
        
        return chunks
    
    def _categorize_chunk(self, text: str) -> QueryCategory:
        """Categorize chunk based on content"""
        text_lower = text.lower()
        
        # Billing keywords
        if any(word in text_lower for word in ["trial", "subscription", "pricing", "billing", "payment", "upgrade", "pro plan", "cancel"]):
            return QueryCategory.BILLING
        
        # Technical keywords
        if any(word in text_lower for word in ["troubleshoot", "error", "not working", "issue", "fix", "desktop", "ios", "install"]):
            return QueryCategory.TECHNICAL
        
        # Account keywords
        if any(word in text_lower for word in ["account", "sign up", "login", "password", "delete"]):
            return QueryCategory.ACCOUNT
        
        # Product keywords
        if any(word in text_lower for word in ["feature", "use case", "workflow", "app", "integration", "dictation"]):
            return QueryCategory.PRODUCT
        
        return QueryCategory.GENERAL
    
    def process_all_documents(self) -> List[DocumentChunk]:
        """Process all PDFs in data directory"""
        all_chunks = []
        
        pdf_files = list(self.data_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("❌ No PDF files found in data/raw/")
            return []
        
        print(f"\n📚 Found {len(pdf_files)} PDF files")
        print("🔄 Processing documents...\n")
        
        for pdf_file in pdf_files:
            try:
                doc = self.extract_pdf_text(pdf_file)
                chunks = self.chunk_document(doc)
                all_chunks.extend(chunks)
                print(f"     ✅ Extracted {len(chunks)} chunks\n")
            except Exception as e:
                print(f"     ❌ Error processing {pdf_file.name}: {e}\n")
        
        # Save processed chunks
        output_path = Path("data/processed/document_chunks.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Pydantic models to dicts for JSON serialization
        chunks_dict = [chunk.dict() for chunk in all_chunks]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Processed {len(all_chunks)} total chunks from {len(pdf_files)} documents")
        print(f"💾 Saved to: {output_path}\n")
        
        return all_chunks

if __name__ == "__main__":
    processor = DocumentProcessor()
    chunks = processor.process_all_documents()
    
    # Show some stats
    if chunks:
        categories = {}
        for chunk in chunks:
            cat = chunk.category.value if chunk.category else "general"
            categories[cat] = categories.get(cat, 0) + 1
        
        print("📊 Chunk Distribution:")
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count} chunks")