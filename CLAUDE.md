# RAG Chat

ローカルRAGシステム - LangChain v1 × Ollama × ChromaDB

**Design Principles**: No custom hooks, useMemo, or useCallback. Initialize core in App.tsx, pass via props to containers.

## 構造

```
frontend/           # React 19 モノレポ (pnpm)
  apps/client-app/  # メインアプリ
backend/            # FastAPI + LangChain
  src/mermaid_llm/  # ソースコード
    rag/            # RAGモジュール
      providers/    # LLM/Embeddingプロバイダー (ollama, openai, anthropic, gemini)
  tests/            # pytest
  data/docs/        # ドキュメント格納ディレクトリ
```

## 開発コマンド

### フロントエンド

```bash
pnpm dev                    # 開発サーバー (5175)
pnpm build                  # ビルド
pnpm lint && pnpm typecheck # 検証
pnpm e2e                    # E2Eテスト
```

### バックエンド

```bash
cd backend
uv run fastapi dev src/mermaid_llm/main.py  # 開発 (8000)
uv run ruff check . && uv run pyright       # 検証
uv run pytest                                # テスト

# RAG操作
uv run python scripts/index_documents.py    # ドキュメントインデックス化
```

## コーディング規約

### フロントエンド

- Biome (lint/format)
- 状態管理: useSyncExternalStore
- TypeScript strict mode

### バックエンド

- ruff + pyright (strict)
- 非同期I/O (asyncpg, SQLAlchemy async)
- LangChain: document loading → splitting → embedding → retrieval

## アーキテクチャ

```
Frontend (React) ─SSE→ Backend (FastAPI) ─→ LangChain RAG ─→ Ollama (LLM)
                                          │
                                          └→ ChromaDB (Vector Store)
                                          └→ PostgreSQL (Metadata)
```

## サポート形式

- PDF (.pdf)
- Word (.docx)
- PowerPoint (.pptx)
- Excel (.xlsx)
- Text (.txt, .md)
