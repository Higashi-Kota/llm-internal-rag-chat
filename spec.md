# ローカルRAG (LangChain v1 × Ollama) 仕様書

## 1. 目的
- WSL上のローカル環境のみで完結するRAGを構築し、機密文書を外部へ送信せずに検索・要約・QAを実現する
- LangChain v1 + Ollama + ChromaDB を用いた最小構成を、既存の構成`~/higashi-wrksp/llm-mermaid-chat`に合わせて実装する

## 2. スコープ
### 対象
- ドキュメント取込・分割・埋め込み・検索・回答生成
- FastAPI APIエンドポイント + 既存フロントエンドからのチャット
- ローカルベクターストアの永続化
- クラウドLLM/EmbeddingのPoC利用（無料枠〜少額課金でのハンズオン）

### 非対象
- マルチユーザー権限管理
- 本番運用向け監視・スケーリング

## 3. 前提環境
- Windows 11 + WSL2 (Ubuntu)
- Python 3.10+
- LangChain v1.x
- Ollama (Linux版, WSL内で起動)
- ChromaDB (ローカル永続)

### モデル方針
- 生成: `gemma3:4b` (既定)
- 埋め込み: `nomic-embed-text` (既定)
- いずれも Ollama から取得

## 4. フィジビリティ (WSL + Ollama)
- WSL2上で Ollama Linux版をインストールし、`ollama serve` をWSL内で常駐させる構成は実現可能
- FastAPI・LangChainはWSL内で動作し、Ollama API (localhost:11434) に接続する
- Windows側ブラウザからは既存フロントエンド (Vite) に接続し、バックエンドはWSLで提供
- 重要要件: WSL側でのメモリ確保 (8GB以上推奨)、モデルサイズに応じた調整

## 5. 全体アーキテクチャ
```
Frontend (React) ─SSE→ Backend (FastAPI) ─→ LangChain v1 ─→ Ollama LLM
                                               └→ Ollama Embeddings ─→ ChromaDB
```
※ クラウド利用時は LLM/Embedding の接続先を差し替え

## 6. ディレクトリ構成 (追加案)
```
backend/
  src/mermaid_llm/
    rag/
      config.py            # モデル/パス/パラメータ
      loaders.py           # 文書ローダー定義
      splitter.py          # 分割設定
      indexer.py           # ベクトル化・永続化
      retriever.py         # 検索
      chain.py             # RAGチェーン
      prompts.py           # システム/ユーザプロンプト
      llm.py               # LLMファクトリ
      embeddings.py        # Embeddingsファクトリ
      providers/           # プロバイダー実装
        __init__.py        # レジストリ・共通定義
        ollama.py          # Ollama (ローカルデフォルト)
        openai.py          # OpenAI
        anthropic.py       # Anthropic
        gemini.py          # Google Gemini
  data/
    docs/                  # 取込対象ファイル
    chroma/                # 永続化ベクターストア
  scripts/
    create_index.py        # CLI: 取込/再インデックス

specs/
  rag.tsp                  # RAG API定義 (TypeSpec)
```

## 7. 開発・デプロイ計画（既存構成に準拠）
### 開発（docker-compose）
- `~/higashi-wrksp/llm-mermaid-chat/docker-compose.yml` を踏襲
- 役割分担: frontend / backend / (chroma 永続ボリューム)
- Ollama は **WSLホスト** で起動し、backend から `OLLAMA_BASE_URL` で接続
- 追加の秘密情報は `.env` で管理

### 本番デプロイ（Dockerfile.frontend / Dockerfile.backend）
- 既存の Dockerfile を流用し、`ENV` で LLM/Embedding 接続先を切り替え可能にする
- RAGデータ（Chroma永続化）は volume マウント運用

## 8. 主要コンポーネント設計
### 8.1 文書ローダー
- 対応拡張子: `.pdf .docx .pptx .xlsx .txt`
- `DirectoryLoader` + 拡張子別Loader

### 8.2 分割 (Chunking)
- `RecursiveCharacterTextSplitter`
- `chunk_size=1000`, `chunk_overlap=200`
- 日本語セパレータ: `\n\n`, `\n`, `。`, ` `, ``

### 8.3 埋め込み/ベクターストア
- `OllamaEmbeddings(model=EMBEDDING_MODEL)`
- `Chroma(persist_directory=CHROMA_DIR)`
- 取込時に埋め込みと保存を同時実行

### 8.4 RAGチェーン
- 検索: `vector_store.similarity_search(query)`
- プロンプト: 検索結果を system message に注入
- LLM: `ChatOllama(model=LLM_MODEL)`

## 9. API設計 (概要)
### `POST /rag/chat`
- 入力: `messages: [{ role, content }]`
- 出力: SSEでトークンストリーム
- 既存のチャット基盤を流用し、RAGチェーンに接続

### `POST /rag/index`
- 入力: `path` (省略時は `backend/data/docs`)
- 出力: 取り込み件数/エラー一覧
- CLIスクリプトからも利用可能

## 10. UI方針
- 既存フロントエンドのチャット画面を流用
- モード切替: `Mermaid生成` / `RAG` のタブまたはトグル
- RAGモードでは「参照文書ソースの表示」をオプションで表示

## 11. 設定値 (env)
```
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma3:4b
EMBEDDING_MODEL=nomic-embed-text
CHROMA_DIR=backend/data/chroma
DOCS_DIR=backend/data/docs
LLM_PROVIDER=ollama        # ollama | openai | anthropic | gemini
EMBEDDING_PROVIDER=ollama  # ollama | openai
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
COST_BUDGET_USD=5          # 目安: 少額課金で試す上限
```

## 12. クラウドLLM/Embedding（無料枠〜$5ハンズオン）
Qiita記事で整理されている「価格・リージョン・コンテキスト長・日本語対応」などの観点を使って、PoC段階で低コストに試せる構成を用意する。

### 推奨候補（低コスト）
- **OpenAI**: `gpt-4o-mini`（生成） + `text-embedding-3-small`（埋め込み）  
  低価格でRAG検証に向く。価格は公式ページを参照。
- **Anthropic**: `Claude Haiku` 系  
  低価格の小型モデル。価格は公式ページを参照。
- **Google Gemini API**: Free Tier あり  
  Gemini APIは無料枠があり、無料トークンで試せる。

### ハンズオンの進め方（無料枠〜$5）
1. **まずは無料枠で試す**: Gemini APIのFree Tierで生成を確認し、埋め込みはローカル（Ollama）で作成する
2. **少額課金で試す**: OpenAI/Anthropicを使う場合は小型モデルを選び、`max_tokens` と `top_k` を小さくする
3. **埋め込みコスト最小化**: 取り込み文書はサンプル数から開始し、再インデックス回数を抑える

### 運用ポリシー（低コスト維持）
- 低価格モデルのデフォルト設定（上記）から開始
- `max_tokens` / `top_k` / `top_p` を抑えて出力を制限
- **請求上限・アラート** を各プロバイダのコンソールで設定
- 料金は変動するため、必ず公式価格表で最新を確認

## 13. テスト方針
- 単体: 文書ローダー・分割・インデックス化
- 結合: `/rag/index` → `/rag/chat` の一連動作
- 回帰: 既存機能の非影響

## 14. 実装マイルストーン
1. WSL上で Ollama 起動確認 + モデル取得
2. `indexer.py` と `scripts/create_index.py` 実装
3. `/rag/chat` API 実装 + SSE対応
4. フロントエンドのRAGモード追加
5. 動作確認とドキュメント更新
