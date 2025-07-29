// frontend/src/pages/HomePage.tsx
/**
 * ホームページ - クイズ設定と開始
 * シンプルな設定インターフェースでクイズを開始
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession, getCategories, getDifficulties, getQuestionCount } from '../services/api';
import { useQuiz } from '../store/quiz';

interface QuizSettings {
  questionCount: number;
  category: string;
  difficulty: string;
  shuffle: boolean;
}

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { setError, clearError } = useQuiz();
  
  // 設定状態
  const [settings, setSettings] = useState<QuizSettings>({
    questionCount: 10,
    category: '',
    difficulty: '',
    shuffle: true
  });
  
  // メタデータ
  const [categories, setCategories] = useState<string[]>([]);
  const [difficulties, setDifficulties] = useState<string[]>([]);
  const [availableQuestions, setAvailableQuestions] = useState<number>(0);
  
  // UI状態
  const [loading, setLoading] = useState(false);
  const [loadingMeta, setLoadingMeta] = useState(true);

  // 初期データ読み込み
  useEffect(() => {
    loadMetadata();
  }, []);

  // 利用可能問題数の更新
  useEffect(() => {
    updateAvailableQuestions();
  }, [settings.category, settings.difficulty]);

  const loadMetadata = async () => {
    try {
      setLoadingMeta(true);
      clearError();
      
      const [categoriesData, difficultiesData] = await Promise.all([
        getCategories(),
        getDifficulties()
      ]);
      
      setCategories(categoriesData.data);
      setDifficulties(difficultiesData.data);
      
    } catch (error) {
      console.error('メタデータ読み込みエラー:', error);
      setError('設定情報の読み込みに失敗しました');
    } finally {
      setLoadingMeta(false);
    }
  };

  const updateAvailableQuestions = async () => {
    try {
      const count = await getQuestionCount(
        settings.category || undefined,
        settings.difficulty || undefined
      );
      setAvailableQuestions(count);
    } catch (error) {
      console.error('問題数取得エラー:', error);
      setAvailableQuestions(0);
    }
  };

  const handleSettingsChange = (key: keyof QuizSettings, value: string | number | boolean) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleStartQuiz = async () => {
    try {
      setLoading(true);
      clearError();

      // バリデーション
      if (availableQuestions === 0) {
        setError('問題が見つかりません。条件を変更してください。');
        return;
      }

      if (settings.questionCount > availableQuestions) {
        setError(`問題数は${availableQuestions}問以下で設定してください。`);
        return;
      }

      // セッション作成
      const response = await createSession({
        question_count: settings.questionCount,
        category: settings.category || undefined,
        difficulty: settings.difficulty || undefined,
        shuffle: settings.shuffle
      });

      // クイズページに遷移
      navigate(`/quiz/${response.data.session_id}`);

    } catch (error) {
      console.error('クイズ開始エラー:', error);
      setError('クイズの開始に失敗しました。しばらく時間をおいて再試行してください。');
    } finally {
      setLoading(false);
    }
  };

  if (loadingMeta) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">設定を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-8">
        {/* タイトル */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            🚀 クイズを始めよう！
          </h2>
          <p className="text-gray-600">
            お好みの設定でクイズをカスタマイズできます
          </p>
        </div>

        {/* 設定フォーム */}
        <div className="space-y-6">
          {/* 問題数設定 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              問題数
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="5"
                max={Math.min(availableQuestions, 50)}
                value={settings.questionCount}
                onChange={(e) => handleSettingsChange('questionCount', parseInt(e.target.value))}
                className="flex-1"
                disabled={availableQuestions === 0}
              />
              <div className="text-lg font-bold text-blue-600 w-16 text-center">
                {settings.questionCount}問
              </div>
            </div>
            <div className="text-sm text-gray-500 mt-1">
              利用可能: {availableQuestions}問
            </div>
          </div>

          {/* カテゴリ選択 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              カテゴリ
            </label>
            <select
              value={settings.category}
              onChange={(e) => handleSettingsChange('category', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">すべてのカテゴリ</option>
              {categories.map(category => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>

          {/* 難易度選択 */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              難易度
            </label>
            <select
              value={settings.difficulty}
              onChange={(e) => handleSettingsChange('difficulty', e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">すべての難易度</option>
              {difficulties.map(difficulty => (
                <option key={difficulty} value={difficulty}>
                  {difficulty}
                </option>
              ))}
            </select>
          </div>

          {/* シャッフル設定 */}
          <div>
            <label className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={settings.shuffle}
                onChange={(e) => handleSettingsChange('shuffle', e.target.checked)}
                className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                問題と選択肢をランダムに表示
              </span>
            </label>
          </div>
        </div>

        {/* 開始ボタン */}
        <div className="mt-8 text-center">
          <button
            onClick={handleStartQuiz}
            disabled={loading || availableQuestions === 0}
            className={`
              px-8 py-4 rounded-lg font-semibold text-lg transition-all duration-200
              ${loading || availableQuestions === 0
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg transform hover:-translate-y-1'
              }
            `}
          >
            {loading ? (
              <span className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                開始中...
              </span>
            ) : availableQuestions === 0 ? (
              '問題データがありません'
            ) : (
              `🎯 ${settings.questionCount}問クイズを開始！`
            )}
          </button>
          
          {availableQuestions === 0 && (
            <p className="text-sm text-red-600 mt-3">
              💡 問題を追加するには: <code>python admin.py --import your_file.csv</code>
            </p>
          )}
        </div>

        {/* 統計リンク */}
        <div className="mt-6 text-center">
          <a
            href="/history"
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            📊 過去の成績を見る
          </a>
        </div>
      </div>
    </div>
  );
};

export default HomePage;