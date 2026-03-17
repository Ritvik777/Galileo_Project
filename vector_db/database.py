from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, EMBEDDING_SIZE
from vector_db.embeddings import get_embedding_model
from vector_db.chunker import chunk_text

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def setup_collection():
    try:
        collections = [c.name for c in qdrant_client.get_collections().collections]
    except Exception as exc:
        raise RuntimeError(f"Qdrant connection failed: {exc}") from exc

    if COLLECTION_NAME in collections:
        info = qdrant_client.get_collection(COLLECTION_NAME)
        if info.config.params.vectors.size != EMBEDDING_SIZE:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' vector size mismatch. "
                f"Expected {EMBEDDING_SIZE}, found {info.config.params.vectors.size}. "
                "Use a new COLLECTION_NAME or recreate this collection manually."
            )
    if COLLECTION_NAME not in collections:
        try:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to create Qdrant collection: {exc}") from exc


def get_vector_store():
    setup_collection()
    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        embedding=get_embedding_model(),
    )


def add_documents(texts: list[str]) -> int:
    try:
        store = get_vector_store()
        all_chunks = []
        for text in texts:
            all_chunks.extend(chunk_text(text))
        if not all_chunks:
            return 0
        store.add_texts(all_chunks)
        return len(all_chunks)
    except Exception as exc:
        raise RuntimeError(f"Failed to add documents to Qdrant: {exc}") from exc


def search_with_scores(query: str, top_k: int = 4) -> list[tuple[str, float]]:
    try:
        store = get_vector_store()
        results = store.similarity_search_with_score(query, k=top_k)
        return [(doc.page_content, score) for doc, score in results]
    except Exception:
        return []


def get_document_count() -> int:
    try:
        return qdrant_client.get_collection(COLLECTION_NAME).points_count
    except Exception:
        return 0
