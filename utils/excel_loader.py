"""
Excelファイルから問題データを読み込むモジュール
"""
import openpyxl
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_excel_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Excelファイルから問題データを読み込む
    
    Args:
        file_path: Excelファイルのパス
        
    Returns:
        問題データのリスト
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    
    if not rows:
        return []
    
    # ヘッダーを取得
    header = rows[0]
    questions = []
    
    # ファイル名から試験回数を抽出
    file_name = file_path.stem
    exam_number = None
    for i in range(29, 34):
        if f'第{i}回' in file_name:
            exam_number = i
            break
    
    if exam_number is None:
        raise ValueError(f"試験回数を特定できませんでした: {file_name}")
    
    # データ行を処理
    for row in rows[1:]:
        if not row or not row[0]:  # 空行をスキップ
            continue
        
        question_id = int(row[0]) if isinstance(row[0], (int, float)) else None
        category = row[1] if len(row) > 1 else None
        theme = row[2] if len(row) > 2 else None
        correct_answer = row[3] if len(row) > 3 else None
        
        # 正答を処理（複数正解の場合はリストに変換）
        if isinstance(correct_answer, str) and ',' in str(correct_answer):
            correct_answer_list = [int(x.strip()) for x in str(correct_answer).split(',')]
        elif correct_answer is not None:
            correct_answer_list = [int(float(correct_answer))] if isinstance(correct_answer, (int, float)) else None
        else:
            correct_answer_list = None
        
        if question_id is None or category is None:
            continue
        
        question = {
            "id": f"{exam_number}_{question_id}",
            "exam_number": exam_number,
            "question_number": question_id,
            "category": category,
            "theme": theme or "",
            "correct_answer": correct_answer_list,
            "question_text": "",  # 後で追加可能
            "choices": {
                "1": "",
                "2": "",
                "3": "",
                "4": ""
            },
            "explanation": "",  # 後で追加可能
            "hint": ""  # 後で追加可能
        }
        questions.append(question)
    
    return questions


def load_all_excel_files(data_dir: Path = None) -> List[Dict[str, Any]]:
    """
    指定ディレクトリ内の全Excelファイルを読み込む
    
    Args:
        data_dir: Excelファイルが格納されているディレクトリ（Noneの場合は現在のディレクトリ）
        
    Returns:
        全問題データのリスト
    """
    if data_dir is None:
        data_dir = Path('.')
    
    excel_files = sorted(data_dir.glob('*.xlsx'))
    all_questions = []
    
    for file_path in excel_files:
        try:
            questions = load_excel_file(file_path)
            all_questions.extend(questions)
            print(f"読み込み完了: {file_path.name} ({len(questions)}問)")
        except Exception as e:
            print(f"エラー: {file_path.name} - {e}")
    
    return all_questions


def merge_excel_and_pdf_data(
    excel_questions: List[Dict[str, Any]], 
    pdf_questions_by_exam: Dict[int, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    ExcelデータとPDFデータをマージ
    
    Args:
        excel_questions: Excelから読み込んだ問題データ
        pdf_questions_by_exam: 試験回数をキーとするPDF問題データの辞書
        
    Returns:
        マージされた問題データのリスト
    """
    # PDFデータを辞書に変換（キー: (exam_number, question_number)）
    pdf_dict = {}
    for exam_num, pdf_questions in pdf_questions_by_exam.items():
        for pdf_q in pdf_questions:
            key = (pdf_q['exam_number'], pdf_q['question_number'])
            pdf_dict[key] = pdf_q
    
    # ExcelデータにPDFデータをマージ
    merged_questions = []
    for excel_q in excel_questions:
        key = (excel_q['exam_number'], excel_q['question_number'])
        pdf_q = pdf_dict.get(key)
        
        if pdf_q:
            # PDFデータで上書き（問題文と選択肢）
            excel_q['question_text'] = pdf_q.get('question_text', excel_q.get('theme', ''))
            excel_q['choices'] = pdf_q.get('choices', excel_q.get('choices', {
                "1": "", "2": "", "3": "", "4": ""
            }))
        else:
            # PDFデータがない場合はテーマを問題文として使用
            if not excel_q.get('question_text'):
                excel_q['question_text'] = excel_q.get('theme', '')
        
        merged_questions.append(excel_q)
    
    return merged_questions


def save_questions_to_json(questions: List[Dict[str, Any]], output_path: Path):
    """
    問題データをJSONファイルに保存
    
    Args:
        questions: 問題データのリスト
        output_path: 出力先のJSONファイルパス
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {output_path} ({len(questions)}問)")


def load_all_data_with_pdf(data_dir: Path = None) -> List[Dict[str, Any]]:
    """
    ExcelとPDFの両方からデータを読み込んでマージ
    
    Args:
        data_dir: データディレクトリ（Noneの場合は現在のディレクトリ）
        
    Returns:
        マージされた問題データのリスト
    """
    if data_dir is None:
        data_dir = Path('.')
    
    # Excelデータを読み込み
    print("=== Excelデータの読み込み ===")
    excel_questions = load_all_excel_files(data_dir)
    
    # PDFデータを読み込み
    print("\n=== PDFデータの読み込み ===")
    try:
        import sys
        from pathlib import Path
        # スクリプトとして実行する場合のパス調整
        script_dir = Path(__file__).parent.parent
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from utils.pdf_loader import load_all_pdf_files, merge_questions_by_exam
        pdf_questions_by_exam_raw = load_all_pdf_files(data_dir)
        # 各試験回数で問題をマージ（前半・後半の統合）
        pdf_questions_by_exam = {}
        for exam_num, questions_list in pdf_questions_by_exam_raw.items():
            pdf_questions_by_exam[exam_num] = merge_questions_by_exam({exam_num: questions_list})
    except Exception as e:
        print(f"警告: PDFローダーをインポートできませんでした。PDFデータをスキップします。 - {e}")
        pdf_questions_by_exam = {}
    
    # データをマージ
    print("\n=== データのマージ ===")
    merged_questions = merge_excel_and_pdf_data(excel_questions, pdf_questions_by_exam)
    
    # 問題番号でソート
    merged_questions.sort(key=lambda x: (x['exam_number'], x['question_number']))
    
    return merged_questions


if __name__ == '__main__':
    # スクリプトとして実行された場合、データを読み込んでJSONに保存
    data_dir = Path('.')
    
    # ExcelとPDFの両方からデータを読み込む
    try:
        questions = load_all_data_with_pdf(data_dir)
    except Exception as e:
        print(f"エラー: PDFデータの読み込みに失敗しました。Excelデータのみを使用します。 - {e}")
        questions = load_all_excel_files(data_dir)
    
    output_dir = Path('data')
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'questions.json'
    
    save_questions_to_json(questions, output_path)
    
    # 統計情報を表示
    categories = {}
    questions_with_text = 0
    questions_with_choices = 0
    
    for q in questions:
        cat = q['category']
        categories[cat] = categories.get(cat, 0) + 1
        
        if q.get('question_text') and q.get('question_text').strip():
            questions_with_text += 1
        
        choices = q.get('choices', {})
        if choices.get('1') or choices.get('2') or choices.get('3') or choices.get('4'):
            questions_with_choices += 1
    
    print(f"\n総問題数: {len(questions)}")
    print(f"問題文あり: {questions_with_text}問 ({questions_with_text/len(questions)*100:.1f}%)")
    print(f"選択肢あり: {questions_with_choices}問 ({questions_with_choices/len(questions)*100:.1f}%)")
    print(f"\nジャンル別問題数:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}問")

