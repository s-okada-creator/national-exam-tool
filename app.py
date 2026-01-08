"""
国家試験対策ツール - Flaskアプリケーション
"""
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
import uuid
import os
from datetime import datetime
from utils.question_manager import QuestionManager
from utils.report_generator import ReportGenerator

# Vercel KV (Upstash Redis) のインポート
try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# 環境変数VERCELを確認して、Vercel環境かどうかを判定
IS_VERCEL = os.environ.get('VERCEL') == '1'

# Flaskアプリの初期化
# Vercel環境では、プロジェクトルートからの相対パスを使用
if IS_VERCEL:
    # Vercel環境: プロジェクトルートを基準にパスを設定
    app = Flask(
        __name__,
        static_folder=str(Path(__file__).parent / 'static'),
        static_url_path='/static',
        template_folder=str(Path(__file__).parent / 'templates')
    )
else:
    # ローカル環境: 通常の相対パス
    app = Flask(__name__, static_folder='static', static_url_path='/static')

app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # 本番環境では環境変数から取得

# 静的ファイルのバージョン管理（キャッシュバスティング用）
# JavaScriptとCSSファイルの最終更新時刻を使用してバージョンを生成
def get_static_file_version(filename):
    """静的ファイルのバージョンを取得（最終更新時刻のタイムスタンプ）"""
    try:
        static_path = Path(__file__).parent / 'static' / filename
        if static_path.exists():
            return str(int(static_path.stat().st_mtime))
    except Exception:
        pass
    # ファイルが見つからない場合は現在時刻を使用
    return str(int(datetime.now().timestamp()))

# アプリケーション起動時に静的ファイルのバージョンを設定
app.config['JS_VERSION'] = get_static_file_version('js/app.js')
app.config['CSS_VERSION'] = get_static_file_version('css/style.css')

# テンプレートで使用できるように関数を登録
@app.context_processor
def inject_version():
    """テンプレートにバージョン情報を注入"""
    return {
        'js_version': app.config.get('JS_VERSION', '1.0.0'),
        'css_version': app.config.get('CSS_VERSION', '1.0.0')
    }

# データディレクトリ
# Vercelのサーバーレス環境では、プロジェクトルートからの相対パスを使用

if IS_VERCEL:
    # Vercel環境: プロジェクトルートからの相対パス
    DATA_DIR = Path(__file__).parent / 'data'
    QUESTIONS_FILE = DATA_DIR / 'questions.json'
    # セッションデータは/tmpに保存（Vercelでは書き込み可能なのは/tmpのみ）
    SESSIONS_DIR = Path('/tmp') / 'sessions'
else:
    # ローカル環境: 通常のパス
    DATA_DIR = Path(__file__).parent / 'data'
    QUESTIONS_FILE = DATA_DIR / 'questions.json'
    SESSIONS_DIR = DATA_DIR / 'sessions'

# 問題マネージャーの初期化（エラーハンドリング付き）
try:
    # パスの存在確認
    if not QUESTIONS_FILE.exists():
        print(f"WARNING: Questions file not found at: {QUESTIONS_FILE}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"File parent exists: {QUESTIONS_FILE.parent.exists()}")
        # 代替パスを試す
        alt_path = Path(__file__).parent / 'data' / 'questions.json'
        if alt_path.exists():
            print(f"Using alternative path: {alt_path}")
            QUESTIONS_FILE = alt_path
    
    question_manager = QuestionManager(QUESTIONS_FILE)
    report_generator = ReportGenerator()
    print(f"Successfully initialized question manager with {len(question_manager.get_all_questions())} questions")
except Exception as e:
    import traceback
    print(f"Error initializing question manager: {e}")
    print(f"QUESTIONS_FILE path: {QUESTIONS_FILE}")
    print(f"QUESTIONS_FILE exists: {QUESTIONS_FILE.exists()}")
    print(f"Traceback: {traceback.format_exc()}")
    # エラーが発生してもアプリは起動できるようにする（後でエラーページを表示）
    question_manager = None
    report_generator = None

# セッションデータ（メモリ上、本番環境ではDBを使用）
sessions = {}

# Redis クライアントの初期化（Vercel KV用）
redis = None
if REDIS_AVAILABLE and os.environ.get('KV_REST_API_URL'):
    try:
        redis = Redis(
            url=os.environ.get('KV_REST_API_URL'),
            token=os.environ.get('KV_REST_API_TOKEN')
        )
        print("Vercel KV (Redis) initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Redis: {e}")
        redis = None
else:
    print("Using in-memory session storage (Redis not available)")

# セッション操作関数
def save_session(session_id, data):
    """セッションデータを保存（Redisまたはメモリ）"""
    if redis:
        try:
            # TTL: 24時間（86400秒）
            redis.setex(f"session:{session_id}", 86400, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"Error saving session to Redis: {e}")
            raise  # 例外を再発生させる
    else:
        # Vercel環境ではメモリ保存は機能しない（サーバーレス関数のため）
        if IS_VERCEL:
            raise RuntimeError("Redis is not configured in Vercel environment. Please set KV_REST_API_URL and KV_REST_API_TOKEN environment variables.")
        # ローカル開発用フォールバック
        sessions[session_id] = data

def get_session_data(session_id):
    """セッションデータを取得（Redisまたはメモリ）"""
    if redis:
        try:
            data = redis.get(f"session:{session_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting session from Redis: {e}")
            # フォールバック: メモリから取得
            return sessions.get(session_id)
    else:
        return sessions.get(session_id)

def update_session(session_id, data):
    """セッションデータを更新（Redisまたはメモリ）"""
    if redis:
        try:
            # 既存のセッションを取得して更新
            existing_data = get_session_data(session_id)
            if existing_data:
                existing_data.update(data)
                save_session(session_id, existing_data)
            else:
                save_session(session_id, data)
        except Exception as e:
            print(f"Error updating session in Redis: {e}")
            # フォールバック: メモリを更新
            if session_id in sessions:
                sessions[session_id].update(data)
            else:
                sessions[session_id] = data
    else:
        # ローカル開発用フォールバック
        if session_id in sessions:
            sessions[session_id].update(data)
        else:
            sessions[session_id] = data

# グローバルエラーハンドラー
@app.errorhandler(Exception)
def handle_exception(e):
    """すべての例外をキャッチしてエラーレスポンスを返す"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"Unhandled exception: {e}")
    print(error_trace)
    
    # エラーページを返す
    try:
        return render_template('error.html', error=str(e)), 500
    except Exception as template_error:
        # テンプレートレンダリングに失敗した場合はプレーンテキストを返す
        return f"Error: {str(e)}\n\nTemplate rendering failed: {str(template_error)}", 500

@app.errorhandler(404)
def handle_404(e):
    """404エラーを処理"""
    return render_template('error.html', error="ページが見つかりません"), 404

@app.errorhandler(500)
def handle_500(e):
    """500エラーを処理"""
    return render_template('error.html', error="サーバーエラーが発生しました"), 500


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/practice')
def practice():
    """学習モードページ"""
    return render_template('practice.html', mode='practice')


@app.route('/test')
def test():
    """テストモードページ"""
    return render_template('test.html', mode='test')


@app.route('/report/<session_id>')
def report(session_id):
    """レポート表示ページ"""
    return render_template('report.html', session_id=session_id)


# API エンドポイント

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """全ジャンル一覧と問題数を取得"""
    if question_manager is None:
        return jsonify({'error': 'Question data not loaded'}), 500
    categories = question_manager.get_categories()
    return jsonify({
        'categories': categories,
        'total': sum(categories.values())
    })


@app.route('/api/exam-numbers', methods=['GET'])
def get_exam_numbers():
    """全試験回数のリストを取得"""
    if question_manager is None:
        return jsonify({'error': 'Question data not loaded'}), 500
    exam_numbers = question_manager.get_exam_numbers()
    return jsonify({'exam_numbers': exam_numbers})


@app.route('/api/questions', methods=['GET'])
def get_questions():
    """問題一覧を取得（フィルタリング対応）"""
    if question_manager is None:
        return jsonify({'error': 'Question data not loaded'}), 500
    exam_numbers = request.args.getlist('exam_numbers', type=int)
    categories = request.args.getlist('categories')
    
    # 空のリストはNoneに変換（全件を意味する）
    exam_numbers = exam_numbers if exam_numbers else None
    categories = categories if categories else None
    
    questions = question_manager.filter_questions(
        exam_numbers=exam_numbers,
        categories=categories
    )
    
    return jsonify({
        'questions': questions,
        'total': len(questions)
    })


@app.route('/api/questions/<question_id>', methods=['GET'])
def get_question(question_id):
    """特定の問題を取得"""
    if question_manager is None:
        return jsonify({'error': 'Question data not loaded'}), 500
    question = question_manager.get_question_by_id(question_id)
    if question:
        return jsonify(question)
    else:
        return jsonify({'error': 'Question not found'}), 404


@app.route('/api/sessions', methods=['POST'])
def create_session():
    """新しいセッションを作成"""
    if question_manager is None:
        return jsonify({'error': 'Question data not loaded'}), 500
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON or missing request body'}), 400
    session_id = str(uuid.uuid4())
    
    # フィルタリング条件に基づいて問題を取得
    exam_numbers = data.get('exam_numbers', [])
    categories = data.get('categories', [])
    max_questions = data.get('max_questions', None)
    
    exam_numbers = exam_numbers if exam_numbers else None
    categories = categories if categories else None
    
    # max_questionsが指定されている場合はランダムサンプリング
    if max_questions is not None and max_questions > 0:
        questions = question_manager.filter_and_sample_questions(
            exam_numbers=exam_numbers,
            categories=categories,
            max_questions=max_questions
        )
    else:
        questions = question_manager.filter_questions(
            exam_numbers=exam_numbers,
            categories=categories
        )
    
    session_data = {
        'session_id': session_id,
        'mode': data.get('mode', 'test'),
        'exam_numbers': exam_numbers or question_manager.get_exam_numbers(),
        'categories': categories or [],
        'max_questions': max_questions,
        'questions': questions,
        'answers': [],
        'created_at': datetime.now().isoformat(),
        'current_question_index': 0
    }
    
    # Redisまたはメモリに保存
    save_session(session_id, session_data)
    
    return jsonify({
        'session_id': session_id,
        'total_questions': len(questions),
        'filtered_total': len(question_manager.filter_questions(
            exam_numbers=exam_numbers,
            categories=categories
        )) if (exam_numbers or categories) else len(question_manager.get_all_questions())
    })


@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """セッション情報を取得"""
    session_data = get_session_data(session_id)
    if session_data:
        return jsonify(session_data)
    else:
        return jsonify({'error': 'Session not found'}), 404


@app.route('/api/sessions/<session_id>/answers', methods=['POST'])
def submit_answer(session_id):
    """解答を送信"""
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid JSON or missing request body'}), 400
    
    question_id = data.get('question_id')
    answer = data.get('answer')
    time_spent = data.get('time_spent', 0)
    
    answer_data = {
        'question_id': question_id,
        'answer': answer,
        'time_spent': time_spent,
        'submitted_at': datetime.now().isoformat()
    }
    
    # 既存の解答を更新するか、新しい解答を追加
    if 'answers' not in session_data:
        session_data['answers'] = []
    
    existing_index = next(
        (i for i, a in enumerate(session_data['answers']) 
         if a.get('question_id') == question_id), 
        None
    )
    
    if existing_index is not None:
        session_data['answers'][existing_index] = answer_data
    else:
        session_data['answers'].append(answer_data)
    
    # セッションデータ全体を直接保存
    try:
        save_session(session_id, session_data)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving answer: {e}")
        return jsonify({'error': 'Failed to save answer'}), 500


@app.route('/api/sessions/<session_id>/report', methods=['GET'])
def get_report(session_id):
    """レポートを生成"""
    if report_generator is None:
        return jsonify({'error': 'Report generator not initialized'}), 500
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # Markdownレポートを生成
    markdown_report = report_generator.generate_markdown_report(session_data)
    
    # JSONレポートも生成
    json_report = report_generator.generate_json_report(session_data)
    
    # セッションデータをファイルに保存（Vercelのサーバーレス環境では/tmpを使用）
    # 注意: Vercelでは/tmpは一時的なストレージで、関数実行後に削除される可能性があります
    try:
        sessions_dir = SESSIONS_DIR
        sessions_dir.mkdir(parents=True, exist_ok=True)
        report_file = sessions_dir / f"{session_id}.json"
        
        session_data['report'] = json_report
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # ファイル保存に失敗してもレポートは返す（Vercel環境では正常な動作）
        # セッションデータはメモリ上に保持されているため、レポート生成は可能
        if not IS_VERCEL:
            print(f"Warning: Could not save session file: {e}")
    
    return jsonify({
        'markdown': markdown_report,
        'json': json_report
    })


@app.route('/api/sessions/<session_id>/report/pdf', methods=['GET'])
def get_report_pdf(session_id):
    """PDF形式のレポートを生成してダウンロード"""
    from flask import Response
    
    if report_generator is None:
        return jsonify({'error': 'Report generator not initialized'}), 500
    session_data = get_session_data(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # PDFレポートを生成
    pdf_buffer = report_generator.generate_pdf_report(session_data)
    
    # レスポンスを返す
    return Response(
        pdf_buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=report_{session_id}.pdf'
        }
    )


if __name__ == '__main__':
    # データディレクトリの確認
    if not QUESTIONS_FILE.exists():
        print(f"エラー: {QUESTIONS_FILE} が見つかりません。")
        print("先に utils/excel_loader.py を実行してデータを生成してください。")
    else:
        print(f"問題データを読み込みました: {len(question_manager.get_all_questions())}問")
        # 環境変数からポートを取得（本番環境用）
        port = int(os.environ.get('PORT', 5002))
        app.run(debug=False, host='0.0.0.0', port=port)

