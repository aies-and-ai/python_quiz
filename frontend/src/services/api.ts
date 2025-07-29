// frontend/src/services/api.ts
/**
 * API通信サービス
 * バックエンドとの通信を管理
 */

import axios, { AxiosResponse } from 'axios';
import {
  QuizSessionRequest,
  QuizSessionResponse,
  QuestionResponse,
  AnswerRequest,
  AnswerResponse,
  ResultsResponse,
  StatisticsResponse,
  ProgressResponse,
  QuestionListResponse,
  SuccessResponse
} from '../types/quiz';

// API Base URL（環境に応じて設定）
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Axiosインスタンス作成
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒タイムアウト
  headers: {
    'Content-Type': 'application/json',
  },
});

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    
    // エラーメッセージの統一
    if (error.response?.data?.error?.message) {
      error.message = error.response.data.error.message;
    } else if (error.response?.data?.detail?.message) {
      error.message = error.response.data.detail.message;
    } else if (error.message === 'Network Error') {
      error.message = 'サーバーに接続できません。ネットワーク接続を確認してください。';
    } else if (error.code === 'ECONNABORTED') {
      error.message = 'リクエストがタイムアウトしました。しばらく時間をおいて再試行してください。';
    }
    
    return Promise.reject(error);
  }
);

// クイズセッション関連API

/**
 * 新しいクイズセッションを作成
 */
export const createSession = async (
  request: QuizSessionRequest
): Promise<SuccessResponse<QuizSessionResponse>> => {
  const response: AxiosResponse<SuccessResponse<QuizSessionResponse>> = await apiClient.post(
    '/sessions',
    request
  );
  return response.data;
};

/**
 * 現在の問題を取得
 */
export const getCurrentQuestion = async (
  sessionId: string
): Promise<SuccessResponse<QuestionResponse>> => {
  const response: AxiosResponse<SuccessResponse<QuestionResponse>> = await apiClient.get(
    `/sessions/${sessionId}/current`
  );
  return response.data;
};

/**
 * 問題に回答を送信
 */
export const submitAnswer = async (
  sessionId: string,
  request: AnswerRequest
): Promise<SuccessResponse<AnswerResponse>> => {
  const response: AxiosResponse<SuccessResponse<AnswerResponse>> = await apiClient.post(
    `/sessions/${sessionId}/answer`,
    request
  );
  return response.data;
};

/**
 * セッションの進行状況を取得
 */
export const getSessionProgress = async (
  sessionId: string
): Promise<SuccessResponse<ProgressResponse>> => {
  const response: AxiosResponse<SuccessResponse<ProgressResponse>> = await apiClient.get(
    `/sessions/${sessionId}/progress`
  );
  return response.data;
};

/**
 * セッション結果を取得
 */
export const getSessionResults = async (
  sessionId: string
): Promise<SuccessResponse<ResultsResponse>> => {
  const response: AxiosResponse<SuccessResponse<ResultsResponse>> = await apiClient.get(
    `/sessions/${sessionId}/results`
  );
  return response.data;
};

// 問題・メタデータ関連API

/**
 * 問題一覧を取得
 */
export const getQuestions = async (
  category?: string,
  difficulty?: string,
  limit?: number
): Promise<SuccessResponse<QuestionListResponse>> => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (difficulty) params.append('difficulty', difficulty);
  if (limit) params.append('limit', limit.toString());
  
  const response: AxiosResponse<SuccessResponse<QuestionListResponse>> = await apiClient.get(
    `/questions?${params.toString()}`
  );
  return response.data;
};

/**
 * 利用可能なカテゴリ一覧を取得
 */
export const getCategories = async (): Promise<SuccessResponse<string[]>> => {
  const response: AxiosResponse<SuccessResponse<string[]>> = await apiClient.get('/categories');
  return response.data;
};

/**
 * 利用可能な難易度一覧を取得
 */
export const getDifficulties = async (): Promise<SuccessResponse<string[]>> => {
  const response: AxiosResponse<SuccessResponse<string[]>> = await apiClient.get('/difficulties');
  return response.data;
};

/**
 * 条件に合う問題数を取得
 */
export const getQuestionCount = async (
  category?: string,
  difficulty?: string
): Promise<number> => {
  const questionsResponse = await getQuestions(category, difficulty, 1);
  return questionsResponse.data.total_count;
};

// 統計関連API

/**
 * 統計情報を取得
 */
export const getStatistics = async (): Promise<SuccessResponse<StatisticsResponse>> => {
  const response: AxiosResponse<SuccessResponse<StatisticsResponse>> = await apiClient.get(
    '/statistics'
  );
  return response.data;
};

// ヘルスチェック関連API

/**
 * 基本ヘルスチェック
 */
export const healthCheck = async (): Promise<any> => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * 詳細ヘルスチェック
 */
export const detailedHealthCheck = async (): Promise<any> => {
  const response = await apiClient.get('/health/detailed');
  return response.data;
};

/**
 * レディネスチェック
 */
export const readinessCheck = async (): Promise<any> => {
  const response = await apiClient.get('/health/ready');
  return response.data;
};

// ユーティリティ関数

/**
 * API接続テスト
 */
export const testConnection = async (): Promise<boolean> => {
  try {
    await healthCheck();
    return true;
  } catch (error) {
    console.error('API接続テスト失敗:', error);
    return false;
  }
};

/**
 * サーバー状態取得
 */
export const getServerStatus = async (): Promise<{
  isConnected: boolean;
  isReady: boolean;
  questionCount: number;
  message?: string;
}> => {
  try {
    // 基本接続確認
    const isConnected = await testConnection();
    if (!isConnected) {
      return {
        isConnected: false,
        isReady: false,
        questionCount: 0,
        message: 'サーバーに接続できません'
      };
    }

    // レディネス確認
    const readiness = await readinessCheck();
    
    return {
      isConnected: true,
      isReady: readiness.ready,
      questionCount: readiness.question_count || 0,
      message: readiness.reason || readiness.message
    };

  } catch (error) {
    console.error('サーバー状態取得エラー:', error);
    return {
      isConnected: false,
      isReady: false,
      questionCount: 0,
      message: 'サーバー状態の取得に失敗しました'
    };
  }
};

// エラーハンドリングヘルパー

/**
 * APIエラーメッセージを取得
 */
export const getErrorMessage = (error: any): string => {
  if (error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }
  if (error.response?.data?.detail?.message) {
    return error.response.data.detail.message;
  }
  if (error.message) {
    return error.message;
  }
  return '予期しないエラーが発生しました';
};

/**
 * HTTPステータスコードに基づくエラー判定
 */
export const isClientError = (error: any): boolean => {
  return error.response?.status >= 400 && error.response?.status < 500;
};

export const isServerError = (error: any): boolean => {
  return error.response?.status >= 500;
};

export const isNetworkError = (error: any): boolean => {
  return !error.response && (error.code === 'ECONNABORTED' || error.message === 'Network Error');
};

// 設定・設定値

/**
 * API設定を取得
 */
export const getApiConfig = () => ({
  baseURL: API_BASE_URL,
  timeout: apiClient.defaults.timeout,
  environment: process.env.NODE_ENV || 'development'
});

/**
 * APIクライアントインスタンスを取得（高度な使用の場合）
 */
export const getApiClient = () => apiClient;

export default {
  // セッション関連
  createSession,
  getCurrentQuestion,
  submitAnswer,
  getSessionProgress,
  getSessionResults,
  
  // 問題・メタデータ関連
  getQuestions,
  getCategories,
  getDifficulties,
  getQuestionCount,
  
  // 統計関連
  getStatistics,
  
  // ヘルスチェック関連
  healthCheck,
  detailedHealthCheck,
  readinessCheck,
  
  // ユーティリティ
  testConnection,
  getServerStatus,
  getErrorMessage,
  getApiConfig
};