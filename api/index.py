"""
Vercel用のエントリーポイント
FlaskアプリをVercelのサーバーレス関数としてラップ
"""
import sys
from pathlib import Path
import os

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Vercel環境変数を設定（app.pyで使用される）
os.environ['VERCEL'] = '1'

# Flaskアプリをインポート
try:
    from app import app
except Exception as e:
    # エラーをログに出力（Vercelのログで確認可能）
    import traceback
    error_trace = traceback.format_exc()
    print(f"Error importing app: {e}")
    print(error_trace)
    
    # エラー時でもハンドラーを返す（エラーページを表示するため）
    from flask import Flask, Response
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def error_handler(path):
        return Response(
            f"Error initializing application: {str(e)}\n\n{error_trace}",
            status=500,
            mimetype='text/plain; charset=utf-8'
        )

# Vercelのサーバーレス関数用のハンドラー
# VercelのPython関数はWSGIアプリケーション（app変数）を直接サポート
# app変数をエクスポート（Vercelが自動的に検出）
# 注意: app変数がモジュールレベルで定義されている必要がある
# from app import appでインポートしたapp変数がここで利用可能
# Vercelはこのモジュールレベルのapp変数を自動的に検出する

