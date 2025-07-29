// frontend/src/App.tsx
/**
 * クイズアプリケーション メインコンポーネント
 * シンプルなSPA構成でローカル動作に最適化
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import QuizPage from './pages/QuizPage';
import HistoryPage from './pages/HistoryPage';
import { QuizProvider } from './store/quiz';
import './App.css';

const App: React.FC = () => {
  return (
    <QuizProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          {/* ヘッダー */}
          <header className="bg-blue-600 text-white shadow-md">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">
                  <a href="/" className="hover:text-blue-200 transition-colors">
                    🧠 クイズアプリ
                  </a>
                </h1>
                
                <nav className="space-x-6">
                  <a
                    href="/"
                    className="hover:text-blue-200 transition-colors font-medium"
                  >
                    ホーム
                  </a>
                  <a
                    href="/history"
                    className="hover:text-blue-200 transition-colors font-medium"
                  >
                    履歴・統計
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* メインコンテンツ */}
          <main className="container mx-auto px-4 py-8">
            <Routes>
              {/* ホームページ */}
              <Route path="/" element={<HomePage />} />
              
              {/* クイズページ */}
              <Route path="/quiz/:sessionId" element={<QuizPage />} />
              
              {/* 履歴・統計ページ */}
              <Route path="/history" element={<HistoryPage />} />
              
              {/* デフォルトリダイレクト */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          {/* フッター */}
          <footer className="bg-gray-800 text-white py-6 mt-12">
            <div className="container mx-auto px-4 text-center">
              <p className="text-sm text-gray-400">
                ローカル検証用クイズアプリケーション v1.0.0
              </p>
              <p className="text-xs text-gray-500 mt-2">
                問題管理: <code>python admin.py</code> | 
                API文書: <a href="/api/v1/docs" className="text-blue-400 hover:text-blue-300">
                  /api/v1/docs
                </a>
              </p>
            </div>
          </footer>
        </div>
      </Router>
    </QuizProvider>
  );
};

export default App;