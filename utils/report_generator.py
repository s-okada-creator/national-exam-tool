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
            
            # 選択肢データを取得（クロージャで確実に参照できるように）
            choices = question.get('choices', {})
            choices_for_text = choices  # ローカル変数として明示的に保持
            
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
            
            # 選択肢の内容を表示するヘルパー関数（choices_for_textを確実に参照）
            def fmt_answer_text(ans):
                if ans is None:
                    return '未回答'
                # リストの場合は各要素を処理
                if isinstance(ans, list):
                    if len(ans) == 0:
                        return '正解データなし'
                    return ', '.join([fmt_answer_text(a) for a in ans])
                # 文字列や数値を文字列に変換
                ans_str = str(ans)
                choice_text = choices_for_text.get(ans_str, '')
                if choice_text and choice_text.strip():
                    return f"{ans_str}. {choice_text}"
                return str(ans)
            
            # あなたの回答と正解を選択肢の内容付きで表示
            user_answer_text = fmt_answer_text(user_answer)
            # correct_answerはリスト形式なので、そのまま渡す
            correct_answer_text = fmt_answer_text(correct_answer) if correct_answer else '正解データなし'
            report_lines.append(f"**あなたの回答**: {user_answer_text}")
            report_lines.append(f"**正解**: {correct_answer_text}")
            
            # 不正解の場合、解説文を追加表示
            is_incorrect = False
            if user_answer is None:
                is_incorrect = False
            elif isinstance(user_answer, list):
                is_incorrect = set(user_answer) != set(correct_answer)
            else:
                is_incorrect = user_answer not in correct_answer
            
            if is_incorrect:
                explanation = question.get('explanation', '')
                if explanation and explanation.strip():
                    report_lines.append(f"**解説**: {explanation}")
                else:
                    # 解説がない場合は、正解の選択肢の内容を解説として表示
                    correct_choice_text = fmt_answer_text(correct_answer)
                    if correct_choice_text and correct_choice_text != '正解データなし':
                        report_lines.append(f"**解説**: 正解は {correct_choice_text} です。")
            
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
        
        # PDF生成（フォント埋め込みを有効化）
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm,
                                title="国家試験対策 フィードバックレポート",
                                author="国家試験対策ツール")
        
        # 日本語フォントの登録（根本的な改善：TTFフォントを優先して確実に埋め込む）
        font_registered = False
        japanese_font_name = 'Helvetica'
        
        try:
            from pathlib import Path
            import platform
            
            # TTFフォントを優先（PDFに埋め込まれる）
            # 1) macOSのシステムフォントから日本語TTFフォントを探す（最優先）
            if platform.system() == 'Darwin':
                ttf_candidates = [
                    '/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf',
                    '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                ]
                
                for ttf_path in ttf_candidates:
                    ttf_obj = Path(ttf_path)
                    if not ttf_obj.exists():
                        continue
                    try:
                        font_id = f"JapaneseFontTTF_{ttf_obj.stem}"
                        pdfmetrics.registerFont(TTFont(font_id, str(ttf_obj)))
                        japanese_font_name = font_id
                        font_registered = True
                        print(f"✅ 日本語フォント登録成功（TTFont）: {japanese_font_name} ({ttf_obj})")
                        print(f"   ✅ このフォントはPDFに埋め込まれます")
                        break
                    except Exception as e:
                        print(f"⚠️ フォント登録失敗 ({ttf_obj}): {e}")
                        continue
            
            # 2) プロジェクト内のフォントを試行（TTFを優先、OTFも試行）
            if not font_registered:
                project_root = Path(__file__).parent.parent
                bundled_fonts = [
                    project_root / 'fonts' / 'NotoSansJP-Regular.ttf',  # TTFを優先
                    project_root / 'fonts' / 'NotoSansJP-Regular.otf',  # OTFも試行
                ]
                
                for bundled_font in bundled_fonts:
                    if bundled_font.exists():
                        try:
                            font_id = "JapaneseFontBundled"
                            pdfmetrics.registerFont(TTFont(font_id, str(bundled_font)))
                            # フォント登録成功（日本語フォントとして使用可能と仮定）
                            japanese_font_name = font_id
                            font_registered = True
                            print(f"✅ 日本語フォント登録成功（同梱フォント）: {japanese_font_name} ({bundled_font})")
                            break
                        except Exception as e:
                            print(f"⚠️ 同梱フォント登録失敗 ({bundled_font}): {e}")
                            continue
            
            # 3) NotoSansCJKのTTCから日本語サブフォントを探す（優先度高い）
            if not font_registered:
                noto_cjk_candidates = [
                    str(Path.home() / 'Library/Fonts/NotoSansCJK-Regular.ttc'),
                    '/System/Library/Fonts/Supplemental/NotoSansCJK-Regular.ttc',
                ]
                
                for font_path in noto_cjk_candidates:
                    font_path_obj = Path(font_path)
                    if not font_path_obj.exists():
                        continue
                    # サブフォントインデックス0-7を試行（日本語は通常0または1）
                    for sub_idx in range(8):
                        try:
                            font_id = f"NotoSansCJK_{sub_idx}"
                            pdfmetrics.registerFont(TTFont(font_id, str(font_path_obj), subfontIndex=sub_idx))
                            # フォント登録成功（日本語フォントとして使用可能と仮定）
                            japanese_font_name = font_id
                            font_registered = True
                            print(f"✅ 日本語フォント登録成功（NotoSansCJK/TTC）: {japanese_font_name} ({font_path_obj}, subfontIndex={sub_idx})")
                            break
                        except Exception:
                            continue
                    if font_registered:
                        break
            
            # 4) ヒラギノフォントのTTCから日本語サブフォントを探す
            if not font_registered:
                hiragino_candidates = [
                    '/System/Library/Fonts/Supplemental/ヒラギノ角ゴシック W3.ttc',
                    '/System/Library/Fonts/Supplemental/ヒラギノ角ゴシック W6.ttc',
                    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
                    '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
                ]
                
                for font_path in hiragino_candidates:
                    font_path_obj = Path(font_path)
                    if not font_path_obj.exists():
                        continue
                    # サブフォントインデックス0-7を試行
                    for sub_idx in range(8):
                        try:
                            font_id = f"Hiragino_{sub_idx}"
                            pdfmetrics.registerFont(TTFont(font_id, str(font_path_obj), subfontIndex=sub_idx))
                            # フォント登録成功（日本語フォントとして使用可能と仮定）
                            japanese_font_name = font_id
                            font_registered = True
                            print(f"✅ 日本語フォント登録成功（ヒラギノ/TTC）: {japanese_font_name} ({font_path_obj}, subfontIndex={sub_idx})")
                            break
                        except Exception:
                            continue
                    if font_registered:
                        break
            
            # 5) 組み込みCIDフォントをフォールバック（埋め込まれないが、最後の手段）
            # 注意: UnicodeCIDFontはPDFに埋め込まれないため、PDFビューアがフォントを持っていない場合、文字化けが発生します
            # 可能な限り、上記のTTFontを使用してください
            if not font_registered:
                try:
                    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
                    japanese_font_name = 'HeiseiKakuGo-W5'
                    font_registered = True
                    print(f"⚠️ 日本語フォント登録（UnicodeCIDFont、埋め込まれません）: {japanese_font_name}")
                    print(f"   ⚠️ 警告: このフォントはPDFに埋め込まれないため、PDFビューアにフォントがない場合、文字化けする可能性があります。")
                    print(f"   ⚠️ 推奨: TTFontを使用してフォントを埋め込むことを強く推奨します。")
                except Exception as e1:
                    try:
                        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                        japanese_font_name = 'HeiseiMin-W3'
                        font_registered = True
                        print(f"⚠️ 日本語フォント登録（UnicodeCIDFont、埋め込まれません）: {japanese_font_name}")
                        print(f"   ⚠️ 警告: このフォントはPDFに埋め込まれないため、PDFビューアにフォントがない場合、文字化けする可能性があります。")
                        print(f"   ⚠️ 推奨: TTFontを使用してフォントを埋め込むことを強く推奨します。")
                    except Exception as e2:
                        print(f"⚠️ 組み込みフォント登録失敗: {e1}, {e2}")
            
            # フォント登録の最終確認
            if font_registered:
                registered_fonts = pdfmetrics.getRegisteredFontNames()
                if japanese_font_name not in registered_fonts:
                    print(f"⚠️ 警告: フォント '{japanese_font_name}' が登録フォントリストにありません")
                    font_registered = False
                else:
                    print(f"✅ フォント確認: '{japanese_font_name}' が正しく登録されています")
                    # TTFontかどうかを確認（埋め込まれるかどうか）
                    try:
                        font_obj = pdfmetrics.getFont(japanese_font_name)
                        if isinstance(font_obj, TTFont):
                            print(f"✅ フォントタイプ: TTFont（PDFに埋め込まれます）")
                        elif isinstance(font_obj, UnicodeCIDFont):
                            print(f"⚠️ フォントタイプ: UnicodeCIDFont（PDFに埋め込まれません）")
                    except Exception:
                        pass
            
            if not font_registered:
                print("❌ 警告: 日本語フォントが見つかりません。Helveticaを使用します（文字化けの可能性があります）")
        except Exception as e:
            print(f"❌ フォント登録エラー: {e}")
            import traceback
            traceback.print_exc()
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
        
        # フォント登録の確認（テーブル生成前に再確認）
        if not font_registered:
            print(f"⚠️ 警告: 日本語フォントが登録されていません。テーブル内の日本語が文字化けする可能性があります。")
        else:
            # フォントが正しく登録されているか確認
            try:
                registered_fonts = pdfmetrics.getRegisteredFontNames()
                if japanese_font_name not in registered_fonts:
                    print(f"⚠️ 警告: フォント '{japanese_font_name}' が登録フォントリストに見つかりません。")
                    # フォント名を再確認
                    print(f"   登録されているフォント: {registered_fonts[:10]}")
                else:
                    print(f"✅ フォント確認: '{japanese_font_name}' が正しく登録されています。")
                    # フォント情報を取得して確認
                    try:
                        font_obj = pdfmetrics.getFont(japanese_font_name)
                        print(f"   フォントオブジェクト: {type(font_obj).__name__}")
                    except Exception as e:
                        print(f"   フォントオブジェクト取得エラー: {e}")
            except Exception as e:
                print(f"⚠️ フォント確認エラー: {e}")
        
        # テーブル用スタイルを完全に独立して定義（parentを使わず、すべての属性を明示的に設定）
        # ヘッダー用のスタイル（白文字、日本語フォント）
        header_normal_style = ParagraphStyle(
            'TableHeaderNormal',
            fontName=japanese_font_name,
            fontSize=11,
            textColor=colors.whitesmoke,
            leading=14,
            alignment=0,  # 左揃え
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
            firstLineIndent=0
        )
        
        # データ行用のスタイル（日本語フォント）
        data_style = ParagraphStyle(
            'TableData',
            fontName=japanese_font_name,
            fontSize=10,
            leading=14,
            alignment=0,  # 左揃え
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
            firstLineIndent=0
        )
        
        summary_data = [
            [Paragraph('項目', header_normal_style), Paragraph('数値', header_normal_style)],
            [Paragraph('総問題数', data_style), Paragraph(f'{total}問', data_style)],
            [Paragraph('正答数', data_style), Paragraph(f'{correct}問', data_style)],
            [Paragraph('誤答数', data_style), Paragraph(f'{incorrect}問', data_style)],
            [Paragraph('未回答', data_style), Paragraph(f'{unanswered}問', data_style)],
            [Paragraph('正答率', data_style), Paragraph(f'{correct_rate:.1f}%', data_style)]
        ]
        
        summary_table = Table(summary_data, colWidths=[80*mm, 80*mm])
        # テーブルスタイル（TEXTCOLORを削除し、ParagraphStyleのtextColorに完全に依存）
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
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
                # テーブル用スタイルを完全に独立して定義（parentを使わず、すべての属性を明示的に設定）
                # ジャンル別テーブル用のスタイル
                cat_header_style = ParagraphStyle(
                    'CatHeader',
                    fontName=japanese_font_name,
                    fontSize=9,
                    leading=12,
                    alignment=0,  # 左揃え
                    leftIndent=0,
                    rightIndent=0,
                    spaceBefore=0,
                    spaceAfter=0,
                    firstLineIndent=0
                )
                cat_data_style = ParagraphStyle(
                    'CatData',
                    fontName=japanese_font_name,
                    fontSize=9,
                    leading=12,
                    alignment=0,  # 左揃え
                    leftIndent=0,
                    rightIndent=0,
                    spaceBefore=0,
                    spaceAfter=0,
                    firstLineIndent=0
                )
                cat_data = [
                    [Paragraph('問題数', cat_header_style), Paragraph(f"{stats['total']}問", cat_data_style)],
                    [Paragraph('正答', cat_data_style), Paragraph(f"{stats['correct']}問", cat_data_style)],
                    [Paragraph('誤答', cat_data_style), Paragraph(f"{stats['incorrect']}問", cat_data_style)],
                    [Paragraph('未回答', cat_data_style), Paragraph(f"{stats['unanswered']}問", cat_data_style)],
                    [Paragraph('正答率', cat_data_style), Paragraph(f"{cat_correct_rate:.1f}%", cat_data_style)]
                ]
                cat_table = Table(cat_data, colWidths=[40*mm, 40*mm])
                # テーブルスタイル（フォント関連の設定を一切含めない）
                cat_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(cat_table)

                # 問題詳細をカテゴリごとに追加（問題文/ユーザー回答/正解/結果/時間）
                cat_questions = [q for q in questions if q.get('category') == cat]
                if cat_questions:
                    detail_header_style = ParagraphStyle(
                        'DetailHeader',
                        fontName=japanese_font_name,
                        fontSize=9,
                        leading=12,
                        textColor=colors.whitesmoke,
                        alignment=0,
                        leftIndent=0,
                        rightIndent=0,
                        spaceBefore=0,
                        spaceAfter=0,
                        firstLineIndent=0
                    )
                    detail_cell_style = ParagraphStyle(
                        'DetailCell',
                        fontName=japanese_font_name,
                        fontSize=8.5,
                        leading=12,
                        alignment=0,
                        leftIndent=0,
                        rightIndent=0,
                        spaceBefore=0,
                        spaceAfter=0,
                        firstLineIndent=0
                    )

                    detail_data = [
                        [
                            Paragraph('問題', detail_header_style),
                            Paragraph('あなたの回答', detail_header_style),
                            Paragraph('正解', detail_header_style),
                            Paragraph('結果', detail_header_style),
                            Paragraph('時間(秒)', detail_header_style),
                        ]
                    ]

                    for q in cat_questions:
                        answer_data = next((a for a in answers if a['question_id'] == q['id']), None)
                        user_answer = answer_data.get('answer') if answer_data else None
                        time_spent = answer_data.get('time_spent', 0) if answer_data else 0
                        correct_answer = q.get('correct_answer', [])

                        # 結果判定
                        if user_answer is None:
                            result_text = "未回答"
                            result_color = colors.grey
                        elif isinstance(user_answer, list):
                            result_text = "正解" if set(user_answer) == set(correct_answer) else "不正解"
                            result_color = colors.green if result_text == "正解" else colors.red
                        else:
                            result_text = "正解" if user_answer in correct_answer else "不正解"
                            result_color = colors.green if result_text == "正解" else colors.red

                        result_style = ParagraphStyle(
                            'DetailResult',
                            parent=detail_cell_style,
                            textColor=result_color
                        )

                        # 問題タイトル（試験回＋問番号＋問題文）
                        question_text = q.get('question_text', '') or ''
                        qt_formatted = question_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                        problem_label = f"第{q.get('exam_number', '')}回 問{q.get('question_number', '')}<br/>{qt_formatted}"

                        # 選択肢の内容を取得するヘルパー関数
                        choices = q.get('choices', {})
                        def fmt_answer_with_text(ans_val):
                            if ans_val is None:
                                return '未回答'
                            if isinstance(ans_val, list):
                                return '<br/>'.join([fmt_answer_with_text(a) for a in ans_val])
                            ans_str = str(ans_val)
                            choice_text = choices.get(ans_str, '')
                            if choice_text:
                                choice_fmt = choice_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                                return f"[{ans_str}] {choice_fmt}"
                            return f"[{ans_str}]"

                        # 正解の選択肢内容を取得
                        def fmt_correct_with_text(correct_val):
                            if correct_val is None or (isinstance(correct_val, list) and len(correct_val) == 0):
                                return '正解データなし'
                            if isinstance(correct_val, list):
                                return '<br/>'.join([fmt_answer_with_text(a) for a in correct_val])
                            return fmt_answer_with_text(correct_val)

                        user_answer_text = fmt_answer_with_text(user_answer)
                        correct_answer_text = fmt_correct_with_text(correct_answer)

                        detail_data.append([
                            Paragraph(problem_label, detail_cell_style),
                            Paragraph(user_answer_text, detail_cell_style),
                            Paragraph(correct_answer_text, detail_cell_style),
                            Paragraph(result_text, result_style),
                            Paragraph(f"{time_spent:.1f}", detail_cell_style),
                        ])

                    detail_table = Table(detail_data, colWidths=[60*mm, 50*mm, 50*mm, 20*mm, 15*mm])
                    detail_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4c51bf')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(detail_table)
                    story.append(Spacer(1, 8))

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
            if question.get('theme'):
                story.append(Paragraph(f"テーマ: {question.get('theme', '')}", normal_style))
            story.append(Spacer(1, 6))
            
            # 問題文を表示（強化版）
            question_text = question.get('question_text', '')
            if question_text and question_text.strip():
                # 問題文のスタイル（強調表示）
                question_text_style = ParagraphStyle(
                    'QuestionText',
                    fontName=japanese_font_name,
                    fontSize=11,
                    leading=16,
                    spaceAfter=10,
                    spaceBefore=6,
                    leftIndent=0,
                    rightIndent=0,
                    backColor=colors.HexColor('#f0f4ff'),
                    borderPadding=6
                )
                # 改行を保持して表示、HTMLエスケープも考慮
                question_text_formatted = question_text.replace('\n', '<br/>')
                # 特殊文字をエスケープ
                question_text_formatted = question_text_formatted.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                question_text_formatted = question_text_formatted.replace('<br/>', '<br/>')  # brタグは残す
                story.append(Paragraph(f"<b><font color='#1e40af'>【問題文】</font></b><br/>{question_text_formatted}", question_text_style))
                story.append(Spacer(1, 8))
            else:
                # 問題文が存在しない場合のエラーメッセージ
                story.append(Paragraph("<b><font color='#dc2626'>【問題文】</font></b> 問題文が取得できませんでした", normal_style))
                story.append(Spacer(1, 6))
            
            # 選択肢データを先に取得（後で使用するため）
            choices = question.get('choices', {})
            
            # 選択肢を表示
            if choices and any(choices.values()):
                story.append(Paragraph("<b>【選択肢】</b>", normal_style))
                for choice_num in ['1', '2', '3', '4']:
                    choice_text = choices.get(choice_num, '')
                    if choice_text and choice_text.strip():
                        # 選択肢のスタイル
                        choice_style = ParagraphStyle(
                            'Choice',
                            fontName=japanese_font_name,
                            fontSize=10,
                            leading=14,
                            leftIndent=20,
                            spaceAfter=4
                        )
                        # 改行を保持して表示、HTMLエスケープも考慮
                        choice_text_formatted = choice_text.replace('\n', '<br/>')
                        # 特殊文字をエスケープ
                        choice_text_formatted = choice_text_formatted.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        choice_text_formatted = choice_text_formatted.replace('<br/>', '<br/>')  # brタグは残す
                        story.append(Paragraph(f"{choice_num}. {choice_text_formatted}", choice_style))
                story.append(Spacer(1, 6))
            
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
            
            # 正誤判定結果を取得（fmt_answerで使用するため）
            is_user_correct = False
            if user_answer is None:
                is_user_correct = False
            elif isinstance(user_answer, list):
                is_user_correct = set(user_answer) == set(correct_answer)
            else:
                is_user_correct = user_answer in correct_answer
            
            # 結果を強調表示
            result_style = ParagraphStyle(
                'Result',
                fontName=japanese_font_name,
                fontSize=12,
                leading=16,
                textColor=result_color,
                spaceAfter=8,
                spaceBefore=8,
                leftIndent=0,
                rightIndent=0
            )
            story.append(Paragraph(f"<b>結果:</b> {result_text}", result_style))
            
            # 区切り線を追加
            story.append(Paragraph("─" * 60, normal_style))
            
            # 選択肢本文を表示するためのヘルパー（改善版）
            # choices変数をクロージャで確実に参照できるようにする
            choices_for_answer = choices  # ローカル変数として明示的に保持
            
            def fmt_answer(ans, is_user_correct_flag=False):
                if ans is None:
                    return '<font color="#6b7280">未回答</font>'
                if isinstance(ans, list):
                    return '<br/>'.join([fmt_answer(a, is_user_correct_flag) for a in ans])
                # ansが数字のとき、選択肢本文を引く
                ans_str = str(ans)
                choice_text = choices_for_answer.get(ans_str, '')
                if choice_text and choice_text.strip():
                    choice_text_fmt = choice_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                    # 間違えた選択肢は赤色で強調
                    if not is_user_correct_flag and result_text == "❌ 不正解":
                        return f"<b><font color='#dc2626'>[{ans_str}] {choice_text_fmt}</font></b>"
                    else:
                        return f"<b>[{ans_str}] {choice_text_fmt}</b>"
                # 選択肢が見つからない場合でも、数字だけは表示
                return f"[{ans_str}]"

            def fmt_correct(ans):
                if ans is None or ans == []:
                    return '<font color="#dc2626">正解データなし</font>'
                if isinstance(ans, list):
                    return '<br/>'.join([fmt_answer(a, is_user_correct_flag=True) for a in ans])
                return fmt_answer(ans, is_user_correct_flag=True)
            
            # あなたの回答と正解を明確に表示
            answer_style = ParagraphStyle(
                'AnswerStyle',
                fontName=japanese_font_name,
                fontSize=10,
                leading=14,
                spaceAfter=6,
                leftIndent=0,
                rightIndent=0
            )
            
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b><font color='#1e40af'>あなたの回答:</font></b> {fmt_answer(user_answer, is_user_correct_flag=is_user_correct)}", answer_style))
            story.append(Paragraph(f"<b><font color='#059669'>正解:</font></b> {fmt_correct(correct_answer)}", answer_style))
            
            # 不正解の場合、解説文を追加表示
            if not is_user_correct:
                explanation = question.get('explanation', '')
                if explanation and explanation.strip():
                    explanation_style = ParagraphStyle(
                        'ExplanationStyle',
                        fontName=japanese_font_name,
                        fontSize=10,
                        leading=14,
                        spaceAfter=6,
                        leftIndent=0,
                        rightIndent=0,
                        textColor=colors.HexColor('#059669')
                    )
                    explanation_formatted = explanation.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                    story.append(Paragraph(f"<b><font color='#059669'>解説:</font></b> {explanation_formatted}", explanation_style))
                else:
                    # 解説がない場合は、正解の選択肢の内容を解説として表示
                    correct_choice_text = fmt_correct(correct_answer)
                    if correct_choice_text and correct_choice_text != '<font color="#dc2626">正解データなし</font>':
                        explanation_style = ParagraphStyle(
                            'ExplanationStyle',
                            fontName=japanese_font_name,
                            fontSize=10,
                            leading=14,
                            spaceAfter=6,
                            leftIndent=0,
                            rightIndent=0,
                            textColor=colors.HexColor('#059669')
                        )
                        story.append(Paragraph(f"<b><font color='#059669'>解説:</font></b> 正解は {correct_choice_text} です。", explanation_style))
            
            story.append(Paragraph(f"<b>解答時間:</b> {time_spent:.1f}秒", answer_style))
            story.append(Spacer(1, 12))
            
            # 問題間の区切りを追加
            if i < len(answers):
                story.append(Paragraph("─" * 60, normal_style))
                story.append(Spacer(1, 12))
            
            # ページ区切り（10問ごと）
            if i % 10 == 0 and i < len(answers):
                story.append(PageBreak())
        
        # PDF生成
        doc.build(story)
        buffer.seek(0)
        return buffer

