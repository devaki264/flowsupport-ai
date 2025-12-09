# test_processing.py
from pathlib import Path
import sys

sys.path.insert(0, 'src')

print("🔍 Checking data/raw folder...")
print()

raw_dir = Path("data/raw")

if not raw_dir.exists():
    print("❌ data/raw folder doesn't exist!")
    exit(1)

pdf_files = list(raw_dir.glob("*.pdf"))

print(f"📁 Found {len(pdf_files)} PDF files:")
for pdf in pdf_files:
    size_kb = pdf.stat().st_size / 1024
    print(f"   - {pdf.name} ({size_kb:.1f} KB)")

print()

if len(pdf_files) == 0:
    print("❌ No PDF files found in data/raw/")
    print("   Please add your Wispr Flow documentation PDFs to data/raw/")
    exit(1)

print("✅ Ready to process!")
print()
print("Now running data_processing.py...")
print("=" * 80)
print()

# Now run the actual processing
from src.data_processing import DocumentProcessor

processor = DocumentProcessor()
chunks = processor.process_all_documents()

print()
print(f"✅ DONE! Created {len(chunks)} chunks")