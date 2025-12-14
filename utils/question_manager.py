"""
問題データの管理とフィルタリング
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional


class QuestionManager:
    def __init__(self, questions_path: Path):
        """
        問題マネージャーの初期化
        
        Args:
            questions_path: questions.jsonファイルのパス
        """
        with open(questions_path, 'r', encoding='utf-8') as f:
            self.questions = json.load(f)
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """全問題を取得"""
        return self.questions
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """IDで問題を取得"""
        for q in self.questions:
            if q['id'] == question_id:
                return q
        return None
    
    def filter_questions(
        self,
        exam_numbers: Optional[List[int]] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        問題をフィルタリング
        
        Args:
            exam_numbers: 試験回数のリスト（Noneの場合は全回）
            categories: ジャンルのリスト（Noneの場合は全ジャンル）
            
        Returns:
            フィルタリングされた問題のリスト
        """
        filtered = self.questions
        
        # 試験回数でフィルタ
        if exam_numbers:
            filtered = [q for q in filtered if q['exam_number'] in exam_numbers]
        
        # ジャンルでフィルタ
        if categories:
            filtered = [q for q in filtered if q['category'] in categories]
        
        return filtered
    
    def get_categories(self) -> Dict[str, int]:
        """
        全ジャンルと問題数を取得
        
        Returns:
            ジャンル名をキー、問題数を値とする辞書
        """
        categories = {}
        for q in self.questions:
            cat = q['category']
            categories[cat] = categories.get(cat, 0) + 1
        return categories
    
    def get_exam_numbers(self) -> List[int]:
        """全試験回数のリストを取得"""
        exam_numbers = set()
        for q in self.questions:
            exam_numbers.add(q['exam_number'])
        return sorted(list(exam_numbers))
    
    def filter_and_sample_questions(
        self,
        exam_numbers: Optional[List[int]] = None,
        categories: Optional[List[str]] = None,
        max_questions: Optional[int] = None,
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        問題をフィルタリングし、必要に応じてランダムサンプリング
        
        Args:
            exam_numbers: 試験回数のリスト（Noneの場合は全回）
            categories: ジャンルのリスト（Noneの場合は全ジャンル）
            max_questions: 最大問題数（Noneの場合は制限なし）
            seed: ランダムシード（再現性のため、Noneの場合はランダム）
            
        Returns:
            フィルタリング・サンプリングされた問題のリスト
        """
        # フィルタリング
        filtered = self.filter_questions(
            exam_numbers=exam_numbers,
            categories=categories
        )
        
        # 問題数制限がない、または問題数が少ない場合はそのまま返す
        if max_questions is None or max_questions <= 0:
            return filtered
        
        if len(filtered) <= max_questions:
            return filtered
        
        # ランダムサンプリング
        if seed is not None:
            random.seed(seed)
        
        sampled = random.sample(filtered, max_questions)
        
        return sampled

