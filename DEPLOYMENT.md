# デプロイ手順

このアプリケーションをWeb上で公開する方法を説明します。

## 推奨サービス

### 1. Render（推奨・無料プランあり）

**メリット:**
- 無料プランあり
- GitHubと連携して自動デプロイ
- 簡単にセットアップ可能

**手順:**

1. [Render](https://render.com) にアカウント作成・ログイン
2. 「New +」→「Web Service」を選択
3. GitHubリポジトリを接続: `s-okada-creator/national-exam-tool`
4. 設定:
   - **Name**: `national-exam-tool`（任意）
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
5. 「Create Web Service」をクリック

**注意**: 無料プランは15分間の非アクセスでスリープします（初回アクセス時に起動）

---

### 2. Railway（無料プランあり）

**メリット:**
- 無料プランあり（月$5分のクレジット）
- GitHubと連携
- 簡単なセットアップ

**手順:**

1. [Railway](https://railway.app) にアカウント作成・ログイン
2. 「New Project」→「Deploy from GitHub repo」を選択
3. リポジトリ `s-okada-creator/national-exam-tool` を選択
4. Railwayが自動的にFlaskアプリを検出してデプロイ

---

### 3. PythonAnywhere（無料プランあり）

**メリット:**
- 無料プランあり
- Pythonアプリに特化
- 簡単なセットアップ

**手順:**

1. [PythonAnywhere](https://www.pythonanywhere.com) にアカウント作成
2. 「Files」タブでGitHubからリポジトリをクローン
3. 「Web」タブで新しいWebアプリを作成
4. WSGI設定ファイルを編集してFlaskアプリを設定

---

### 4. Fly.io（無料プランあり）

**メリット:**
- 無料プランあり
- グローバルにデプロイ可能

**手順:**

1. [Fly.io](https://fly.io) にアカウント作成
2. `flyctl` CLIをインストール
3. `fly launch` コマンドでデプロイ

---

## デプロイ前の確認事項

1. ✅ `Procfile` が作成済み
2. ✅ `runtime.txt` が作成済み
3. ✅ `requirements.txt` が最新
4. ✅ `data/questions.json` がコミット済み
5. ✅ `.gitignore` で不要なファイルが除外済み

## デプロイ後の確認

- アプリケーションが正常に起動しているか
- 問題データが正しく読み込まれているか
- すべての機能が動作しているか

## カスタムドメインの設定（オプション）

各サービスでカスタムドメインを設定できます。詳細は各サービスのドキュメントを参照してください。

