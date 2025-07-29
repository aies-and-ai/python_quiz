// frontend/src/store/quiz.tsx
/**
 * クイズ状態管理
 * React Contextを使用したシンプルな状態管理
 */

import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import {
  QuizSessionResponse,
  QuestionResponse,
  ProgressResponse,
  ResultsResponse,
  StatisticsResponse
} from '../types/quiz';

// 状態の型定義
interface QuizState {
  // 現在のセッション
  currentSession: QuizSessionResponse | null;
  currentQuestion: QuestionResponse | null;
  progress: ProgressResponse | null;
  
  // 結果・統計
  lastResults: ResultsResponse | null;
  statistics: StatisticsResponse | null;
  
  // UI状態
  loading: boolean;
  error: string | null;
  
  // 設定
  settings: {
    soundEnabled: boolean;
    animationsEnabled: boolean;
  };
}

// アクションの型定義
type QuizAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CURRENT_SESSION'; payload: QuizSessionResponse | null }
  | { type: 'SET_CURRENT_QUESTION'; payload: QuestionResponse | null }
  | { type: 'SET_PROGRESS'; payload: ProgressResponse | null }
  | { type: 'SET_LAST_RESULTS'; payload: ResultsResponse | null }
  | { type: 'SET_STATISTICS'; payload: StatisticsResponse | null }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<QuizState['settings']> }
  | { type: 'RESET_SESSION' }
  | { type: 'CLEAR_ERROR' };

// 初期状態
const initialState: QuizState = {
  currentSession: null,
  currentQuestion: null,
  progress: null,
  lastResults: null,
  statistics: null,
  loading: false,
  error: null,
  settings: {
    soundEnabled: false, // オフライン環境なので音声は無効
    animationsEnabled: true
  }
};

// リデューサー
const quizReducer = (state: QuizState, action: QuizAction): QuizState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      };
      
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false
      };
      
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };
      
    case 'SET_CURRENT_SESSION':
      return {
        ...state,
        currentSession: action.payload,
        // セッションが変わったら関連データをクリア
        currentQuestion: action.payload ? state.currentQuestion : null,
        progress: action.payload ? state.progress : null,
        lastResults: action.payload ? null : state.lastResults
      };
      
    case 'SET_CURRENT_QUESTION':
      return {
        ...state,
        currentQuestion: action.payload
      };
      
    case 'SET_PROGRESS':
      return {
        ...state,
        progress: action.payload
      };
      
    case 'SET_LAST_RESULTS':
      return {
        ...state,
        lastResults: action.payload
      };
      
    case 'SET_STATISTICS':
      return {
        ...state,
        statistics: action.payload
      };
      
    case 'UPDATE_SETTINGS':
      return {
        ...state,
        settings: {
          ...state.settings,
          ...action.payload
        }
      };
      
    case 'RESET_SESSION':
      return {
        ...state,
        currentSession: null,
        currentQuestion: null,
        progress: null,
        error: null
      };
      
    default:
      return state;
  }
};

// コンテキストの型定義
interface QuizContextType {
  state: QuizState;
  
  // 基本アクション
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  
  // セッション管理
  setCurrentSession: (session: QuizSessionResponse | null) => void;
  setCurrentQuestion: (question: QuestionResponse | null) => void;
  setProgress: (progress: ProgressResponse | null) => void;
  resetSession: () => void;
  
  // 結果・統計
  setLastResults: (results: ResultsResponse | null) => void;
  setStatistics: (statistics: StatisticsResponse | null) => void;
  
  // 設定
  updateSettings: (settings: Partial<QuizState['settings']>) => void;
  
  // ヘルパー
  isSessionActive: boolean;
  isQuizCompleted: boolean;
  currentAccuracy: number;
}

// コンテキスト作成
const QuizContext = createContext<QuizContextType | undefined>(undefined);

// プロバイダーコンポーネント
interface QuizProviderProps {
  children: ReactNode;
}

export const QuizProvider: React.FC<QuizProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(quizReducer, initialState);
  
  // アクション関数
  const setLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };
  
  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };
  
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };
  
  const setCurrentSession = (session: QuizSessionResponse | null) => {
    dispatch({ type: 'SET_CURRENT_SESSION', payload: session });
  };
  
  const setCurrentQuestion = (question: QuestionResponse | null) => {
    dispatch({ type: 'SET_CURRENT_QUESTION', payload: question });
  };
  
  const setProgress = (progress: ProgressResponse | null) => {
    dispatch({ type: 'SET_PROGRESS', payload: progress });
  };
  
  const resetSession = () => {
    dispatch({ type: 'RESET_SESSION' });
  };
  
  const setLastResults = (results: ResultsResponse | null) => {
    dispatch({ type: 'SET_LAST_RESULTS', payload: results });
  };
  
  const setStatistics = (statistics: StatisticsResponse | null) => {
    dispatch({ type: 'SET_STATISTICS', payload: statistics });
  };
  
  const updateSettings = (settings: Partial<QuizState['settings']>) => {
    dispatch({ type: 'UPDATE_SETTINGS', payload: settings });
  };
  
  // 計算されたプロパティ
  const isSessionActive = state.currentSession !== null && !state.currentSession.is_completed;
  const isQuizCompleted = state.currentSession?.is_completed || false;
  const currentAccuracy = state.progress?.accuracy || 0;
  
  const contextValue: QuizContextType = {
    state,
    
    // 基本アクション
    setLoading,
    setError,
    clearError,
    
    // セッション管理
    setCurrentSession,
    setCurrentQuestion,
    setProgress,
    resetSession,
    
    // 結果・統計
    setLastResults,
    setStatistics,
    
    // 設定
    updateSettings,
    
    // ヘルパー
    isSessionActive,
    isQuizCompleted,
    currentAccuracy
  };
  
  return (
    <QuizContext.Provider value={contextValue}>
      {children}
    </QuizContext.Provider>
  );
};

// カスタムフック
export const useQuiz = (): QuizContextType => {
  const context = useContext(QuizContext);
  if (context === undefined) {
    throw new Error('useQuiz must be used within a QuizProvider');
  }
  return context;
};

// セレクター関数（特定の状態にアクセスするためのヘルパー）
export const useQuizSession = () => {
  const { state } = useQuiz();
  return state.currentSession;
};

export const useCurrentQuestion = () => {
  const { state } = useQuiz();
  return state.currentQuestion;
};

export const useQuizProgress = () => {
  const { state } = useQuiz();
  return state.progress;
};

export const useQuizError = () => {
  const { state, setError, clearError } = useQuiz();
  return {
    error: state.error,
    setError,
    clearError
  };
};

export const useQuizLoading = () => {
  const { state, setLoading } = useQuiz();
  return {
    loading: state.loading,
    setLoading
  };
};

export const useQuizStatistics = () => {
  const { state } = useQuiz();
  return state.statistics;
};

export const useLastResults = () => {
  const { state } = useQuiz();
  return state.lastResults;
};

export const useQuizSettings = () => {
  const { state, updateSettings } = useQuiz();
  return {
    settings: state.settings,
    updateSettings
  };
};

// 複合セレクター（複数の状態を組み合わせた便利な関数）
export const useQuizStatus = () => {
  const { state, isSessionActive, isQuizCompleted } = useQuiz();
  
  return {
    hasActiveSession: isSessionActive,
    isCompleted: isQuizCompleted,
    hasError: state.error !== null,
    isLoading: state.loading,
    sessionId: state.currentSession?.session_id,
    questionCount: state.currentSession?.total_questions,
    currentScore: state.progress?.score,
    accuracy: state.progress?.accuracy
  };
};

// デバッグ用（開発環境でのみ使用）
export const useQuizDebug = () => {
  const { state } = useQuiz();
  
  if (process.env.NODE_ENV === 'development') {
    return {
      state,
      sessionInfo: state.currentSession ? {
        id: state.currentSession.session_id,
        totalQuestions: state.currentSession.total_questions,
        currentIndex: state.currentSession.current_index,
        isCompleted: state.currentSession.is_completed
      } : null,
      questionInfo: state.currentQuestion ? {
        id: state.currentQuestion.id,
        category: state.currentQuestion.category,
        difficulty: state.currentQuestion.difficulty
      } : null,
      progressInfo: state.progress ? {
        score: state.progress.score,
        accuracy: state.progress.accuracy,
        percentage: state.progress.progress_percentage
      } : null
    };
  }
  
  return null;
};

export default QuizProvider;