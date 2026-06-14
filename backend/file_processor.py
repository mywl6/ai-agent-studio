"""文件处理：校验、文本提取、图片编码"""
import base64
import json
import os
import re
from pathlib import Path
from typing import Optional

MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_IMAGE_SIZE = 10 * 1024 * 1024
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".html", ".css", ".json", ".xml", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".log", ".csv", ".sql",
    ".sh", ".bat", ".ps1", ".env", ".dockerfile",
    ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs",
    ".rb", ".php", ".swift", ".kt", ".scala", ".pl",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"}
DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}

SUPPORTED_EXTENSIONS = TEXT_EXTENSIONS | IMAGE_EXTENSIONS | DOC_EXTENSIONS


def validate_file(filename: str, content: bytes) -> Optional[str]:
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return f"不支持的文件类型: {ext}（支持：文本/图片/PDF/Office）"
    if ext in IMAGE_EXTENSIONS and len(content) > MAX_IMAGE_SIZE:
        return f"图片过大（{len(content)//1024//1024}MB），最大 {MAX_IMAGE_SIZE//1024//1024}MB"
    if len(content) > MAX_FILE_SIZE:
        return f"文件过大（{len(content)//1024//1024}MB），最大 {MAX_FILE_SIZE//1024//1024}MB"
    return None


def extract_text(content: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in TEXT_EXTENSIONS:
        return _read_text(content)
    if ext in IMAGE_EXTENSIONS:
        return f"[图片: {filename}]"
    if ext == ".pdf":
        return _extract_pdf(content)
    if ext == ".docx":
        return _extract_docx(content)
    return f"[文件: {filename}]（无法提取文本内容）"


def encode_image(content: bytes, filename: str) -> Optional[dict]:
    ext = Path(filename).suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return None
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp", ".bmp": "image/bmp",
        ".svg": "image/svg+xml",
    }
    mime = mime_map.get(ext, "image/png")
    b64 = base64.b64encode(content).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def _read_text(content: bytes) -> str:
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return content.decode("utf-8", errors="replace")


def _extract_pdf(content: bytes) -> str:
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        result = "\n".join(pages)
        return result if result.strip() else "[PDF: 无法提取文本内容（扫描件或图片型PDF）]"
    except ImportError:
        return "[PDF: 需要安装 PyPDF2 库才能提取文本]"
    except Exception as e:
        return f"[PDF 提取失败: {e}]"


def _extract_docx(content: bytes) -> str:
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs) if paragraphs else "[DOCX: 空文档]"
    except ImportError:
        return "[DOCX: 需要安装 python-docx 库才能提取文本]"
    except Exception as e:
        return f"[DOCX 提取失败: {e}]"


def describe_uploaded_files(files_data: list[dict]) -> str:
    if not files_data:
        return ""
    lines = ["\n\n[用户上传的文件]"]
    for f in files_data:
        size_str = _format_size(f.get("size", 0))
        lines.append(f"  - {f.get('filename', '未知')} ({size_str}, {f.get('mime_type', '未知')})")
        if f.get("text_content"):
            text = f["text_content"]
            if len(text) > 2000:
                text = text[:2000] + f"\n  ...（共 {len(text)} 字符，已截断）"
            lines.append(f"    内容:\n{text}")
    lines.append("[/用户上传的文件]")
    return "\n".join(lines)


def _format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    return f"{size/1024/1024:.1f}MB"