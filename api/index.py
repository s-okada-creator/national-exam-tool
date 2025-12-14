"""
Vercel用のエントリーポイント
FlaskアプリをVercelのサーバーレス関数としてラップ
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app import app
except Exception as e:
    # エラーをログに出力（Vercelのログで確認可能）
    import traceback
    print(f"Error importing app: {e}")
    print(traceback.format_exc())
    raise

# Vercelのサーバーレス関数用のハンドラー
def handler(request):
    """Vercelのサーバーレス関数ハンドラー"""
    # VercelのrequestオブジェクトからWSGI環境を構築
    environ = request.environ
    start_response = request.start_response
    
    # Flaskアプリを呼び出し
    return app(environ, start_response)

