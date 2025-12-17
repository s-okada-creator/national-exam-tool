# GitHubへのプッシュ手順

## 1. GitHubリポジトリの作成

1. GitHubにログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例: `national-exam-tool`）
4. 「Create repository」をクリック

## 2. リモートリポジトリの追加とプッシュ

GitHubリポジトリを作成したら、以下のコマンドを実行してください：

```bash
# リモートリポジトリを追加（YOUR_USERNAMEとREPO_NAMEを置き換えてください）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# またはSSHを使用する場合
git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git

# メインブランチを設定
git branch -M main

# プッシュ
git push -u origin main
```

## 注意事項

- `backup/` ディレクトリは `.gitignore` で除外されています（個人情報保護のため）
- `data/sessions/` 内のセッションデータも除外されています
- `data/questions.json` は含まれています（問題データ）

## 既にリポジトリが存在する場合

既にGitHubリポジトリが存在する場合は、以下のコマンドで確認できます：

```bash
git remote -v
```

リモートが設定されていない場合は、上記の手順で追加してください。



