"""Tests for document loaders."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mermaid_llm.rag.loaders import (
    SUPPORTED_EXTENSIONS,
    load_directory,
    load_document,
    load_docx,
    load_pdf,
    load_pptx,
    load_txt,
    load_xlsx,
)


class TestLoadTxt:
    """Tests for TXT loader."""

    def test_load_txt_basic(self, tmp_path: Path):
        """Test loading a basic TXT file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!\nThis is a test.", encoding="utf-8")

        docs = load_txt(test_file)

        assert len(docs) == 1
        assert docs[0].page_content == "Hello, World!\nThis is a test."
        assert docs[0].metadata["filename"] == "test.txt"
        assert docs[0].metadata["source"] == str(test_file)

    def test_load_txt_empty(self, tmp_path: Path):
        """Test loading an empty TXT file returns no documents."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        docs = load_txt(test_file)

        assert len(docs) == 0

    def test_load_txt_whitespace_only(self, tmp_path: Path):
        """Test loading whitespace-only TXT file returns no documents."""
        test_file = tmp_path / "whitespace.txt"
        test_file.write_text("   \n\t\n   ", encoding="utf-8")

        docs = load_txt(test_file)

        assert len(docs) == 0

    def test_load_txt_japanese(self, tmp_path: Path):
        """Test loading Japanese text."""
        test_file = tmp_path / "japanese.txt"
        test_file.write_text("これはテストです。日本語のテキスト。", encoding="utf-8")

        docs = load_txt(test_file)

        assert len(docs) == 1
        assert "これはテストです" in docs[0].page_content


class TestLoadPdf:
    """Tests for PDF loader."""

    def test_load_pdf_with_mock(self):
        """Test PDF loading with mocked PdfReader."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Page 1 content"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("pypdf.PdfReader", return_value=mock_reader):
            docs = load_pdf(Path("/fake/test.pdf"))

        assert len(docs) == 1
        assert docs[0].page_content == "Page 1 content"
        assert docs[0].metadata["page"] == 1
        assert docs[0].metadata["total_pages"] == 1

    def test_load_pdf_multiple_pages(self):
        """Test PDF with multiple pages."""
        pages = []
        for i in range(3):
            page = MagicMock()
            page.extract_text.return_value = f"Content of page {i + 1}"
            pages.append(page)

        mock_reader = MagicMock()
        mock_reader.pages = pages

        with patch("pypdf.PdfReader", return_value=mock_reader):
            docs = load_pdf(Path("/fake/multi.pdf"))

        assert len(docs) == 3
        assert docs[0].metadata["page"] == 1
        assert docs[1].metadata["page"] == 2
        assert docs[2].metadata["page"] == 3
        assert docs[0].metadata["total_pages"] == 3

    def test_load_pdf_empty_page(self):
        """Test PDF with empty pages are skipped."""
        pages = [MagicMock(), MagicMock()]
        pages[0].extract_text.return_value = "Content"
        pages[1].extract_text.return_value = "   "  # Empty

        mock_reader = MagicMock()
        mock_reader.pages = pages

        with patch("pypdf.PdfReader", return_value=mock_reader):
            docs = load_pdf(Path("/fake/partial.pdf"))

        assert len(docs) == 1
        assert docs[0].metadata["page"] == 1


class TestLoadDocx:
    """Tests for DOCX loader."""

    def test_load_docx_with_mock(self):
        """Test DOCX loading with mocked python-docx."""
        mock_paragraphs = [
            MagicMock(text="First paragraph"),
            MagicMock(text="Second paragraph"),
            MagicMock(text=""),  # Empty paragraph
        ]

        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs

        with patch("docx.Document", return_value=mock_doc):
            docs = load_docx(Path("/fake/test.docx"))

        assert len(docs) == 1
        assert "First paragraph" in docs[0].page_content
        assert "Second paragraph" in docs[0].page_content
        assert docs[0].metadata["filename"] == "test.docx"

    def test_load_docx_empty(self):
        """Test loading empty DOCX returns no documents."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = []

        with patch("docx.Document", return_value=mock_doc):
            docs = load_docx(Path("/fake/empty.docx"))

        assert len(docs) == 0


class TestLoadPptx:
    """Tests for PPTX loader."""

    def test_load_pptx_with_mock(self):
        """Test PPTX loading with mocked python-pptx."""
        # Create mock shapes with text
        mock_shape1 = MagicMock()
        mock_shape1.text = "Title text"

        mock_shape2 = MagicMock()
        mock_shape2.text = "Body text"

        mock_slide = MagicMock()
        mock_slide.shapes = [mock_shape1, mock_shape2]

        mock_prs = MagicMock()
        mock_prs.slides = [mock_slide]

        with patch("pptx.Presentation", return_value=mock_prs):
            docs = load_pptx(Path("/fake/test.pptx"))

        assert len(docs) == 1
        assert "Title text" in docs[0].page_content
        assert "Body text" in docs[0].page_content
        assert docs[0].metadata["slide"] == 1
        assert docs[0].metadata["total_slides"] == 1

    def test_load_pptx_multiple_slides(self):
        """Test PPTX with multiple slides."""
        slides = []
        for i in range(2):
            shape = MagicMock()
            shape.text = f"Slide {i + 1} content"
            slide = MagicMock()
            slide.shapes = [shape]
            slides.append(slide)

        mock_prs = MagicMock()
        mock_prs.slides = slides

        with patch("pptx.Presentation", return_value=mock_prs):
            docs = load_pptx(Path("/fake/multi.pptx"))

        assert len(docs) == 2
        assert docs[0].metadata["slide"] == 1
        assert docs[1].metadata["slide"] == 2


class TestLoadXlsx:
    """Tests for XLSX loader."""

    def test_load_xlsx_with_mock(self):
        """Test XLSX loading with mocked openpyxl."""
        mock_sheet = MagicMock()
        mock_sheet.iter_rows.return_value = [
            ("Header1", "Header2"),
            ("Value1", "Value2"),
        ]

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_wb.__getitem__ = MagicMock(return_value=mock_sheet)

        with patch("openpyxl.load_workbook", return_value=mock_wb):
            docs = load_xlsx(Path("/fake/test.xlsx"))

        assert len(docs) == 1
        assert "Header1" in docs[0].page_content
        assert "Value1" in docs[0].page_content
        assert docs[0].metadata["sheet"] == "Sheet1"

    def test_load_xlsx_multiple_sheets(self):
        """Test XLSX with multiple sheets."""
        mock_sheets = {}
        for name in ["Sheet1", "Sheet2"]:
            mock_sheet = MagicMock()
            mock_sheet.iter_rows.return_value = [
                (f"{name} Data",),
            ]
            mock_sheets[name] = mock_sheet

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1", "Sheet2"]
        mock_wb.__getitem__ = lambda self, key: mock_sheets[key]

        with patch("openpyxl.load_workbook", return_value=mock_wb):
            docs = load_xlsx(Path("/fake/multi.xlsx"))

        assert len(docs) == 2
        assert docs[0].metadata["sheet"] == "Sheet1"
        assert docs[1].metadata["sheet"] == "Sheet2"


class TestLoadDocument:
    """Tests for load_document function."""

    def test_load_txt(self, tmp_path: Path):
        """Test load_document dispatches to correct loader for TXT."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content", encoding="utf-8")

        docs = load_document(test_file)

        assert len(docs) == 1
        assert docs[0].page_content == "Content"

    def test_unsupported_extension(self, tmp_path: Path):
        """Test load_document raises error for unsupported extension."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("Content", encoding="utf-8")

        with pytest.raises(ValueError, match="Unsupported file extension"):
            load_document(test_file)

    def test_supported_extensions(self):
        """Test all expected extensions are supported."""
        expected = {".pdf", ".docx", ".pptx", ".xlsx", ".txt"}
        assert expected == SUPPORTED_EXTENSIONS


class TestLoadDirectory:
    """Tests for load_directory function."""

    def test_load_directory_txt_files(self, tmp_path: Path):
        """Test loading TXT files from directory."""
        (tmp_path / "file1.txt").write_text("Content 1", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("Content 2", encoding="utf-8")

        with patch("mermaid_llm.rag.loaders.rag_settings") as mock_settings:
            mock_settings.docs_path = tmp_path
            docs = list(load_directory(tmp_path))

        assert len(docs) == 2

    def test_load_directory_recursive(self, tmp_path: Path):
        """Test recursive loading from subdirectories."""
        (tmp_path / "file1.txt").write_text("Root content", encoding="utf-8")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("Subdir content", encoding="utf-8")

        with patch("mermaid_llm.rag.loaders.rag_settings") as mock_settings:
            mock_settings.docs_path = tmp_path
            docs = list(load_directory(tmp_path, recursive=True))

        assert len(docs) == 2

    def test_load_directory_non_recursive(self, tmp_path: Path):
        """Test non-recursive loading ignores subdirectories."""
        (tmp_path / "file1.txt").write_text("Root content", encoding="utf-8")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("Subdir content", encoding="utf-8")

        with patch("mermaid_llm.rag.loaders.rag_settings") as mock_settings:
            mock_settings.docs_path = tmp_path
            docs = list(load_directory(tmp_path, recursive=False))

        assert len(docs) == 1

    def test_load_directory_not_exists(self, tmp_path: Path):
        """Test loading from non-existent directory raises error."""
        non_existent = tmp_path / "not_exists"

        with pytest.raises(ValueError, match="Directory does not exist"):
            list(load_directory(non_existent))

    def test_load_directory_ignores_unsupported(self, tmp_path: Path):
        """Test unsupported file types are ignored."""
        (tmp_path / "file1.txt").write_text("Content", encoding="utf-8")
        (tmp_path / "file2.xyz").write_text("Unsupported", encoding="utf-8")

        with patch("mermaid_llm.rag.loaders.rag_settings") as mock_settings:
            mock_settings.docs_path = tmp_path
            docs = list(load_directory(tmp_path))

        assert len(docs) == 1
