from __future__ import annotations

from pathlib import Path

from django.utils.html import escape
from rest_framework.exceptions import ValidationError
from docx import Document
import markdown as md


SUPPORTED_EXTENSIONS = {'.md', '.markdown', '.txt', '.html', '.htm', '.docx'}


def convert_uploaded_file(upload) -> str:
    """
    Convert an uploaded document (docx/md/txt/html) into HTML string for storage.
    """
    extension = Path(upload.name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValidationError(f"不支持的文件类型：{extension}（仅支持 docx/md/txt/html）")

    if extension in {'.md', '.markdown'}:
        text = _read_text(upload)
        return md.markdown(text)

    if extension == '.txt':
        text = _read_text(upload)
        paragraphs = [f"<p>{escape(line) or '&nbsp;'}</p>" for line in text.splitlines()]
        return ''.join(paragraphs)

    if extension in {'.html', '.htm'}:
        return _read_text(upload, raw=True)

    # docx
    document = Document(upload)
    paragraphs = [f"<p>{escape(paragraph.text)}</p>" for paragraph in document.paragraphs if paragraph.text.strip()]
    return ''.join(paragraphs) or '<p></p>'


def _read_text(upload, raw: bool = False) -> str:
    upload.seek(0)
    data = upload.read()
    if raw:
        return data.decode('utf-8', errors='ignore')
    # strip BOM if any
    return data.decode('utf-8-sig', errors='ignore')
