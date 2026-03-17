"""
vector_db/ — Everything related to the vector database
========================================================
  embeddings.py  → Google Gemini embedding model (text → vectors)
  chunker.py     → text splitting + PDF extraction
  database.py    → Qdrant: store, search, and manage documents
"""
from vector_db.database import add_documents, search_with_scores, get_document_count
from vector_db.chunker import extract_text_from_pdf
