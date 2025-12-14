# デプロイ手順（Render）

このアプリケーションをRenderにデプロイする手順です。

## 前提条件

- GitHubアカウント
- Renderアカウント（無料プランで利用可能）
- リポジトリがGitHubにプッシュ済みであること

## デプロイ手順

### 1. Renderにアクセス

1. ブラウザで https://dashboard.render.com にアクセス
2. 「Get Started for Free」をクリックしてアカウント作成
   - GitHubアカウントでログインすることを推奨

### 2. 新しいWebサービスを作成

1. ダッシュボードで「New +」ボタンをクリック
2. 「Web Service」を選択

### 3. GitHubリポジトリを接続

1. 「Connect account」でGitHubアカウントを接続（初回のみ）
2. リポジトリ一覧から `s-okada-creator/national-exam-tool` を選択

### 4. 設定を入力

以下の設定を入力します：

- **Name**: `national-exam-tool`
- **Region**: お好みのリージョン（例: Singapore, Tokyo）
- **Branch**: `main`
- **Root Directory**: （空白のまま）
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`

### 5. 環境変数

環境変数は特に設定する必要はありません。Renderが自動的に `PORT` 環境変数を設定します。

### 6. デプロイ開始

「Create Web Service」をクリックしてデプロイを開始します。

デプロイには数分かかります。ログを確認して、エラーがないか確認してください。

### 7. デプロイ完了後

デプロイが完了すると、Renderが提供するURL（例: `https://national-exam-tool.onrender.com`）でアプリケーションにアクセスできます。

## 注意事項

- **無料プラン**: Renderの無料プランでは、15分間アクセスがないとスリープします。最初のアクセス時に起動に時間がかかることがあります。
- **データファイル**: `data/questions.json` はリポジトリに含まれているため、デプロイ時に自動的に含まれます。
- **セッションデータ**: セッションデータはメモリ上に保存されるため、アプリが再起動されると消去されます。

## トラブルシューティング

### デプロイが失敗する場合

1. **ログを確認**: Renderのダッシュボードで「Logs」タブを確認
2. **依存パッケージ**: `requirements.txt` に必要なパッケージがすべて含まれているか確認
3. **ポート設定**: `app.py` で `PORT` 環境変数を使用しているか確認

### アプリが起動しない場合

1. **ログを確認**: エラーメッセージを確認
2. **データファイル**: `data/questions.json` が存在するか確認
3. **Pythonバージョン**: `runtime.txt` で指定されたPythonバージョンが正しいか確認

## 自動デプロイ

`render.yaml` ファイルがリポジトリに含まれているため、Renderが自動的に設定を読み込む場合があります。手動で設定を入力する必要がない場合もあります。
