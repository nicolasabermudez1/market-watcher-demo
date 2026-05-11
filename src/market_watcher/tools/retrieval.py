"""Chroma vector store setup and semantic retrieval tool."""

import json
from pathlib import Path
from typing import Any

import chromadb
from agents import function_tool

from market_watcher.config import FIXTURES_DIR, USE_CHROMA

_client: Any = None
_collection: Any = None
COLLECTION_NAME = "market_watcher_corpus"


def get_chroma_client() -> Any:
    global _client
    if _client is None:
        _client = chromadb.Client()  # in-memory; rebuilt on each app start
    return _client


def build_index() -> None:
    """Ingest all fixture data into Chroma. Called at app startup."""
    if not USE_CHROMA:
        return

    global _collection
    client = get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    _collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    docs, ids, metas = [], [], []

    # Ingest supplier profiles
    for sup_file in (FIXTURES_DIR / "suppliers" / "cloud_infrastructure").glob("*.json"):
        with open(sup_file) as f:
            data = json.load(f)
        text = (
            f"Supplier: {data['name']}. Category: {data['category']}. "
            f"Status: {data['status']}. Region: {data['region']}. "
            f"Risks: {'; '.join(r['description'] for r in data.get('risks', []))}. "
            f"Certifications: {', '.join(c['type'] for c in data.get('certifications', []))}."
        )
        docs.append(text)
        ids.append(f"supplier_{data['supplier_id']}")
        metas.append({"type": "supplier", "supplier_id": data["supplier_id"], "name": data["name"]})

    # Ingest news
    with open(FIXTURES_DIR / "mock_news_seed.json") as f:
        news = json.load(f)
    for item in news:
        docs.append(f"{item['headline']}. {item['summary']}")
        ids.append(item["id"])
        metas.append({"type": "news", "date": item["date"], "source": item["source"], "risk_signal": str(item["risk_signal"])})

    # Ingest category strategy (chunked)
    strat_path = FIXTURES_DIR / "category_strategy.md"
    if strat_path.exists():
        lines = strat_path.read_text(encoding="utf-8").splitlines()
        chunks = [" ".join(lines[i:i+20]) for i in range(0, len(lines), 20)]
        for j, chunk in enumerate(chunks):
            if chunk.strip():
                docs.append(chunk)
                ids.append(f"strategy_chunk_{j}")
                metas.append({"type": "strategy", "chunk": j})

    if docs:
        _collection.add(documents=docs, ids=ids, metadatas=metas)


@function_tool
def semantic_retrieve(query: str, k: int = 5) -> list[dict]:
    """Perform semantic search over the indexed supplier/news/strategy corpus.
    Returns the top-k most relevant passages with source metadata.
    """
    if not USE_CHROMA or _collection is None:
        return [{"text": "Chroma index not available — use mock fixtures directly.", "meta": {}}]

    results = _collection.query(query_texts=[query], n_results=min(k, 10))
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append({"text": doc, "meta": meta})
    return output
