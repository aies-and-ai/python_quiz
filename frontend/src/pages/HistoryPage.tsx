// frontend/src/pages/HistoryPage.tsx
/**
 * 履歴・統計ページ
 * クイズの成績履歴と統計情報を表示
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getStatistics, getSessionResults } from '../services/api';
import { useQuiz } from '../store/quiz';
import { StatisticsResponse, ResultsResponse } from '../types/quiz';

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { setError, clearError } = useQuiz();

  // 状態管理
  const [statistics, setStatistics] = useState<StatisticsResponse | null>(null);
  const [sessionResults, setSessionResults] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [showResults, setShowResults] = useState(false);

  // URLパラメータから結果表示を判定
  const sessionId = searchParams.get('session');

  useEffect(() => {
    loadData();
  }, [sessionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      clearError();

      // 統計情報を読み込み
      const statsResponse = await getStatistics();
      setStatistics(statsResponse.data);

      // セッション結果を読み込み（URLパラメータがある場合）
      if (sessionId) {
        try {
          const resultsResponse = await getSessionResults(sessionId);
          setSessionResults(resultsResponse.data);
          setShowResults(true);
        } catch (error) {
          console.error('セッション結果取得エラー:', error);
          setError('結果の取得に失敗しました');
        }
      }

    } catch (error) {
      console.error('データ読み込みエラー:', error);
      setError('データの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleStartNewQuiz = () => {
    navigate('/');
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreColor = (score: number, total: number) => {
    const percentage = (score / total) * 100;
    return getAccuracyColor(percentage);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">データを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* セッション結果表示 */}
      {showResults && sessionResults && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              🎯 クイズ結果
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className={`text-4xl font-bold ${getScoreColor(sessionResults.score, sessionResults.total_questions)}`}>
                  {sessionResults.score}/{sessionResults.total_questions}
                </div>
                <div className="text-gray-600">スコア</div>
              </div>
              <div className="text-center">
                <div className={`text-4xl font-bold ${getAccuracyColor(sessionResults.accuracy)}`}>
                  {sessionResults.accuracy.toFixed(1)}%
                </div>
                <div className="text-gray-600">正答率</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-600">
                  {sessionResults.duration_seconds ? 
                    Math.round(sessionResults.duration_seconds / 60) : '-'}
                </div>
                <div className="text-gray-600">所要時間(分)</div>
              </div>
            </div>
          </div>

          {/* 間違えた問題 */}
          {sessionResults.wrong_questions.length > 0 && (
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">
                📝 間違えた問題 ({sessionResults.wrong_questions.length}問)
              </h3>
              <div className="space-y-4">
                {sessionResults.wrong_questions.map((wrong, index) => (
                  <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                    <div className="mb-2">
                      <strong className="text-gray-800">{wrong.question.text}</strong>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-red-600 font-medium">あなたの回答:</span>
                        <br />
                        {wrong.question.options[wrong.selected_option]}
                      </div>
                      <div>
                        <span className="text-green-600 font-medium">正解:</span>
                        <br />
                        {wrong.question.options[wrong.correct_answer]}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="text-center">
            <button
              onClick={handleStartNewQuiz}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-all duration-200"
            >
              🚀 新しいクイズを始める
            </button>
          </div>
        </div>
      )}

      {/* 統計情報 */}
      {statistics && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">
            📊 統計情報
          </h2>

          {statistics.total_sessions === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 text-lg mb-4">
                まだクイズを実行していません
              </p>
              <button
                onClick={handleStartNewQuiz}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-all duration-200"
              >
                🎯 最初のクイズを始める
              </button>
            </div>
          ) : (
            <>
              {/* 全体統計 */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {statistics.total_sessions}
                  </div>
                  <div className="text-gray-600">総クイズ数</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-3xl font-bold text-green-600">
                    {statistics.total_questions_answered}
                  </div>
                  <div className="text-gray-600">総問題数</div>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className={`text-3xl font-bold ${getAccuracyColor(statistics.overall_accuracy)}`}>
                    {statistics.overall_accuracy.toFixed(1)}%
                  </div>
                  <div className="text-gray-600">全体正答率</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600">
                    {statistics.best_score}
                  </div>
                  <div className="text-gray-600">最高スコア</div>
                </div>
              </div>

              {/* ベスト記録 */}
              <div className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  🏆 ベスト記録
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex justify-between">
                    <span className="text-gray-700">最高正答率:</span>
                    <span className={`font-bold ${getAccuracyColor(statistics.best_accuracy)}`}>
                      {statistics.best_accuracy.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-700">最高スコア:</span>
                    <span className="font-bold text-purple-600">
                      {statistics.best_score}問正解
                    </span>
                  </div>
                </div>
              </div>

              {/* パフォーマンス分析 */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  📈 パフォーマンス分析
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>平均正解数</span>
                      <span className="font-medium">
                        {(statistics.total_correct_answers / statistics.total_sessions).toFixed(1)}問
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{
                          width: `${Math.min((statistics.total_correct_answers / statistics.total_sessions) * 10, 100)}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>全体正答率</span>
                      <span className="font-medium">{statistics.overall_accuracy.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          statistics.overall_accuracy >= 80 ? 'bg-green-500' :
                          statistics.overall_accuracy >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${statistics.overall_accuracy}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* アクションボタン */}
      {!showResults && (
        <div className="text-center">
          <button
            onClick={handleStartNewQuiz}
            className="px-8 py-4 bg-blue-600 text-white rounded-lg font-semibold text-lg hover:bg-blue-700 transition-all duration-200 hover:shadow-lg transform hover:-translate-y-1"
          >
            🎯 新しいクイズを始める
          </button>
        </div>
      )}
    </div>
  );
};

export default HistoryPage;