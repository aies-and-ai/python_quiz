// frontend/src/pages/QuizPage.tsx
/**
 * クイズページ - 実際のクイズ実行画面
 * 問題表示、回答、進行状況管理
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCurrentQuestion, submitAnswer, getSessionProgress } from '../services/api';
import { useQuiz } from '../store/quiz';
import { Question, AnswerResponse, ProgressResponse } from '../types/quiz';

const QuizPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { setError, clearError } = useQuiz();

  // 状態管理
  const [question, setQuestion] = useState<Question | null>(null);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [lastAnswer, setLastAnswer] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadCurrentQuestion();
      loadProgress();
    }
  }, [sessionId]);

  const loadCurrentQuestion = async () => {
    try {
      setLoading(true);
      clearError();
      
      const response = await getCurrentQuestion(sessionId!);
      setQuestion(response.data);
      setSelectedOption(null);
      setShowResult(false);
      
    } catch (error: any) {
      console.error('問題取得エラー:', error);
      
      if (error.response?.status === 409) {
        // クイズ完了
        navigate('/history');
      } else {
        setError('問題の取得に失敗しました');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadProgress = async () => {
    try {
      const response = await getSessionProgress(sessionId!);
      setProgress(response.data);
    } catch (error) {
      console.error('進行状況取得エラー:', error);
    }
  };

  const handleAnswerSelect = (optionIndex: number) => {
    if (!showResult) {
      setSelectedOption(optionIndex);
    }
  };

  const handleSubmitAnswer = async () => {
    if (selectedOption === null || !sessionId) return;

    try {
      setSubmitting(true);
      clearError();

      const response = await submitAnswer(sessionId, {
        session_id: sessionId,
        selected_option: selectedOption
      });

      setLastAnswer(response.data);
      setShowResult(true);

      // 進行状況を更新
      await loadProgress();

    } catch (error) {
      console.error('回答送信エラー:', error);
      setError('回答の送信に失敗しました');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (lastAnswer?.is_session_completed) {
      navigate('/history');
    } else {
      loadCurrentQuestion();
    }
  };

  const getOptionClass = (optionIndex: number) => {
    const baseClass = "w-full p-4 text-left border rounded-lg transition-all duration-200 ";
    
    if (!showResult) {
      // 回答前
      if (selectedOption === optionIndex) {
        return baseClass + "border-blue-500 bg-blue-50 text-blue-800";
      }
      return baseClass + "border-gray-300 hover:border-blue-300 hover:bg-blue-50";
    } else {
      // 回答後
      if (optionIndex === lastAnswer?.correct_answer) {
        return baseClass + "border-green-500 bg-green-100 text-green-800";
      }
      if (optionIndex === selectedOption && !lastAnswer?.is_correct) {
        return baseClass + "border-red-500 bg-red-100 text-red-800";
      }
      return baseClass + "border-gray-300 bg-gray-50 text-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">問題を読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!question || !progress) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 text-lg">問題の読み込みに失敗しました</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          ホームに戻る
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* 進行状況 */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-800">
            問題 {progress.current_index + 1} / {progress.total_questions}
          </h2>
          <div className="text-right">
            <div className="text-lg font-bold text-blue-600">
              スコア: {progress.score}
            </div>
            <div className="text-sm text-gray-600">
              正答率: {progress.accuracy.toFixed(1)}%
            </div>
          </div>
        </div>
        
        {/* プログレスバー */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress.progress_percentage}%` }}
          ></div>
        </div>
        <div className="text-sm text-gray-600 mt-2">
          あと {progress.remaining_questions} 問
        </div>
      </div>

      {/* 問題表示 */}
      <div className="bg-white rounded-lg shadow-md p-8">
        {/* カテゴリ・難易度 */}
        <div className="flex gap-2 mb-4">
          {question.category && (
            <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
              {question.category}
            </span>
          )}
          {question.difficulty && (
            <span className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
              {question.difficulty}
            </span>
          )}
        </div>

        {/* 問題文 */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold text-gray-800 leading-relaxed">
            {question.text}
          </h3>
        </div>

        {/* 選択肢 */}
        <div className="space-y-3 mb-8">
          {question.options.map((option, index) => (
            <button
              key={index}
              onClick={() => handleAnswerSelect(index)}
              disabled={showResult}
              className={getOptionClass(index)}
            >
              <div className="flex items-center">
                <span className="w-8 h-8 rounded-full bg-white border-2 border-current flex items-center justify-center mr-4 font-semibold">
                  {index + 1}
                </span>
                <span className="flex-1">{option}</span>
                {showResult && index === lastAnswer?.correct_answer && (
                  <span className="text-green-600 ml-2">✓</span>
                )}
                {showResult && index === selectedOption && !lastAnswer?.is_correct && (
                  <span className="text-red-600 ml-2">✗</span>
                )}
              </div>
            </button>
          ))}
        </div>

        {/* 結果表示 */}
        {showResult && lastAnswer && (
          <div className={`p-4 rounded-lg mb-6 ${
            lastAnswer.is_correct ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center mb-2">
              <span className={`text-lg font-bold ${
                lastAnswer.is_correct ? 'text-green-600' : 'text-red-600'
              }`}>
                {lastAnswer.is_correct ? '🎉 正解！' : '😔 不正解'}
              </span>
            </div>
            
            {!lastAnswer.is_correct && (
              <p className="text-gray-700 mb-2">
                正解は <strong>{question.options[lastAnswer.correct_answer]}</strong> でした。
              </p>
            )}
            
            {lastAnswer.explanation && (
              <div className="text-gray-700">
                <strong>解説:</strong> {lastAnswer.explanation}
              </div>
            )}
          </div>
        )}

        {/* アクションボタン */}
        <div className="text-center">
          {!showResult ? (
            <button
              onClick={handleSubmitAnswer}
              disabled={selectedOption === null || submitting}
              className={`px-8 py-3 rounded-lg font-semibold transition-all duration-200 ${
                selectedOption === null || submitting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg'
              }`}
            >
              {submitting ? (
                <span className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  送信中...
                </span>
              ) : (
                '回答を送信'
              )}
            </button>
          ) : (
            <button
              onClick={handleNextQuestion}
              className="px-8 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-all duration-200"
            >
              {lastAnswer?.is_session_completed ? (
                '🎯 結果を見る'
              ) : (
                '➡️ 次の問題'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuizPage;