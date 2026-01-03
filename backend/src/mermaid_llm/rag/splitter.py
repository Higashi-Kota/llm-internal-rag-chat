"""Text splitter configuration with Japanese language support."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import rag_settings

# Japanese-aware separators
# Order matters: prefer splitting on larger units first
JAPANESE_SEPARATORS = [
    "\n\n",  # Double newline (paragraph)
    "\n",  # Single newline
    "。",  # Japanese period
    "、",  # Japanese comma
    "！",  # Japanese exclamation
    "？",  # Japanese question
    ".",  # English period
    ",",  # English comma
    " ",  # Space
    "",  # Character-level (fallback)
]


def create_text_splitter(
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> RecursiveCharacterTextSplitter:
    """Create a text splitter with Japanese language support.

    Args:
        chunk_size: Maximum size of chunks. Defaults to config value.
        chunk_overlap: Overlap between chunks. Defaults to config value.

    Returns:
        Configured RecursiveCharacterTextSplitter instance.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or rag_settings.chunk_size,
        chunk_overlap=chunk_overlap or rag_settings.chunk_overlap,
        separators=JAPANESE_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )


# Default splitter instance
text_splitter = create_text_splitter()
