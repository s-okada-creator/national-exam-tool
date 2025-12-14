#!/bin/bash
# Vercel自動デプロイスクリプト

echo "=========================================="
echo "Vercelデプロイを開始します"
echo "=========================================="

# ログイン状態を確認
if ! vercel whoami > /dev/null 2>&1; then
    echo "Vercelにログインしていません。"
    echo "ブラウザでログインしてください..."
    vercel login
fi

# ログイン確認
if vercel whoami > /dev/null 2>&1; then
    echo "ログイン済み: $(vercel whoami)"
    echo ""
    echo "デプロイを開始します..."
    vercel --yes --prod
else
    echo "ログインに失敗しました。手動でログインしてください。"
    exit 1
fi
