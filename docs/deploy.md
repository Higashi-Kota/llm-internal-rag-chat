# デプロイ

## 環境変数

### バックエンド

#### 必須

| 変数 | 説明 |
|------|------|
| `DATABASE_URL` | PostgreSQL接続URL（例: `postgresql://user:pass@host:5432/db`） |

#### アプリケーション設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `PORT` | `10000` | サーバーポート（Renderは自動設定） |
| `DEBUG` | `false` | デバッグモード |
| `USE_MOCK` | `false` | モックモード（LLM呼び出しをスキップ） |
| `CORS_ORIGINS` | - | 追加のCORS許可オリジン（カンマ区切り） |

#### RAG設定

| 変数 | デフォルト | 説明 |
|------|-----------|------|
| `LLM_PROVIDER` | `ollama` | LLMプロバイダー (`ollama`/`openai`/`anthropic`/`gemini`) |
| `LLM_MODEL` | `gemma3:4b` | 使用するLLMモデル |
| `EMBEDDING_PROVIDER` | `ollama` | 埋め込みプロバイダー (`ollama`/`openai`) |
| `EMBEDDING_MODEL` | `nomic-embed-text` | 埋め込みモデル |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `CHROMA_DIR` | `backend/data/chroma` | ChromaDB永続化ディレクトリ |
| `DOCS_DIR` | `backend/data/docs` | ドキュメントディレクトリ |
| `CHUNK_SIZE` | `1000` | ドキュメントチャンクサイズ |
| `CHUNK_OVERLAP` | `200` | チャンクオーバーラップ |
| `RETRIEVAL_K` | `4` | 検索結果数 |
| `MAX_TOKENS` | `2048` | LLM最大トークン数 |
| `TEMPERATURE` | `0.7` | LLM温度パラメータ |

#### APIキー（クラウドプロバイダー使用時）

| 変数 | 説明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI APIキー（`LLM_PROVIDER=openai`または`EMBEDDING_PROVIDER=openai`時に必要） |
| `ANTHROPIC_API_KEY` | Anthropic APIキー（`LLM_PROVIDER=anthropic`時に必要） |
| `GEMINI_API_KEY` | Google Gemini APIキー（`LLM_PROVIDER=gemini`時に必要） |

### フロントエンド

ビルド時に埋め込まれる環境変数（`ARG`として渡す）:

| 変数 | 説明 |
|------|------|
| `VITE_API_URL` | バックエンドAPIのURL（例: `https://api.example.com`） |

## GitHub Actions

### ワークフロー

- **ci.yml**: PR/pushでlint, typecheck, test実行
- **deploy.yml**: mainへのpushでDockerイメージビルド、マイグレーション
- **e2e.yml**: PRでPlaywright E2Eテスト実行

### Secrets (Settings > Secrets and variables > Actions)

| Secret | 説明 |
|--------|------|
| `DATABASE_URL` | PostgreSQL接続URL（マイグレーション用） |
| `RENDER_BACKEND_DEPLOY_HOOK` | デプロイフック（オプション） |
| `RENDER_FRONTEND_DEPLOY_HOOK` | デプロイフック（オプション） |

### Variables

| Variable | 説明 |
|----------|------|
| `VITE_API_URL` | バックエンドURL |
