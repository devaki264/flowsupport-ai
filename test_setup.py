# test_setup.py
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import QueryCategory, DocumentChunk
from dotenv import load_dotenv

load_dotenv()

print("🔧 Testing setup...\n")

# Test Pydantic models
try:
    chunk = DocumentChunk(
        text="This is a test document chunk about Wispr Flow.",
        source="test.pdf",
        page=1,
        chunk_id=0,
        category=QueryCategory.PRODUCT
    )
    print(f"✅ Pydantic models working!")
    print(f"   Created chunk: {chunk.source}, Page {chunk.page}\n")
except Exception as e:
    print(f"❌ Pydantic models failed: {e}\n")

# Test imports
try:
    import google.generativeai as genai
    print("✅ Google Generative AI SDK installed")
except Exception as e:
    print(f"❌ Google Generative AI SDK missing: {e}")

try:
    import chromadb
    print("✅ ChromaDB installed")
except:
    print("❌ ChromaDB missing")

try:
    import streamlit
    print("✅ Streamlit installed")
except:
    print("❌ Streamlit missing")

# Test API key
api_key = os.getenv("GOOGLE_API_KEY")
if api_key and api_key != "your_key_here":
    print("✅ Gemini API key found\n")
    
    # Quick API test
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content("Say 'Hello!' in one sentence")
        print(f"✅ Gemini API working! Response: {response.text[:50]}...\n")
    except Exception as e:
        print(f"⚠️  API key set but test failed: {e}\n")
else:
    print("⚠️  Gemini API key not set in .env\n")

print("🎉 Setup check complete!")