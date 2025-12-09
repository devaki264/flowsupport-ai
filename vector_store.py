# src/vector_store.py
import chromadb
from chromadb.utils import embedding_functions
import json
from pathlib import Path
from typing import List, Dict
import sys

sys.path.insert(0, str(Path(__file__).parent))
from models import DocumentChunk

class VectorStore:
    """ChromaDB vector store for document retrieval"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence transformers for embeddings
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="flow_docs",
            embedding_function=self.embedding_function,
            metadata={"description": "Wispr Flow documentation"}
        )
        
        print("🔧 Initializing vector store...")
        print("✅ Vector store ready!\n")
    
    def load_documents(self, chunks: List[DocumentChunk]):
        """Load document chunks from old JSON structure"""
        
        texts = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            texts.append(chunk.text)
            metadatas.append({
                "source": chunk.source,
                "page": chunk.page,
                "chunk_id": chunk.chunk_id,
                "category": chunk.category or "general"
            })
            ids.append(str(chunk.chunk_id))
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_texts,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        """Search for relevant documents"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Return in format compatible with old agent
        return {
            "documents": results['documents'][0],
            "metadatas": results['metadatas'][0],
            "distances": results['distances'][0]
        }
    
    def clear(self):
        """Clear all documents from collection"""
        self.client.delete_collection("flow_docs")
        self.collection = self.client.create_collection(
            name="flow_docs",
            embedding_function=self.embedding_function
        )

if __name__ == "__main__":
    # Initialize vector store
    vector_store = VectorStore()
    
    # Path to chunks file
    chunks_path = Path(__file__).parent.parent / "data" / "processed" / "document_chunks.json"
    
    if not chunks_path.exists():
        print(f"❌ Chunks file not found at: {chunks_path}")
        print("Please run: python src\\data_processing.py")
        exit(1)
    
    # Load chunks directly from JSON
    print(f"📥 Loading chunks from: {chunks_path}")
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    
    # Convert to DocumentChunk objects
    chunks = [DocumentChunk(**chunk) for chunk in chunks_data]
    
    print(f"📥 Loading {len(chunks)} chunks into vector store...")
    
    # Clear and reload
    vector_store.clear()
    vector_store.load_documents(chunks)
    
    print(f"✅ Loaded {len(chunks)} chunks into vector store\n")
    
    # Test search
    print("🔍 Testing search...\n")
    test_query = "How do I cancel my trial?"
    results = vector_store.search(test_query, n_results=3)
    
    print(f"Query: '{test_query}'")
    print(f"Found {len(results['documents'])} results:\n")
    
    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'],
        results['metadatas'],
        results['distances']
    ), 1):
        print(f"{i}. Source: {meta['source']} (Page {meta['page']})")
        print(f"   Relevance: {(1-dist)*100:.1f}%")
        print(f"   Preview: {doc[:100]}...")
        print()