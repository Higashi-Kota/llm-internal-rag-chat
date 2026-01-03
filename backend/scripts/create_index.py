#!/usr/bin/env python
"""CLI script for document indexing.

Usage:
    python scripts/create_index.py                    # Index from default directory
    python scripts/create_index.py --path /path/to/docs
    python scripts/create_index.py --clear            # Clear existing index first
    python scripts/create_index.py --status           # Show index status
"""

import argparse
import sys
from pathlib import Path

# Add backend/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mermaid_llm.rag import get_indexer, rag_settings
from mermaid_llm.rag.indexer import IndexResult


def show_status() -> None:
    """Show current index status."""
    indexer = get_indexer()
    count = indexer.get_document_count()

    print("=== Index Status ===")
    print(f"Document chunks: {count}")
    print(f"ChromaDB directory: {rag_settings.chroma_path}")
    print(f"Documents directory: {rag_settings.docs_path}")
    print(f"Embedding provider: {rag_settings.embedding_provider}")
    print(f"Embedding model: {rag_settings.embedding_model}")


def index_documents(
    path: Path | None = None,
    clear: bool = False,
) -> IndexResult:
    """Index documents from a directory.

    Args:
        path: Directory containing documents. Defaults to config.
        clear: Whether to clear existing index first.

    Returns:
        IndexResult with statistics.
    """
    indexer = get_indexer()
    docs_path = path or rag_settings.docs_path

    print(f"Indexing documents from: {docs_path}")
    if clear:
        print("Clearing existing index...")

    result = indexer.index_documents(
        docs_dir=docs_path,
        clear_existing=clear,
    )

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index documents for RAG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Path to documents directory (default: from config)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing index before indexing",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show index status and exit",
    )

    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    # Validate path if provided
    if args.path and not args.path.exists():
        print(f"Error: Directory does not exist: {args.path}", file=sys.stderr)
        return 1

    # Index documents
    try:
        result = index_documents(path=args.path, clear=args.clear)
    except Exception as e:
        print(f"Error during indexing: {e}", file=sys.stderr)
        return 1

    # Print results
    print("\n=== Indexing Complete ===")
    print(f"Documents indexed: {result.indexed_count}")
    print(f"Chunks created: {result.chunk_count}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("\nIndex ready for querying.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
