// frontend/src/types/quiz.ts
/**
 * クイズアプリケーションの型定義
 * バックエンドAPIとの型整合性を保つ
 */

// 基本的な共通型
export interface BaseResponse {
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ErrorResponse extends BaseResponse {
  success: false;
  error_code?: string;
  error_details?: Record<string, any>;
}

export interface SuccessResponse<T> extends BaseResponse {
  success: true;
  data: T;
}

// 問題関連の型
export interface Question {
  id: number;
  text: string;
  options: [string, string, string, string]; // 4つの選択肢
  category?: string;
  difficulty?: string;
}

export interface QuestionResponse extends Question {}

export interface QuestionListResponse {
  questions: QuestionResponse[];
  total_count: number;
  categories: string[];
  difficulties: string[];
}

// セッション関連の型
export interface QuizSessionRequest {
  question_count: number;
  category?: string;
  difficulty?: string;
  shuffle: boolean;
}

export interface QuizSessionResponse {
  session_id: string;
  total_questions: number;
  current_index: number;
  score: number;
  accuracy: number;
  progress_percentage: number;
  is_completed: boolean;
}

export interface ProgressResponse {
  session_id: string;
  current_index: number;
  total_questions: number;
  score: number;
  accuracy: number;
  progress_percentage: number;
  is_completed: boolean;
  remaining_questions: number;
}

// 回答関連の型
export interface AnswerRequest {
  session_id: string;
  selected_option: number; // 0-3
}

export interface AnswerResponse {
  session_id: string;
  question_id: number;
  selected_option: number;
  correct_answer: number;
  is_correct: boolean;
  explanation?: string;
  current_score: number;
  current_accuracy: number;
  is_session_completed: boolean;
}

// 結果関連の型
export interface WrongQuestionDetail {
  question: QuestionResponse;
  selected_option: number;
  correct_answer: number;
  answered_at: string;
}

export interface ResultsResponse {
  session_id: string;
  total_questions: number;
  score: number;
  accuracy: number;
  wrong_count: number;
  wrong_questions: WrongQuestionDetail[];
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

// 統計関連の型
export interface CategoryStats {
  total: number;
  correct: number;
  accuracy: number;
}

export interface StatisticsResponse {
  total_sessions: number;
  total_questions_answered: number;
  total_correct_answers: number;
  overall_accuracy: number;
  best_score: number;
  best_accuracy: number;
  category_stats?: Record<string, CategoryStats>;
  difficulty_stats?: Record<string, CategoryStats>;
}

// UI状態の型
export interface QuizSettings {
  questionCount: number;
  category: string;
  difficulty: string;
  shuffle: boolean;
}

export interface AppSettings {
  soundEnabled: boolean;
  animationsEnabled: boolean;
  theme?: 'light' | 'dark';
  language?: 'ja' | 'en';
}

// ヘルスチェック関連の型
export interface HealthResponse {
  status: string;
  version: string;
  database_status: string;
  timestamp: string;
}

export interface ServerStatus {
  isConnected: boolean;
  isReady: boolean;
  questionCount: number;
  message?: string;
}

// エラー関連の型
export interface ApiError {
  error_code: string;
  message: string;
  technical_message?: string;
  field?: string;
  value?: any;
}

export interface ValidationError {
  field: string;
  message: string;
  value: any;
}

// ルーティング関連の型
export type PageType = 'home' | 'quiz' | 'history' | 'results';

export interface NavigationState {
  currentPage: PageType;
  sessionId?: string;
  showResults?: boolean;
}

// フォーム関連の型
export interface QuizStartForm {
  questionCount: number;
  category: string;
  difficulty: string;
  shuffle: boolean;
}

export interface FormValidation {
  isValid: boolean;
  errors: Record<string, string>;
}

// パフォーマンス関連の型
export interface PerformanceMetrics {
  averageResponseTime: number;
  correctAnswerRate: number;
  categoryPerformance: Record<string, number>;
  difficultyPerformance: Record<string, number>;
  timeSpentPerQuestion: number[];
}

// API関連のユーティリティ型
export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
  loading: boolean;
  success: boolean;
}

export interface ApiRequestConfig {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

// イベント関連の型
export interface QuizEvent {
  type: 'session_start' | 'question_view' | 'answer_submit' | 'session_complete';
  timestamp: string;
  sessionId: string;
  data?: Record<string, any>;
}

// ローカルストレージ関連の型
export interface LocalStorageData {
  settings: AppSettings;
  recentSessions: string[];
  preferences: {
    defaultQuestionCount: number;
    favoriteCategory?: string;
    preferredDifficulty?: string;
  };
}

// コンポーネントProps関連の型
export interface QuestionCardProps {
  question: Question;
  selectedOption?: number;
  showResult?: boolean;
  correctAnswer?: number;
  onOptionSelect?: (optionIndex: number) => void;
  disabled?: boolean;
}

export interface ProgressBarProps {
  current: number;
  total: number;
  score?: number;
  accuracy?: number;
  showDetails?: boolean;
}

export interface StatisticsCardProps {
  statistics: StatisticsResponse;
  compact?: boolean;
  showDetails?: boolean;
}

export interface ResultsCardProps {
  results: ResultsResponse;
  showWrongQuestions?: boolean;
  onRetry?: () => void;
}

// フック関連の型
export interface UseApiHook<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  execute: (...args: any[]) => Promise<void>;
  reset: () => void;
}

export interface UseQuizSessionHook {
  session: QuizSessionResponse | null;
  progress: ProgressResponse | null;
  currentQuestion: Question | null;
  createSession: (request: QuizSessionRequest) => Promise<void>;
  submitAnswer: (optionIndex: number) => Promise<AnswerResponse>;
  loadCurrentQuestion: () => Promise<void>;
  resetSession: () => void;
  loading: boolean;
  error: string | null;
}

// 定数・列挙型
export enum QuizStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  ABANDONED = 'abandoned'
}

export enum DifficultyLevel {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard'
}

export enum ApiErrorCode {
  SESSION_NOT_FOUND = 'SESSION_NOT_FOUND',
  QUESTION_NOT_FOUND = 'QUESTION_NOT_FOUND',
  INVALID_ANSWER = 'INVALID_ANSWER',
  SESSION_COMPLETED = 'SESSION_COMPLETED',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  INTERNAL_ERROR = 'INTERNAL_ERROR'
}

// タイプガード関数の型
export type TypeGuard<T> = (value: any) => value is T;

// ユーティリティ型
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Partial<T> = { [P in keyof T]?: T[P] };
export type Required<T> = { [P in keyof T]-?: T[P] };

// 関数型
export type EventHandler<T = void> = () => T;
export type EventHandlerWithPayload<P, T = void> = (payload: P) => T;
export type AsyncEventHandler<T = void> = () => Promise<T>;
export type AsyncEventHandlerWithPayload<P, T = void> = (payload: P) => Promise<T>;

// デフォルト値の型
export interface DefaultValues {
  QUESTION_COUNT: number;
  TIMEOUT: number;
  MAX_RETRIES: number;
  ANIMATION_DURATION: number;
}

// 設定可能な値の型
export interface ConfigurableValues {
  MIN_QUESTION_COUNT: number;
  MAX_QUESTION_COUNT: number;
  SUPPORTED_DIFFICULTIES: string[];
  SUPPORTED_LANGUAGES: string[];
}

export default {};