"""
PDFファイルから問題データを抽出するモジュール
"""
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


def extract_questions_from_pdf(pdf_path: Path, exam_number: int) -> List[Dict[str, Any]]:
    """
    PDFファイルから問題文と選択肢を抽出
    
    Args:
        pdf_path: PDFファイルのパス
        exam_number: 試験回数
        
    Returns:
        問題データのリスト [{
            'exam_number': int,
            'question_number': int,
            'question_text': str,
            'choices': {'1': str, '2': str, '3': str, '4': str}
        }]
    """
    questions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # 全ページのテキストを結合
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # 問題を抽出
            questions = parse_questions_from_text(full_text, exam_number)
            
    except Exception as e:
        print(f"エラー: {pdf_path.name} の読み込みに失敗しました - {e}")
    
    return questions


def parse_questions_from_text(text: str, exam_number: int) -> List[Dict[str, Any]]:
    """
    テキストから問題をパース
    
    Args:
        text: PDFから抽出したテキスト
        exam_number: 試験回数
        
    Returns:
        問題データのリスト
    """
    questions = []
    
    # 問題パターン: 「問題 N」または「問題N」（Nは数字）
    # 選択肢パターン: 「1.」または「1．」（全角・半角両対応）
    
    # 問題番号のパターン
    question_pattern = r'問題\s*(\d+)'
    
    # テキストを行に分割
    lines = text.split('\n')
    
    current_question = None
    current_question_number = None
    current_question_text = ""
    current_choices = {}
    collecting_question_text = False
    collecting_choice = None
    
    i = 0
    while i < len(lines):
        line = line.strip() if (line := lines[i]) else ""
        
        if not line:
            i += 1
            continue
        
        # 問題番号を探す
        question_match = re.search(question_pattern, line)
        if question_match:
            # 前の問題を保存
            if current_question_number is not None:
                question_data = {
                    'exam_number': exam_number,
                    'question_number': current_question_number,
                    'question_text': current_question_text.strip(),
                    'choices': current_choices.copy()
                }
                questions.append(question_data)
            
            # 新しい問題を開始
            current_question_number = int(question_match.group(1))
            # 問題番号の後のテキストを問題文の最初の部分として取得
            after_match = line[question_match.end():].strip()
            current_question_text = after_match
            current_choices = {}
            collecting_question_text = True
            collecting_choice = None
            
        elif current_question_number is not None:
            # 選択肢を探す（1. 2. 3. 4. のパターン）
            choice_match = re.match(r'^(\d+)[．.]\s*(.+)$', line)
            if choice_match:
                choice_num = choice_match.group(1)
                choice_text = choice_match.group(2).strip()
                
                # 選択肢1が見つかったら、問題文の収集を終了
                if choice_num == '1':
                    collecting_question_text = False
                
                # 選択肢が1-4の範囲内か確認
                if choice_num in ['1', '2', '3', '4']:
                    current_choices[choice_num] = choice_text
                    collecting_choice = choice_num
            else:
                # 選択肢の続き（改行された場合）または問題文の続き
                if collecting_choice and current_choices.get(collecting_choice):
                    # 前の選択肢の続きとして追加
                    current_choices[collecting_choice] += " " + line
                elif collecting_question_text:
                    # 問題文の続き（改行を保持）
                    if current_question_text:
                        # 前の行の末尾が句点や疑問符で終わっていない場合は、改行を保持
                        if current_question_text[-1] not in ['。', '？', '?', '.', '）', ')']:
                            current_question_text += " " + line
                        else:
                            # 文が完結している場合は改行を追加（複数行の問題文に対応）
                            current_question_text += "\n" + line
                    else:
                        current_question_text = line
        
        i += 1
    
    # 最後の問題を保存
    if current_question_number is not None:
        question_data = {
            'exam_number': exam_number,
            'question_number': current_question_number,
            'question_text': current_question_text.strip(),
            'choices': current_choices.copy()
        }
        questions.append(question_data)
    
    return questions


def load_all_pdf_files(data_dir = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    指定ディレクトリ内の全PDFファイルを読み込む
    
    Args:
        data_dir: PDFファイルが格納されているディレクトリ（Noneの場合は現在のディレクトリ、Pathまたはstr）
        
    Returns:
        試験回数をキー、問題リストを値とする辞書
    """
    if data_dir is None:
        data_dir = Path('.')
    elif isinstance(data_dir, str):
        data_dir = Path(data_dir)
    
    pdf_files = sorted(data_dir.glob('*.pdf'))
    all_questions_by_exam = {}
    
    for pdf_path in pdf_files:
        # ファイル名から試験回数を抽出
        file_name = pdf_path.stem
        exam_number = None
        
        # パターン1: "29回" または "第29回"
        for i in range(29, 34):
            if f'{i}回' in file_name or f'第{i}回' in file_name:
                exam_number = i
                break
        
        # パターン2: "32 前半" や "29 午前" のような形式（スペース区切り、回が含まれない）
        if exam_number is None:
            # 数字を探す
            match = re.search(r'(\d+)', file_name)
            if match:
                num = int(match.group(1))
                if 29 <= num <= 33:
                    exam_number = num
        
        if exam_number is None:
            print(f"警告: {pdf_path.name} から試験回数を特定できませんでした")
            continue
        
        try:
            questions = extract_questions_from_pdf(pdf_path, exam_number)
            if exam_number not in all_questions_by_exam:
                all_questions_by_exam[exam_number] = []
            all_questions_by_exam[exam_number].extend(questions)
            print(f"読み込み完了: {pdf_path.name} ({len(questions)}問)")
        except Exception as e:
            print(f"エラー: {pdf_path.name} - {e}")
    
    # 各試験回数で問題番号でソート
    for exam_number in all_questions_by_exam:
        all_questions_by_exam[exam_number].sort(key=lambda x: x['question_number'])
    
    return all_questions_by_exam


def merge_questions_by_exam(questions_by_exam: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    試験回数ごとの問題リストを統合（前半・後半をマージ）
    
    Args:
        questions_by_exam: 試験回数をキーとする問題リストの辞書
        
    Returns:
        統合された問題リスト（重複除去済み）
    """
    merged = {}
    
    for exam_number, questions in questions_by_exam.items():
        for q in questions:
            key = (exam_number, q['question_number'])
            if key not in merged:
                merged[key] = q
            else:
                # 既存の問題とマージ（選択肢や問題文が空の場合に上書き）
                existing = merged[key]
                if not existing.get('question_text') and q.get('question_text'):
                    existing['question_text'] = q['question_text']
                for choice_num in ['1', '2', '3', '4']:
                    if not existing.get('choices', {}).get(choice_num) and q.get('choices', {}).get(choice_num):
                        if 'choices' not in existing:
                            existing['choices'] = {}
                        existing['choices'][choice_num] = q['choices'][choice_num]
    
    return list(merged.values())


if __name__ == '__main__':
    # テスト実行
    data_dir = Path('.')
    questions_by_exam = load_all_pdf_files(data_dir)
    
    print(f"\n=== 読み込み結果 ===")
    for exam_number in sorted(questions_by_exam.keys()):
        questions = questions_by_exam[exam_number]
        print(f"第{exam_number}回: {len(questions)}問")
        if questions:
            print(f"  問題番号範囲: {questions[0]['question_number']} - {questions[-1]['question_number']}")
            # 最初の問題を表示
            if questions[0].get('question_text'):
                print(f"  サンプル問題: {questions[0]['question_text'][:50]}...")

