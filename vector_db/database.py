from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from config import QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME, EMBEDDING_SIZE
from vector_db.embeddings import get_embedding_model
from vector_db.chunker import chunk_text


qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def setup_collection():
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if COLLECTION_NAME in collections:
        info = qdrant_client.get_collection(COLLECTION_NAME)
        if info.config.params.vectors.size != EMBEDDING_SIZE:
            qdrant_client.delete_collection(COLLECTION_NAME)
            collections.remove(COLLECTION_NAME)
    if COLLECTION_NAME not in collections:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_SIZE, distance=Distance.COSINE),
        )


def get_vector_store():
    setup_collection()
    return QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME,
        embedding=get_embedding_model(),
    )


def add_documents(texts: list[str]) -> int:
    store = get_vector_store()
    all_chunks = []
    for text in texts:
        all_chunks.extend(chunk_text(text))
    store.add_texts(all_chunks)
    return len(all_chunks)


def search_with_scores(query: str, top_k: int = 4) -> list[tuple[str, float]]:
    store = get_vector_store()
    results = store.similarity_search_with_score(query, k=top_k)
    return [(doc.page_content, score) for doc, score in results]


def get_document_count() -> int:
    try:
        return qdrant_client.get_collection(COLLECTION_NAME).points_count
    except Exception:
        return 0
