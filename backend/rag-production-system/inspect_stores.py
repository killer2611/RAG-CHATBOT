import sqlite3
import json

print("=== PARENT STORE ===")
conn = sqlite3.connect('data/parent_store/parents.sqlite3')
rows = conn.execute('SELECT DISTINCT source_id, metadata_json FROM parents LIMIT 20').fetchall()
for source_id, meta_json in rows:
    meta = json.loads(meta_json)
    sname = meta.get('source_name', 'unknown')
    print(f"source_id={source_id} | source_name={sname}")

counts = conn.execute('SELECT source_id, COUNT(*) FROM parents GROUP BY source_id').fetchall()
print("\n=== PARENT CHUNK COUNTS PER SOURCE ===")
for s, c in counts:
    print(f"  {s}: {c} parent chunks")
conn.close()

print("\n=== CHROMA VECTORSTORE ===")
import chromadb
client = chromadb.PersistentClient(path='data/vectorstore')
collections = client.list_collections()
print(f"Collections: {[c.name for c in collections]}")
for col in collections:
    count = col.count()
    print(f"  {col.name}: {count} embeddings")
    # Peek at metadata
    if count > 0:
        peek = col.peek(limit=5)
        for i, meta in enumerate(peek.get('metadatas', [])):
            print(f"    chunk {i}: source_id={meta.get('source_id','?')} source_name={meta.get('source_name','?')}")
