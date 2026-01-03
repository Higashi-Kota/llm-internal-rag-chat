# Ollama インストール〜動作確認（WSL / Linux）

https://ollama.com/

この手順は、ローカルRAG（LangChain v1 × Ollama）向けに **Ollama をWSL上へ導入**し、
**自動起動の設定**と **動作確認** までを一通り行います。

> ここでのインストール先は `/usr/local/bin/ollama` を前提にしています。

---

## 1. 前提確認（WSL / systemd）
WSL上で systemd が利用可能なことを前提とします。
すでに `systemctl status docker` が動作するならOKです。

---

## 2. Ollama をインストール
```bash
curl -fsSL https://ollama.com/download/linux | sh
```

インストール確認：
```bash
which ollama
ollama -v
```
例: 
- `which ollama` → `/usr/local/bin/ollama`
- `ollama -v` → `ollama version is 0.13.5` など

---

## 3. Ollama 専用ユーザー/グループの作成
```bash
sudo useradd -r -s /bin/false -U -m -d /usr/share/ollama ollama
sudo usermod -a -G ollama "$USER"
```
※ 既に存在する場合は `useradd: user 'ollama' already exists` と出ますが問題ありません。

反映確認：
```bash
getent passwd ollama
getent group ollama
id "$USER"
```
`groups` に `ollama` が入っていればOKです。

---

## 4. systemd サービスの作成（自動起動）
`/etc/systemd/system/ollama.service` を作成します。
```bash
sudo tee /etc/systemd/system/ollama.service >/dev/null <<'EOF'
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF
```

反映：
```bash
sudo systemctl daemon-reload
```

---

## 5. 有効化（自動起動 + 起動）
```bash
sudo systemctl enable ollama
sudo systemctl start ollama
sudo systemctl status ollama
```
`Active: active (running)` なら成功です。

---

## 6. 無効化（停止 + 自動起動解除）
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo systemctl status ollama
```
`inactive (dead)` になっていればOKです。

---

## 7. 動作確認（最小）
**モデル一覧確認**
```bash
ollama list
```

**モデル実行（軽量）**
```bash
ollama run qwen2.5:1.5b "hello"
```

**RAGで使う想定モデル（例）**
```bash
ollama run gemma3:4b "こんにちは。自己紹介して。"
```

初回はモデルを自動ダウンロードします。2回目以降は即応答になります。

---

## 8. 参考：RAGで使う埋め込みモデルの取得
```bash
ollama pull nomic-embed-text
```

---

## 9. よくあるつまずき
- **`systemctl` が使えない**: WSLでsystemdが有効か確認してください
- **`ollama` が見つからない**: `which ollama` が `/usr/local/bin/ollama` か確認
- **モデルが遅い/重い**: より軽量なモデル（例: `qwen2.5:1.5b`）で確認

---
