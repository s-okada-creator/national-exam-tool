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

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # 本番環境では環境変数から取得

# データディレクトリ
# Vercelのサーバーレス環境では、プロジェクトルートからの相対パスを使用
DATA_DIR = Path(__file__).parent / 'data'
QUESTIONS_FILE = DATA_DIR / 'questions.json'
SESSIONS_DIR = DATA_DIR / 'sessions'

# 問題マネージャーの初期化（エラーハンドリング付き）
try:
    question_manager = QuestionManager(QUESTIONS_FILE)
    report_generator = ReportGenerator()
except Exception as e:
    print(f"Error initializing question manager: {e}")
    print(f"QUESTIONS_FILE path: {QUESTIONS_FILE}")
    print(f"QUESTIONS_FILE exists: {QUESTIONS_FILE.exists()}")
    # エラーが発生してもアプリは起動できるようにする（後でエラーページを表示）
    question_manager = None
    report_generator = None

# セッションデータ（メモリ上、本番環境ではDBを使用）
sessions = {}


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
    data = request.json
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
    
    sessions[session_id] = session_data
    
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
    session_data = sessions.get(session_id)
    if session_data:
        return jsonify(session_data)
    else:
        return jsonify({'error': 'Session not found'}), 404


@app.route('/api/sessions/<session_id>/answers', methods=['POST'])
def submit_answer(session_id):
    """解答を送信"""
    session_data = sessions.get(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    data = request.json
    question_id = data.get('question_id')
    answer = data.get('answer')
    time_spent = data.get('time_spent', 0)
    
    answer_data = {
        'question_id': question_id,
        'answer': answer,
        'time_spent': time_spent,
        'submitted_at': datetime.now().isoformat()
    }
    
    session_data['answers'].append(answer_data)
    
    return jsonify({'success': True})


@app.route('/api/sessions/<session_id>/report', methods=['GET'])
def get_report(session_id):
    """レポートを生成"""
    if report_generator is None:
        return jsonify({'error': 'Report generator not initialized'}), 500
    session_data = sessions.get(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    # Markdownレポートを生成
    markdown_report = report_generator.generate_markdown_report(session_data)
    
    # JSONレポートも生成
    json_report = report_generator.generate_json_report(session_data)
    
    # セッションデータをファイルに保存（Vercelのサーバーレス環境では/tmpを使用）
    try:
        sessions_dir = SESSIONS_DIR
        sessions_dir.mkdir(parents=True, exist_ok=True)
        report_file = sessions_dir / f"{session_id}.json"
        
        session_data['report'] = json_report
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # ファイル保存に失敗してもレポートは返す
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
    session_data = sessions.get(session_id)
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        # PDFレポートを生成
        pdf_buffer = report_generator.generate_pdf_report(session_data)
        
        # バッファの内容を取得
        pdf_content = pdf_buffer.getvalue()
        
        # PDFが正しく生成されたか確認
        if not pdf_content or len(pdf_content) < 100:
            print(f"⚠️ PDF生成警告: PDFサイズが異常に小さいです ({len(pdf_content)} bytes)")
            return jsonify({'error': 'PDF generation failed: invalid PDF size'}), 500
        
        # レスポンスを返す
        return Response(
            pdf_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=report_{session_id}.pdf',
                'Content-Length': str(len(pdf_content))
            }
        )
    except Exception as e:
        import traceback
        error_msg = f"PDF生成エラー: {str(e)}"
        print(f"❌ {error_msg}")
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500


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

