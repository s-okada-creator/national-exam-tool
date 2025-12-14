# 国家試験対策ツール

あん摩マッサージ指圧師国家試験の対策用Webアプリケーションです。

## 機能

- **学習モード**: 正解・解説・ヒントを表示しながら学習
- **テストモード**: 本番形式でテスト実施（正解・解説は非表示）
- **学科別フィルタリング**: 特定のジャンルのみを選択して学習
- **試験回数選択**: 第29回〜第33回から選択可能
- **フィードバックレポート**: Notebook.lm対応のMarkdown形式でレポート生成

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. データの準備

**初回セットアップ時:**

ExcelとPDFファイルを準備します：
- Excelファイル: 正答肢表（第29回〜第33回）を `backup/excel/` に保存
- PDFファイル: 問題集（29回前半.pdf など）を `backup/pdf/` に保存

その後、データをJSONに変換します：

```bash
# バックアップファイルを一時的にコピー
cp backup/excel/*.xlsx .
cp backup/pdf/*.pdf .

# データを生成
python3 utils/excel_loader.py

# 一時ファイルを削除（オプション）
rm *.xlsx *.pdf
```

これで `data/questions.json` が生成されます（ExcelとPDFのデータがマージされます）。

**既に `data/questions.json` がある場合:**

バックアップファイルを `backup/` ディレクトリに保存しておくことを推奨します。詳細は `backup/README.md` を参照してください。

### 3. アプリケーションの起動

```bash
python3 app.py
```

ブラウザで `http://localhost:5002` にアクセスしてください。

（注: ポートが使用中の場合は、app.pyのポート番号を変更してください）

## 使い方

1. **トップページ**: モード（学習/テスト）とフィルタ条件を選択
2. **学習/テスト画面**: 問題を選択して解答
3. **レポート画面**: テスト終了後に成績と詳細を確認

## Web上で公開する

このアプリケーションをWeb上で公開する方法は `DEPLOYMENT_VERCEL.md` を参照してください。

### クイックデプロイ（Vercel）⭐ 推奨

**方法1: Vercel CLIでデプロイ**
```bash
# ログイン（初回のみ）
vercel login

# デプロイ
vercel --yes --prod
```

**方法2: Webダッシュボードからデプロイ**
1. https://vercel.com にアクセス
2. GitHubアカウントでログイン
3. 「Add New...」→「Project」を選択
4. リポジトリ `s-okada-creator/national-exam-tool` を選択
5. 「Deploy」をクリック

詳細は `DEPLOYMENT_VERCEL.md` を参照してください。

### その他のデプロイ方法

- **Render**: `DEPLOYMENT.md` を参照
- **Railway**: 無料プランあり
- **PythonAnywhere**: 無料プランあり

## データ構造

- `data/questions.json`: 全問題データ
- `data/sessions/`: セッション履歴（JSON形式）

## バックアップについて

**重要**: 元のExcelファイルとPDFファイルは `backup/` ディレクトリにバックアップとして保存しておくことを強く推奨します。

- `backup/excel/` - Excelファイル（正答肢表）を保存
- `backup/pdf/` - PDFファイル（問題集）を保存

バックアップファイルは以下の場合に必要です：
- データの再生成が必要になった場合
- `questions.json` が破損した場合の復元
- パーサーを改善した後の再抽出
- データに不備が見つかった場合の修正

詳細は `backup/README.md` を参照してください。

## 注意事項

- セッションデータはメモリ上に保存されます。アプリを再起動すると消去されます。
- 問題文と選択肢はPDFから抽出されています。より完全な抽出には元のPDFファイルが必要です。

