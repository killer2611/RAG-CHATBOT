"""
Verify that retrieval for microLED questions finds the correct document.
"""
import sys
sys.path.insert(0, '.')

from app.core.config import get_settings
from app.rag.retriever import HierarchicalRetriever

settings = get_settings()
retriever = HierarchicalRetriever(settings)

questions = [
    "What is the main focus of this paper?",
    "What substrate do light-emitting GaN devices typically use, and why?",
    "What circuit design is commonly used to drive individual microLED pixels?",
    "What are the three key requirements for mass transfer technology in microLED display manufacturing?",
    "Why is silicon preferred for electronic GaN devices instead of sapphire?",
]

for q in questions:
    print(f"\n=== QUERY: {q[:60]}... ===")
    results = retriever.retrieve(q)
    for i, r in enumerate(results):
        print(f"  [{i}] score={r.score:.3f} source={r.document.metadata.get('source_name','?')} source_id={r.document.metadata.get('source_id','?')[:20]}")
        print(f"       excerpt: {r.document.page_content[:200].replace(chr(10), ' ')}")
