import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_SIZE = 3072
LLM_MODEL = "gpt-4o-mini"
COLLECTION_NAME = "my_documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
