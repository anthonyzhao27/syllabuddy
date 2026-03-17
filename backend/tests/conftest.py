import fitz
import pytest
from docx import Document
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def create_fixtures() -> None:
    """Generate small test fixture files."""
    FIXTURES.mkdir(exist_ok=True)

    # PDF — text must be >= 50 chars so vision fallback is NOT triggered
    pdf_path = FIXTURES / "sample.pdf"
    if not pdf_path.exists():
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "CS 101 — Spring 2025 Syllabus\n"
            "Homework 1 due January 30, 2025\n"
            "Midterm Exam on March 10, 2025\n"
            "Final Project due April 20, 2025",
        )
        doc.save(str(pdf_path))
        doc.close()

    # DOCX
    docx_path = FIXTURES / "sample.docx"
    if not docx_path.exists():
        doc = Document()
        doc.add_paragraph("Midterm Exam — March 10, 2025")
        table = doc.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Quiz 1"
        table.rows[0].cells[1].text = "Feb 14, 2025"
        doc.save(str(docx_path))

    # HTML
    html_path = FIXTURES / "sample.html"
    if not html_path.exists():
        html_path.write_text(
            "<html><body><h1>CS 101</h1>"
            "<p>Final Project due April 20, 2025</p>"
            "<script>var x = 1;</script>"
            "</body></html>"
        )
