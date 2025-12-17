# Vercelデプロイ手順

このアプリケーションをVercelにデプロイする手順です。

## 前提条件

- GitHubアカウント
- Vercelアカウント（無料プランで利用可能）
- リポジトリがGitHubにプッシュ済みであること

## デプロイ手順

### 方法1: Vercel CLIを使用（推奨）

1. **Vercel CLIをインストール**
   ```bash
   npm install -g vercel
   ```

2. **Vercelにログイン**
   ```bash
   vercel login
   ```

3. **プロジェクトをデプロイ**
   ```bash
   vercel
   ```
   
   初回デプロイ時は以下の質問に答えます：
   - Set up and deploy? → **Y**
   - Which scope? → アカウントを選択
   - Link to existing project? → **N**
   - What's your project's name? → `national-exam-tool`（または任意の名前）
   - In which directory is your code located? → **./**（そのままEnter）
   - Want to override the settings? → **N**

4. **本番環境にデプロイ**
   ```bash
   vercel --prod
   ```

### 方法2: Vercel Webダッシュボードからデプロイ

1. **Vercelにアクセス**
   - ブラウザで https://vercel.com にアクセス
   - 「Sign Up」または「Log In」をクリック
   - GitHubアカウントでログインすることを推奨

2. **新しいプロジェクトを作成**
   - ダッシュボードで「Add New...」→「Project」をクリック
   - GitHubリポジトリ `s-okada-creator/national-exam-tool` を選択

3. **プロジェクト設定**
   - **Framework Preset**: Other
   - **Root Directory**: `./`（そのまま）
   - **Build Command**: （空白のまま）
   - **Output Directory**: （空白のまま）
   - **Install Command**: `pip install -r requirements.txt`

4. **環境変数**
   - 特に設定する必要はありません

5. **デプロイ開始**
   - 「Deploy」をクリック
   - デプロイには数分かかります

## デプロイ後の確認

デプロイが完了すると、Vercelが提供するURL（例: `https://national-exam-tool.vercel.app`）でアプリケーションにアクセスできます。

## 注意事項

- **サーバーレス関数**: Vercelはサーバーレス関数として動作するため、セッションデータはメモリ上に保存されますが、関数が再起動されると消去される可能性があります。
- **タイムアウト**: 無料プランでは関数の実行時間に制限があります（10秒）。長時間かかる処理は避けてください。
- **静的ファイル**: `static/` ディレクトリ内のファイルは自動的に配信されます。
- **データファイル**: `data/questions.json` はリポジトリに含まれているため、デプロイ時に自動的に含まれます。

## トラブルシューティング

### デプロイが失敗する場合

1. **ログを確認**: Vercelのダッシュボードで「Deployments」→「Functions」タブを確認
2. **依存パッケージ**: `requirements.txt` に必要なパッケージがすべて含まれているか確認
3. **Pythonバージョン**: `vercel.json` で指定されたPythonバージョンが正しいか確認

### アプリが起動しない場合

1. **ログを確認**: Vercelのダッシュボードでエラーログを確認
2. **データファイル**: `data/questions.json` が存在するか確認
3. **パス問題**: Vercelのサーバーレス環境ではパスの解決方法が異なる場合があります

## 自動デプロイ

GitHubリポジトリと連携している場合、`main`ブランチにプッシュするたびに自動的にデプロイされます。



