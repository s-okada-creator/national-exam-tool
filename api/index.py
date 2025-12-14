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

# VercelのPythonランタイムはWSGIアプリケーションを直接サポート
# appを直接エクスポートすることで、Vercelが自動的に検出する

