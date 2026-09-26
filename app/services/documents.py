from io import BytesIO


def extract_text(uploaded_file) -> str:
    """Extract UTF-8, PDF, or DOCX text from a Streamlit upload."""
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    if name.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(BytesIO(raw)).paragraphs)
    return raw.decode("utf-8", errors="ignore")
