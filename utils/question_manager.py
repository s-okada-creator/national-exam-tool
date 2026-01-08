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
        
        # インデックスを作成（フィルタリングを高速化）
        self._exam_number_index = {}
        self._category_index = {}
        self._id_index = {}
        
        for q in self.questions:
            exam_num = q['exam_number']
            cat = q['category']
            q_id = q['id']
            
            # 試験回数インデックス
            if exam_num not in self._exam_number_index:
                self._exam_number_index[exam_num] = []
            self._exam_number_index[exam_num].append(q)
            
            # ジャンルインデックス
            if cat not in self._category_index:
                self._category_index[cat] = []
            self._category_index[cat].append(q)
            
            # IDインデックス
            self._id_index[q_id] = q
    
    def get_all_questions(self) -> List[Dict[str, Any]]:
        """全問題を取得"""
        return self.questions
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """IDで問題を取得（インデックスを使用して高速化）"""
        return self._id_index.get(question_id)
    
    def filter_questions(
        self,
        exam_numbers: Optional[List[int]] = None,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        問題をフィルタリング（インデックスを使用して高速化）
        
        Args:
            exam_numbers: 試験回数のリスト（Noneの場合は全回）
            categories: ジャンルのリスト（Noneの場合は全ジャンル）
            
        Returns:
            フィルタリングされた問題のリスト
        """
        # インデックスを使用して高速化
        if exam_numbers and categories:
            # 両方の条件がある場合：インデックスから取得して交差を取る
            # IDを使って交差を計算（辞書はhashableでないため）
            exam_question_ids = set()
            for exam_num in exam_numbers:
                if exam_num in self._exam_number_index:
                    for q in self._exam_number_index[exam_num]:
                        exam_question_ids.add(q['id'])
            
            cat_question_ids = set()
            for cat in categories:
                if cat in self._category_index:
                    for q in self._category_index[cat]:
                        cat_question_ids.add(q['id'])
            
            # 交差を取る
            common_ids = exam_question_ids & cat_question_ids
            filtered = [self._id_index[q_id] for q_id in common_ids if q_id in self._id_index]
        elif exam_numbers:
            # 試験回数のみ
            filtered = []
            for exam_num in exam_numbers:
                if exam_num in self._exam_number_index:
                    filtered.extend(self._exam_number_index[exam_num])
        elif categories:
            # ジャンルのみ
            filtered = []
            for cat in categories:
                if cat in self._category_index:
                    filtered.extend(self._category_index[cat])
        else:
            # フィルタなし
            filtered = self.questions
        
        return filtered
    
    def get_categories(self) -> Dict[str, int]:
        """
        全ジャンルと問題数を取得（インデックスを使用して高速化）
        
        Returns:
            ジャンル名をキー、問題数を値とする辞書
        """
        categories = {}
        for cat, questions in self._category_index.items():
            categories[cat] = len(questions)
        return categories
    
    def get_exam_numbers(self) -> List[int]:
        """全試験回数のリストを取得（インデックスを使用して高速化）"""
        return sorted(list(self._exam_number_index.keys()))
    
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

