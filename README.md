# logwatch-with-ai

システムログを自動監視し、**DeepSeek AI** で解析して、毎日メールで管理者に通知するスクリプト。DeepSeek API 障害時は生ログを直接送信、メール送信失敗時はファイルに保存するフォールバック機構付き。

## Features

- ✅ **logwatch** で Linux ログを自動収集
- ✅ **DeepSeek API** でスマート解析・要約
- ✅ **HTML メール** で見やすい形式で管理者に通知
- ✅ **DeepSeek 障害時** → 生ログをそのまま送信
- ✅ **メール送信失敗時** → `/var/tmp` に自動保存
- ✅ **Cron 統合** で毎日自動実行（推奨：午前2時）

## 要件

- **OS**: Linux (RHEL/CentOS, Debian/Ubuntu)
- **Python**: 3.7 以上
- **Tools**: `logwatch`, `postfix` (メール送信)
- **API**: DeepSeek API キー
- **Network**: インターネット接続 (DeepSeek API 呼び出し用)

## インストール

### 1. 前提条件をインストール

```bash
# RHEL/CentOS
sudo yum install -y logwatch postfix python3

# Debian/Ubuntu
sudo apt-get install -y logwatch postfix python3 python3-venv
```

### 2. プロジェクトをクローン

```bash
cd /opt
sudo git clone https://github.com/your-org/logwatch-with-ai.git
cd logwatch-with-ai
```

### 2.5 自動セットアップ（`deploy.sh` を使う）

手動セットアップの代わりに、同梱のデプロイスクリプトを利用できます。

```bash
cd /opt/logwatch-with-ai
sudo bash deploy.sh
```

このスクリプトは以下を自動実施します。
- `.venv` 作成と依存パッケージインストール
- `config/logwatch-ai.cron` の配置
- `config/logwatch-ai.logrotate` の配置
- 実行権限とログファイルの初期設定

> すでに `deploy.sh` を使った場合は、以降の「3〜5」は確認だけでOKです。

### 3. Python 仮想環境を作成して依存パッケージをインストール

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. 環境変数を設定

```bash
# テンプレートをコピー
sudo cp .env.example .env

# 編集
sudo nano .env
```

**必須項目:**
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx  # DeepSeek API キーを記入
ADMIN_EMAIL=nishimura@69.nyanta.jp
MAIL_FROM=logwatch-ai@your-domain.com
```

**推奨（大きなログ対策）:**
```bash
# DeepSeek に送るログ文字数上限（コンテキスト超過回避）
DEEPSEEK_MAX_INPUT_CHARS=50000
```

### 5. スクリプトの権限を設定

```bash
sudo chmod 755 /opt/logwatch-with-ai/src/main.py
sudo chmod 755 /opt/logwatch-with-ai/src/*.py
```

## 使用方法

### 手動実行（テスト）

```bash
# 実行（.env は自動読み込み）
cd /opt/logwatch-with-ai
.venv/bin/python src/main.py
```

**ログ出力:**
```
/var/log/logwatch-ai.log
```

### Cron で自動実行

#### 6. Cron ジョブを登録

```bash
# Cron ファイルを確認
sudo cat config/logwatch-ai.cron

# /etc/cron.d/ にコピー
sudo cp config/logwatch-ai.cron /etc/cron.d/logwatch-ai

# Cron サービスを再起動
sudo systemctl restart cron
```

> `config/logwatch-ai.cron` には機密情報（APIキー等）を記載しません。実行時の設定値は `/opt/logwatch-with-ai/.env` から自動読み込みされます。

#### 7. ログローテーションを設定

```bash
sudo cp config/logwatch-ai.logrotate /etc/logrotate.d/logwatch-ai
```

#### 8. Cron 実行を確認

```bash
# Cron ジョブが登録されているか確認
sudo grep logwatch /etc/cron.d/logwatch-ai

# Cron ログで実行確認
sudo tail -f /var/log/cron
```

## トラブルシューティング

### logwatch コマンドが見つからない

```bash
# logwatch をインストール
sudo yum install logwatch
# または
sudo apt-get install logwatch
```

### DeepSeek API が失敗する

**症状**: `[WARNING] DeepSeek API failed` がログに出力されている

```bash
# APIキーを確認
grep DEEPSEEK_API_KEY /opt/logwatch-with-ai/.env

# APIキーが正しいか確認（テスト呼び出し）
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

**対応**: この場合、生ログが自動的にメール送信されます（フォールバック）

### メール送信が失敗する

**症状**: `[ERROR] Email send failed` がログに出力されている

```bash
# postfix が起動しているか確認
sudo systemctl status postfix

# postfix を起動（されていない場合）
sudo systemctl start postfix
sudo systemctl enable postfix

# SMTP 接続テスト
telnet localhost 25
```

**対応**: この場合、レポートが `/var/tmp/logwatch-report-*.html` に自動保存されます

### ログファイルが見つからない

```bash
# logwatch の実行確認（本スクリプトと同じ実行オプション）
logwatch --format text

# logwatch 設定を確認
cat /etc/logwatch/default.conf
ls /etc/logwatch/conf/logfiles/
```

**補足**: journald 対応・監視対象サービスは logwatch 側設定で管理します。

## 設定のカスタマイズ

### 監視対象サービスを変更

`logwatch` 側設定を編集します（例: `/etc/logwatch/conf/logfiles/`, `/etc/logwatch/conf/services/`）。

例:
```bash
sudo ls /etc/logwatch/conf/logfiles/
sudo ls /etc/logwatch/conf/services/
```

### 実行スケジュールを変更

`/etc/cron.d/logwatch-ai` を編集:
```bash
# 毎日午前8時に実行
0 8 * * * root cd /opt/logwatch-with-ai && /opt/logwatch-with-ai/.venv/bin/python src/main.py >> /var/log/logwatch-ai-cron.log 2>&1
```

## メール送信設定

### Gmail を使用する場合

1. Gmail アカウントで 2 段階認証を有効化
2. アプリパスワードを生成
3. `.env` で SMTP 設定:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
MAIL_FROM=your-email@gmail.com
# パスワードは環境変数で設定
```

### 企業メールサーバーを使用する場合

```bash
SMTP_HOST=mail.your-company.com
SMTP_PORT=587
MAIL_FROM=logwatch-ai@your-company.com
```

## ファイル構成

```
logwatch-with-ai/
├── src/
│   ├── main.py                  # メインスクリプト
│   ├── config.py                # 設定管理
│   ├── logwatch_executor.py     # logwatch 実行
│   ├── deepseek_analyzer.py     # DeepSeek API 統合
│   └── email_sender.py          # メール送信
├── config/
│   ├── logwatch.conf            # logwatch 設定
│   ├── logwatch-ai.cron         # Cron ジョブ定義
│   └── logwatch-ai.logrotate    # ログローテーション
├── tests/
│   ├── test_config.py
│   ├── test_logwatch_executor.py
│   ├── test_deepseek_analyzer.py
│   └── test_email_sender.py
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git 除外設定
├── requirements.txt             # Python 依存
├── deploy.sh                    # 自動デプロイスクリプト
└── README.md                    # このファイル
```

## 実行フロー

```
1. logwatch 実行 → ログ収集
        ↓
2. DeepSeek API 呼び出し
    ├─ ✓ 成功 → JSON 解析結果
    │          → HTML メール本体に変換
    │
    └─ ✗ 失敗 → 生ログをそのまま使用
                → "DeepSeek 利用不可" 注釈付き
        ↓
3. メール送信
    ├─ ✓ 成功 → 完了
    │
    └─ ✗ 失敗 → /var/tmp に HTML ファイル保存
                → 管理者に手動確認を促す
```

## デバッグ

### ログレベルを上げる

```bash
LOG_LEVEL=DEBUG .venv/bin/python src/main.py
```

### 個別モジュールをテスト

```bash
# logwatch 実行テスト
python3 -c "from src.logwatch_executor import LogwatchExecutor; e = LogwatchExecutor(); print(e.execute())"

# DeepSeek 接続テスト
python3 -c "from src.deepseek_analyzer import DeepSeekAnalyzer; a = DeepSeekAnalyzer('your-key'); print(a.analyze('test log'))"

# メール送信テスト
python3 -c "from src.email_sender import EmailSender; e = EmailSender(); print(e.send_email('Test', '<p>Test</p>', 'admin@example.com'))"
```

## セキュリティに関する注意

- ✅ `.env` ファイルは Git に含めないこと（`.gitignore` で除外）
- ✅ API キーとパスワードは環境変数で管理
- ✅ ログファイルの権限を適切に設定 (`chmod 640`)
- ✅ Cron 実行ユーザーを制限（推奨: `root` または専用ユーザー）

## サポート

問題が発生した場合:
1. `/var/log/logwatch-ai.log` を確認
2. `DEBUG` モードで実行して詳細ログを取得
3. DeepSeek API ドキュメントを確認

## ライセンス

MIT License

## 更新履歴

- **v1.0.0** (2026-03-27): Initial release