from vector_db import add_documents, get_document_count, extract_text_from_pdf


def get_doc_count() -> int:
    return get_document_count()


def add_text_documents(raw_text: str) -> int:
    lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
    if not lines:
        return 0
    return add_documents(lines)


def add_pdf_document(pdf_file) -> int:
    return add_documents([extract_text_from_pdf(pdf_file)])
