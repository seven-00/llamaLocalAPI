# app/pdf_handler.py
from pypdf import PdfReader
import io


def ProcessPdf(binary_pdf):
    """Process PDF binary data and extract text."""
    pdf_file = io.BytesIO(binary_pdf)
    pdf_reader = PdfReader(pdf_file)

    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    if not text.strip():
        raise ValueError("Unable to extract text from the PDF")

    return text
