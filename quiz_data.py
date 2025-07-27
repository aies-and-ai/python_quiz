# quiz_data.py
"""
クイズデータを管理するクラス
Week 4: pydanticモデルとデータバリデーション強化版
"""

import random
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from csv_reader import QuizCSVReader
from models import QuestionModel, QuizSessionModel, DataQualityReport
from enhanced_exceptions import QuizDataError, wrap_exception
from logger import get_logger


class QuizData:
    """クイズデータの管理を行うクラス（Week 4強化版）"""
    
    def __init__(self, csv_file: str, shuffle: bool = True, shuffle_options: bool = True):
        """
        初期化
        
        Args:
            csv_file (str): CSVファイルのパス
            shuffle (bool): 問題をシャッフルするかどうか
            shuffle_options (bool): 選択肢をシャッフルするかどうか
        """
        self.logger = get_logger()
        self.csv_file = csv_file
        self.csv_reader = QuizCSVReader(csv_file)
        
        # セッション管理
        self.session: Optional[QuizSessionModel] = None
        self.questions = []
        self.validated_questions: List[QuestionModel] = []
        
        # 設定
        self.shuffle = shuffle
        self.shuffle_options = shuffle_options
        
        # 状態管理（後方互換性のため維持）
        self.current_index = 0
        self.score = 0
        self.answered_questions = []
        self.wrong_questions = []
        
        # データ品質情報
        self.quality_report: Optional[DataQualityReport] = None
        
        self.logger.info(f"QuizData initialized with {csv_file}")
        self._load_questions()
    
    def _load_questions(self) -> None:
        """問題データを読み込む（強化版）"""
        try:
            self.logger.debug("Loading questions with enhanced validation")
            
            # CSVから問題を読み込み
            self.questions = self.csv_reader.load_questions()
            
            # 品質レポートを取得
            self.quality_report = self.csv_reader.get_data_quality_report()
            
            # pydanticモデルでの再バリデーション
            self._validate_and_convert_questions()
            
            # 選択肢をシャッフル
            if self.shuffle_options:
                self._shuffle_options()
            
            # 問題をシャッフル
            if self.shuffle:
                random.shuffle(self.questions)
                random.shuffle(self.validated_questions)
            
            # セッションを初期化
            self._initialize_session()
            
            self.logger.info(f"Successfully loaded {len(self.questions)} questions")
            
            # 品質レポートの表示
            if self.quality_report:
                self.logger.info(f"Data quality score: {self.quality_report.quality_score:.1f}/100")
                if not self.quality_report.is_high_quality():
                    self.logger.warning("Data quality could be improved")
            
        except Exception as e:
            self.logger.error(f"Failed to load questions: {e}")
            raise wrap_exception(e, "question_loading")
    
    def _validate_and_convert_questions(self) -> None:
        """問題データをpydanticモデルで再バリデーション"""
        self.validated_questions = []
        
        for i, question_dict in enumerate(self.questions):
            try:
                # 辞書からQuestionModelを作成
                question_model = self._dict_to_question_model(question_dict, i)
                self.validated_questions.append(question_model)
                
            except Exception as e:
                self.logger.error(f"Failed to validate question {i}: {e}")
                # バリデーションに失敗した問題は除外
                continue
    
    def _dict_to_question_model(self, question_dict: Dict[str, Any], index: int) -> QuestionModel:
        """辞書形式の問題データをQuestionModelに変換"""
        try:
            # 基本フィールドの抽出
            question = question_dict['question']
            options = question_dict['options']
            correct_answer = question_dict['correct_answer']
            explanation = question_dict.get('explanation', '')
            option_explanations = question_dict.get('option_explanations', ['', '', '', ''])
            
            # extra_dataからメタデータを抽出
            extra_data = question_dict.get('extra_data', {})
            
            return QuestionModel(
                question=question,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation if explanation else None,
                option_explanations=option_explanations,
                title=extra_data.get('title'),
                genre=extra_data.get('genre'),
                difficulty=extra_data.get('difficulty'),
                tags=extra_data.get('tags'),
                source=extra_data.get('source'),
                extra_data={k: v for k, v in extra_data.items() 
                          if k not in ['title', 'genre', 'difficulty', 'tags', 'source']}
            )
            
        except Exception as e:
            raise QuizDataError(
                message=f"Failed to convert question {index} to model: {str(e)}",
                question_number=index + 1,
                operation="model_conversion"
            )
    
    def _shuffle_options(self) -> None:
        """各問題の選択肢をランダムに並べ替える（強化版）"""
        for i, question in enumerate(self.questions):
            try:
                # 現在の正解インデックスを取得
                correct_index = question['correct_answer']
                correct_option = question['options'][correct_index]
                
                # 選択肢をシャッフル
                options_with_indices = list(enumerate(question['options']))
                random.shuffle(options_with_indices)
                
                # シャッフル後の選択肢リストと新しい正解インデックスを更新
                shuffled_options = [option for _, option in options_with_indices]
                
                # 正解選択肢の新しいインデックスを見つける
                new_correct_index = shuffled_options.index(correct_option)
                
                # 問題データを更新
                question['options'] = shuffled_options
                question['correct_answer'] = new_correct_index
                
                # 選択肢解説も同様にシャッフル
                if 'option_explanations' in question:
                    original_explanations = question['option_explanations']
                    shuffled_explanations = ['', '', '', '']
                    
                    for new_idx, (old_idx, _) in enumerate(options_with_indices):
                        if old_idx < len(original_explanations):
                            shuffled_explanations[new_idx] = original_explanations[old_idx]
                    
                    question['option_explanations'] = shuffled_explanations
                
                self.logger.debug(f"Shuffled options for question {i+1}")
                
            except Exception as e:
                self.logger.error(f"Failed to shuffle options for question {i+1}: {e}")
                # シャッフルに失敗しても継続
                continue
    
    def _initialize_session(self) -> None:
        """クイズセッションを初期化"""
        try:
            self.session = QuizSessionModel(
                session_id=str(uuid.uuid4()),
                csv_file=self.csv_file,
                total_questions=len(self.questions),
                current_index=0,
                shuffle_questions=self.shuffle,
                shuffle_options=self.shuffle_options,
                score=0,
                answered_questions=[],
                wrong_questions=[]
            )
            
            self.logger.debug(f"Initialized session {self.session.session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session: {e}")
            # セッション初期化に失敗しても従来の方式で継続
            self.session = None
    
    def reset_quiz(self) -> None:
        """クイズをリセット（強化版）"""
        try:
            self.current_index = 0
            self.score = 0
            self.answered_questions = []
            self.wrong_questions = []
            
            # セッションもリセット
            if self.session:
                self.session.current_index = 0
                self.session.score = 0
                self.session.answered_questions = []
                self.session.wrong_questions = []
            
            self.logger.info("Quiz reset completed")
            
        except Exception as e:
            self.logger.error(f"Failed to reset quiz: {e}")
            raise QuizDataError(
                message=f"Quiz reset failed: {str(e)}",
                operation="quiz_reset"
            )
    
    def get_current_question(self) -> Optional[Dict]:
        """現在の問題を取得（強化版）"""
        if not self.has_next_question():
            return None
        
        try:
            question_dict = self.questions[self.current_index]
            
            # QuestionModelからの追加情報を付与
            if self.current_index < len(self.validated_questions):
                question_model = self.validated_questions[self.current_index]
                
                # 表示用の追加情報を追加
                question_dict = question_dict.copy()
                question_dict['display_title'] = question_model.get_display_title()
                question_dict['has_explanations'] = question_model.has_explanations()
                question_dict['difficulty_level'] = question_model.get_difficulty_level()
                question_dict['tags_list'] = question_model.get_tags_list()
            
            return question_dict
            
        except Exception as e:
            self.logger.error(f"Failed to get current question: {e}")
            raise QuizDataError(
                message=f"Failed to get question {self.current_index + 1}: {str(e)}",
                question_number=self.current_index + 1,
                operation="get_question"
            )
    
    def has_next_question(self) -> bool:
        """次の問題があるかどうか"""
        return self.current_index < len(self.questions)
    
    def answer_question(self, selected_option: int) -> Dict:
        """
        問題に回答する（強化版）
        
        Args:
            selected_option (int): 選択された選択肢のインデックス（0-3）
            
        Returns:
            Dict: 回答結果の情報
        """
        if not self.has_next_question():
            raise QuizDataError(
                message="No more questions available",
                operation="answer_question"
            )
        
        try:
            current_question = self.questions[self.current_index]
            is_correct = selected_option == current_question['correct_answer']
            
            # 回答結果を記録
            answer_result = {
                'question': current_question,
                'selected_option': selected_option,
                'is_correct': is_correct,
                'correct_answer': current_question['correct_answer'],
                'timestamp': datetime.now().isoformat()
            }
            
            # QuestionModelからの追加情報
            if self.current_index < len(self.validated_questions):
                question_model = self.validated_questions[self.current_index]
                answer_result['question_model'] = question_model
                answer_result['has_explanations'] = question_model.has_explanations()
            
            self.answered_questions.append(answer_result)
            
            if is_correct:
                self.score += 1
            else:
                self.wrong_questions.append(answer_result)
            
            # セッションも更新
            if self.session:
                self.session.answered_questions.append(answer_result)
                self.session.score = self.score
                if not is_correct:
                    self.session.wrong_questions.append(answer_result)
            
            self.current_index += 1
            
            # セッションのインデックスも更新
            if self.session:
                self.session.current_index = self.current_index
            
            self.logger.debug(f"Answered question {self.current_index}: {'correct' if is_correct else 'wrong'}")
            
            return answer_result
            
        except Exception as e:
            self.logger.error(f"Failed to process answer: {e}")
            raise QuizDataError(
                message=f"Failed to process answer: {str(e)}",
                question_number=self.current_index + 1,
                operation="answer_processing"
            )
    
    def get_progress(self) -> Dict:
        """進行状況を取得（強化版）"""
        try:
            base_progress = {
                'current': self.current_index,
                'total': len(self.questions),
                'score': self.score,
                'percentage': (self.current_index / len(self.questions)) * 100 if self.questions else 0
            }
            
            # セッションモデルからの追加情報
            if self.session:
                base_progress.update({
                    'session_id': self.session.session_id,
                    'accuracy': self.session.get_accuracy(),
                    'is_completed': self.session.is_completed()
                })
            
            return base_progress
            
        except Exception as e:
            self.logger.error(f"Failed to get progress: {e}")
            # エラーが発生してもデフォルト情報を返す
            return {
                'current': self.current_index,
                'total': len(self.questions),
                'score': self.score,
                'percentage': 0
            }
    
    def get_final_results(self) -> Dict:
        """最終結果を取得（強化版）"""
        try:
            total_questions = len(self.questions)
            accuracy = (self.score / total_questions) * 100 if total_questions > 0 else 0
            
            base_results = {
                'total_questions': total_questions,
                'score': self.score,
                'accuracy': accuracy,
                'wrong_questions': self.wrong_questions,
                'answered_questions': self.answered_questions
            }
            
            # データ品質情報を追加
            if self.quality_report:
                base_results['data_quality'] = {
                    'quality_score': self.quality_report.quality_score,
                    'is_high_quality': self.quality_report.is_high_quality(),
                    'explanation_coverage': self.quality_report.get_explanation_coverage(),
                    'metadata_coverage': self.quality_report.get_metadata_coverage()
                }
            
            # セッション情報を追加
            if self.session:
                base_results['session_info'] = {
                    'session_id': self.session.session_id,
                    'started_at': None,  # 開始時刻（今後実装）
                    'completed_at': datetime.now().isoformat(),
                    'settings': {
                        'shuffle_questions': self.session.shuffle_questions,
                        'shuffle_options': self.session.shuffle_options
                    }
                }
            
            # 統計情報を追加
            base_results['statistics'] = self._generate_result_statistics()
            
            self.logger.info(f"Final results: {self.score}/{total_questions} ({accuracy:.1f}%)")
            
            return base_results
            
        except Exception as e:
            self.logger.error(f"Failed to generate final results: {e}")
            raise QuizDataError(
                message=f"Failed to generate results: {str(e)}",
                operation="final_results"
            )
    
    def _generate_result_statistics(self) -> Dict[str, Any]:
        """結果の統計情報を生成"""
        try:
            stats = {
                'total_time': None,  # 今後実装
                'average_time_per_question': None,  # 今後実装
                'difficulty_breakdown': {},
                'genre_breakdown': {},
                'correct_by_position': [0, 0, 0, 0],  # 正解した選択肢の位置別統計
                'wrong_by_position': [0, 0, 0, 0]    # 間違えた選択肢の位置別統計
            }
            
            # 難易度別・ジャンル別の統計
            for answer in self.answered_questions:
                question = answer['question']
                extra_data = question.get('extra_data', {})
                
                # 難易度別統計
                difficulty = extra_data.get('difficulty', '未設定')
                if difficulty not in stats['difficulty_breakdown']:
                    stats['difficulty_breakdown'][difficulty] = {'correct': 0, 'total': 0}
                
                stats['difficulty_breakdown'][difficulty]['total'] += 1
                if answer['is_correct']:
                    stats['difficulty_breakdown'][difficulty]['correct'] += 1
                
                # ジャンル別統計
                genre = extra_data.get('genre', '未設定')
                if genre not in stats['genre_breakdown']:
                    stats['genre_breakdown'][genre] = {'correct': 0, 'total': 0}
                
                stats['genre_breakdown'][genre]['total'] += 1
                if answer['is_correct']:
                    stats['genre_breakdown'][genre]['correct'] += 1
                
                # 選択肢位置別統計
                selected_pos = answer['selected_option']
                if answer['is_correct']:
                    stats['correct_by_position'][selected_pos] += 1
                else:
                    stats['wrong_by_position'][selected_pos] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to generate statistics: {e}")
            return {}
    
    def restart_with_wrong_questions(self) -> None:
        """間違えた問題のみでクイズを再開（強化版）"""
        if not self.wrong_questions:
            raise QuizDataError(
                message="No wrong questions available",
                operation="restart_wrong_questions"
            )
        
        try:
            # 間違えた問題のみを抽出
            self.questions = [q['question'] for q in self.wrong_questions]
            
            # validated_questionsも更新
            wrong_indices = []
            for wrong in self.wrong_questions:
                # 元のインデックスを見つける（近似）
                original_question = wrong['question']
                for i, validated_q in enumerate(self.validated_questions):
                    if validated_q.question == original_question['question']:
                        wrong_indices.append(i)
                        break
            
            self.validated_questions = [self.validated_questions[i] for i in wrong_indices 
                                     if i < len(self.validated_questions)]
            
            # 選択肢を再シャッフル（設定されている場合）
            if self.shuffle_options:
                self._shuffle_options()
            
            # 問題をシャッフル（設定されている場合）
            if self.shuffle:
                combined = list(zip(self.questions, self.validated_questions))
                random.shuffle(combined)
                self.questions, self.validated_questions = zip(*combined) if combined else ([], [])
                self.questions = list(self.questions)
                self.validated_questions = list(self.validated_questions)
            
            self.reset_quiz()
            
            self.logger.info(f"Restarted with {len(self.questions)} wrong questions")
            
        except Exception as e:
            self.logger.error(f"Failed to restart with wrong questions: {e}")
            raise QuizDataError(
                message=f"Failed to restart with wrong questions: {str(e)}",
                operation="restart_wrong_questions"
            )
    
    def get_question_by_index(self, index: int) -> Optional[Dict]:
        """指定されたインデックスの問題を取得"""
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None
    
    def get_total_questions(self) -> int:
        """総問題数を取得"""
        return len(self.questions)
    
    def is_quiz_completed(self) -> bool:
        """クイズが完了したかどうか"""
        return self.current_index >= len(self.questions)
    
    def get_data_quality_summary(self) -> str:
        """データ品質のサマリーを取得"""
        if not self.quality_report:
            return "品質レポートがありません"
        
        return self.csv_reader.get_quality_summary()
    
    def export_session_data(self, output_path: str) -> None:
        """セッションデータをファイルに出力"""
        try:
            import json
            
            if not self.session:
                self.logger.warning("No session data to export")
                return
            
            session_data = {
                'session': self.session.model_dump(),
                'final_results': self.get_final_results() if self.is_quiz_completed() else None,
                'quality_report': self.quality_report.model_dump() if self.quality_report else None
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Session data exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export session data: {e}")