from io import BytesIO


def extract_text_from_bytes(name: str, raw: bytes) -> str:
    """Extract UTF-8, PDF, or DOCX text from uploaded file bytes."""
    lowered = name.lower()
    if lowered.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    if lowered.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(BytesIO(raw)).paragraphs)
    return raw.decode("utf-8", errors="ignore")


def extract_text(uploaded_file) -> str:
    """Extract text from a Streamlit upload."""
    return extract_text_from_bytes(uploaded_file.name, uploaded_file.getvalue())
