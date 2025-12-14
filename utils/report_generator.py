"""
フィードバックレポート生成モジュール
"""
from typing import Dict, List, Any, BinaryIO
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_markdown_report(self, session_data: Dict[str, Any]) -> str:
        """
        Notebook.lm用のMarkdownレポートを生成
        
        Args:
            session_data: セッションデータ（解答履歴、問題データなど）
            
        Returns:
            Markdown形式のレポート文字列
        """
        answers = session_data.get('answers', [])
        questions = session_data.get('questions', [])
        mode = session_data.get('mode', 'test')
        exam_numbers = session_data.get('exam_numbers', [])
        categories = session_data.get('categories', [])
        
        # 問題データを辞書に変換（IDをキーに）
        question_dict = {q['id']: q for q in questions}
        
        # 統計を計算
        total = len(answers)
        correct = 0
        incorrect = 0
        unanswered = 0
        
        category_stats = {}
        
        for answer_data in answers:
            question_id = answer_data['question_id']
            user_answer = answer_data.get('answer')
            question = question_dict.get(question_id)
            
            if not question:
                continue
            
            # ジャンル統計の初期化
            cat = question['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'correct': 0, 'incorrect': 0, 'unanswered': 0}
            
            category_stats[cat]['total'] += 1
            
            # 正誤判定
            correct_answer = question.get('correct_answer', [])
            if user_answer is None:
                unanswered += 1
                category_stats[cat]['unanswered'] += 1
            elif isinstance(user_answer, list):
                if set(user_answer) == set(correct_answer):
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
            else:
                if user_answer in correct_answer:
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
        
        # Markdownレポートを生成
        report_lines = []
        
        # ヘッダー
        report_lines.append("# 国家試験対策 フィードバックレポート")
        report_lines.append("")
        report_lines.append(f"**試験日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")
        report_lines.append(f"**モード**: {'テストモード' if mode == 'test' else '学習モード'}")
        report_lines.append("")
        
        # 試験回数とジャンル
        if exam_numbers:
            report_lines.append(f"**試験回数**: 第{', 第'.join(map(str, exam_numbers))}回")
        if categories:
            report_lines.append(f"**選択ジャンル**: {', '.join(categories)}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # 総合成績
        report_lines.append("## 総合成績")
        report_lines.append("")
        correct_rate = (correct / total * 100) if total > 0 else 0
        report_lines.append(f"- **総問題数**: {total}問")
        report_lines.append(f"- **正答数**: {correct}問")
        report_lines.append(f"- **誤答数**: {incorrect}問")
        report_lines.append(f"- **未回答**: {unanswered}問")
        report_lines.append(f"- **正答率**: {correct_rate:.1f}%")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # ジャンル別成績
        if category_stats:
            report_lines.append("## ジャンル別成績")
            report_lines.append("")
            
            # 正答率でソート
            sorted_categories = sorted(
                category_stats.items(),
                key=lambda x: (x[1]['correct'] / x[1]['total'] * 100) if x[1]['total'] > 0 else 0,
                reverse=True
            )
            
            for cat, stats in sorted_categories:
                cat_correct_rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                report_lines.append(f"### {cat}")
                report_lines.append(f"- 問題数: {stats['total']}問")
                report_lines.append(f"- 正答: {stats['correct']}問")
                report_lines.append(f"- 誤答: {stats['incorrect']}問")
                report_lines.append(f"- 未回答: {stats['unanswered']}問")
                report_lines.append(f"- **正答率: {cat_correct_rate:.1f}%**")
                report_lines.append("")
            
            report_lines.append("---")
            report_lines.append("")
        
        # 問題別詳細
        report_lines.append("## 問題別詳細")
        report_lines.append("")
        
        for i, answer_data in enumerate(answers, 1):
            question_id = answer_data['question_id']
            user_answer = answer_data.get('answer')
            time_spent = answer_data.get('time_spent', 0)
            question = question_dict.get(question_id)
            
            if not question:
                continue
            
            report_lines.append(f"### 問題 {i} (第{question['exam_number']}回 問{question['question_number']})")
            report_lines.append(f"**ジャンル**: {question['category']}")
            report_lines.append(f"**テーマ**: {question.get('theme', '')}")
            report_lines.append("")
            
            # 正誤マーク
            correct_answer = question.get('correct_answer', [])
            if user_answer is None:
                report_lines.append("**結果**: ⚪ 未回答")
            elif isinstance(user_answer, list):
                if set(user_answer) == set(correct_answer):
                    report_lines.append("**結果**: ✅ 正解")
                else:
                    report_lines.append("**結果**: ❌ 不正解")
            else:
                if user_answer in correct_answer:
                    report_lines.append("**結果**: ✅ 正解")
                else:
                    report_lines.append("**結果**: ❌ 不正解")
            
            report_lines.append(f"**あなたの回答**: {user_answer if user_answer is not None else '未回答'}")
            report_lines.append(f"**正解**: {correct_answer}")
            report_lines.append(f"**解答時間**: {time_spent:.1f}秒")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_json_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON形式のレポートを生成（API用）
        
        Args:
            session_data: セッションデータ
            
        Returns:
            JSON形式のレポート辞書
        """
        answers = session_data.get('answers', [])
        questions = session_data.get('questions', [])
        
        question_dict = {q['id']: q for q in questions}
        
        # 統計計算
        total = len(answers)
        correct = 0
        incorrect = 0
        unanswered = 0
        
        category_stats = {}
        
        for answer_data in answers:
            question_id = answer_data['question_id']
            user_answer = answer_data.get('answer')
            question = question_dict.get(question_id)
            
            if not question:
                continue
            
            cat = question['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'correct': 0, 'incorrect': 0, 'unanswered': 0}
            
            category_stats[cat]['total'] += 1
            
            correct_answer = question.get('correct_answer', [])
            if user_answer is None:
                unanswered += 1
                category_stats[cat]['unanswered'] += 1
            elif isinstance(user_answer, list):
                if set(user_answer) == set(correct_answer):
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
            else:
                if user_answer in correct_answer:
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'unanswered': unanswered,
            'correct_rate': (correct / total * 100) if total > 0 else 0,
            'category_stats': category_stats,
            'answers': answers,
            'questions': questions
        }
    
    def generate_pdf_report(self, session_data: Dict[str, Any]) -> BytesIO:
        """
        PDF形式のレポートを生成
        
        Args:
            session_data: セッションデータ
            
        Returns:
            PDFファイルのBytesIOオブジェクト
        """
        answers = session_data.get('answers', [])
        questions = session_data.get('questions', [])
        mode = session_data.get('mode', 'test')
        exam_numbers = session_data.get('exam_numbers', [])
        categories = session_data.get('categories', [])
        
        # 問題データを辞書に変換
        question_dict = {q['id']: q for q in questions}
        
        # 統計を計算
        total = len(answers)
        correct = 0
        incorrect = 0
        unanswered = 0
        category_stats = {}
        
        for answer_data in answers:
            question_id = answer_data['question_id']
            user_answer = answer_data.get('answer')
            question = question_dict.get(question_id)
            
            if not question:
                continue
            
            cat = question['category']
            if cat not in category_stats:
                category_stats[cat] = {'total': 0, 'correct': 0, 'incorrect': 0, 'unanswered': 0}
            
            category_stats[cat]['total'] += 1
            
            correct_answer = question.get('correct_answer', [])
            if user_answer is None:
                unanswered += 1
                category_stats[cat]['unanswered'] += 1
            elif isinstance(user_answer, list):
                if set(user_answer) == set(correct_answer):
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
            else:
                if user_answer in correct_answer:
                    correct += 1
                    category_stats[cat]['correct'] += 1
                else:
                    incorrect += 1
                    category_stats[cat]['incorrect'] += 1
        
        # PDF生成
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        
        # 日本語フォントの登録
        try:
            # reportlabの組み込み日本語フォントを試す
            font_registered = False
            japanese_font_name = 'Helvetica'
            
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
                japanese_font_name = 'HeiseiKakuGo-W5'
                font_registered = True
            except:
                try:
                    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                    japanese_font_name = 'HeiseiMin-W3'
                    font_registered = True
                except:
                    pass
            
            if not font_registered:
                # TTFファイルを探す（フォールバック）
                from pathlib import Path
                font_paths = [
                    Path.home() / 'Library/Fonts/NotoSansCJK-Regular.ttc',
                    '/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc',
                ]
                
                for font_path in font_paths:
                    if font_path.exists():
                        try:
                            pdfmetrics.registerFont(TTFont('JapaneseFont', str(font_path)))
                            japanese_font_name = 'JapaneseFont'
                            font_registered = True
                            break
                        except:
                            continue
        except Exception as e:
            print(f"フォント登録エラー: {e}")
            japanese_font_name = 'Helvetica'
        
        # スタイル設定
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=japanese_font_name,
            fontSize=18,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            alignment=1  # 中央揃え
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName=japanese_font_name,
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=10,
            spaceBefore=12
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=japanese_font_name,
            fontSize=10,
            leading=14
        )
        
        story = []
        
        # タイトル
        story.append(Paragraph("国家試験対策 フィードバックレポート", title_style))
        story.append(Spacer(1, 12))
        
        # 基本情報
        story.append(Paragraph(f"<b>試験日時</b>: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}", normal_style))
        story.append(Paragraph(f"<b>モード</b>: {'テストモード' if mode == 'test' else '学習モード'}", normal_style))
        if exam_numbers:
            story.append(Paragraph(f"<b>試験回数</b>: 第{', 第'.join(map(str, exam_numbers))}回", normal_style))
        if categories:
            story.append(Paragraph(f"<b>選択ジャンル</b>: {', '.join(categories)}", normal_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph("─" * 50, normal_style))
        story.append(Spacer(1, 12))
        
        # 総合成績
        story.append(Paragraph("総合成績", heading_style))
        correct_rate = (correct / total * 100) if total > 0 else 0
        
        summary_data = [
            ['項目', '数値'],
            ['総問題数', f'{total}問'],
            ['正答数', f'{correct}問'],
            ['誤答数', f'{incorrect}問'],
            ['未回答', f'{unanswered}問'],
            ['正答率', f'{correct_rate:.1f}%']
        ]
        
        summary_table = Table(summary_data, colWidths=[80*mm, 80*mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))
        
        # ジャンル別成績
        if category_stats:
            story.append(Paragraph("ジャンル別成績", heading_style))
            
            sorted_categories = sorted(
                category_stats.items(),
                key=lambda x: (x[1]['correct'] / x[1]['total'] * 100) if x[1]['total'] > 0 else 0,
                reverse=True
            )
            
            for cat, stats in sorted_categories:
                cat_correct_rate = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                story.append(Paragraph(f"<b>{cat}</b>", normal_style))
                cat_data = [
                    ['問題数', f"{stats['total']}問"],
                    ['正答', f"{stats['correct']}問"],
                    ['誤答', f"{stats['incorrect']}問"],
                    ['未回答', f"{stats['unanswered']}問"],
                    ['正答率', f"{cat_correct_rate:.1f}%"]
                ]
                cat_table = Table(cat_data, colWidths=[40*mm, 40*mm])
                cat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                story.append(cat_table)
                story.append(Spacer(1, 8))
            
            story.append(Spacer(1, 12))
        
        # 問題別詳細
        story.append(Paragraph("問題別詳細", heading_style))
        
        for i, answer_data in enumerate(answers, 1):
            question_id = answer_data['question_id']
            user_answer = answer_data.get('answer')
            time_spent = answer_data.get('time_spent', 0)
            question = question_dict.get(question_id)
            
            if not question:
                continue
            
            # 問題番号と基本情報
            story.append(Paragraph(
                f"<b>問題 {i}</b> (第{question['exam_number']}回 問{question['question_number']})",
                normal_style
            ))
            story.append(Paragraph(f"ジャンル: {question['category']}", normal_style))
            story.append(Paragraph(f"テーマ: {question.get('theme', '')}", normal_style))
            
            # 正誤判定
            correct_answer = question.get('correct_answer', [])
            if user_answer is None:
                result_text = "⚪ 未回答"
                result_color = colors.grey
            elif isinstance(user_answer, list):
                if set(user_answer) == set(correct_answer):
                    result_text = "✅ 正解"
                    result_color = colors.green
                else:
                    result_text = "❌ 不正解"
                    result_color = colors.red
            else:
                if user_answer in correct_answer:
                    result_text = "✅ 正解"
                    result_color = colors.green
                else:
                    result_text = "❌ 不正解"
                    result_color = colors.red
            
            result_style = ParagraphStyle('Result', parent=normal_style, textColor=result_color)
            story.append(Paragraph(f"<b>結果</b>: {result_text}", result_style))
            story.append(Paragraph(
                f"あなたの回答: {user_answer if user_answer is not None else '未回答'}",
                normal_style
            ))
            story.append(Paragraph(f"正解: {correct_answer}", normal_style))
            story.append(Paragraph(f"解答時間: {time_spent:.1f}秒", normal_style))
            story.append(Spacer(1, 8))
            
            # ページ区切り（10問ごと）
            if i % 10 == 0 and i < len(answers):
                story.append(PageBreak())
        
        # PDF生成
        doc.build(story)
        buffer.seek(0)
        return buffer

