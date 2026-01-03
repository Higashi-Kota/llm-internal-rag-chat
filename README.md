# llm-internal-rag-chat

ローカルRAGシステム - LangChain × Ollama × ChromaDB

## ローカル開発

### 前提条件

[ホストマシンでOllamaを起動しておく必要があります](./docs/install.md)

```bash
# Ollama起動
ollama serve

# 必要なモデルを取得
ollama pull gemma3:4b
ollama pull nomic-embed-text
```

### ドキュメント配置

RAG用のドキュメントを `backend/data/docs/` に配置してください。

対応形式: PDF, DOCX, PPTX, XLSX, TXT

### セットアップ

```bash
# バックエンド依存関係インストール
cd backend && uv sync --extra dev

# 環境変数ファイルをコピー
cp .env.example .env
cd ..

# フロントエンド依存関係インストール
pnpm install
```

### データベース（Docker Compose）

```bash
# PostgreSQL起動（初回起動時に自動マイグレーション）
docker compose up -d

# 停止
docker compose down

# 洗い替え（データ削除してクリーンな状態から再作成）
docker compose down -v && docker compose up -d
```

| サービス | ポート | 説明 |
|---------|-------|------|
| postgres | 5434 | PostgreSQL |

接続URL: `postgresql://rag_chat:dev_password@localhost:5434/rag_chat`

### 起動

```bash
# バックエンド起動
cd backend
uv run fastapi dev src/mermaid_llm/main.py --port 8000

# フロントエンド起動（別ターミナル）
pnpm dev:frontend
```

### ドキュメントインデックス作成

```bash
cd backend
uv run python scripts/create_index.py

# ステータス確認
uv run python scripts/create_index.py --status

# インデックスクリア
uv run python scripts/create_index.py --clear
```