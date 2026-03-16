"""Text extraction from PDF, Word, and HTML files."""

from fastapi import UploadFile


async def extract_text(file: UploadFile) -> str:
    """Extract plain text from an uploaded file based on its content type."""
    # TODO: implement PDF extraction (PyMuPDF / pdfplumber)
    # TODO: implement Word extraction (python-docx)
    # TODO: implement HTML extraction
    raise NotImplementedError("Text extraction not yet implemented")
