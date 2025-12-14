"""
Vercel用のエントリーポイント
FlaskアプリをVercelのサーバーレス関数としてラップ
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app

# VercelのPythonランタイムはWSGIアプリケーションを直接サポート
# appを直接エクスポートすることで、Vercelが自動的に検出する

