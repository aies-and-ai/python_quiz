# quiz.py
"""
クイズプレイ専用アプリケーション（ユーザー向け）
Phase 1: デスクトップUI削除、API準備用に簡素化

このファイルの配置場所: プロジェクトルート/quiz.py
"""

import sys
from pathlib import Path

from app.config import get_settings
from app.core.service_factory import initialize_services, shutdown_services, get_quiz_service
from utils.logger import get_logger, set_log_level


def check_quiz_readiness() -> tuple[bool, str]:
    """
    クイズ実行可能性をチェック
    
    Returns:
        tuple[bool, str]: (準備完了フラグ, メッセージ)
    """
    try:
        quiz_service = get_quiz_service()
        question_count = quiz_service.get_question_count()
        
        if question_count == 0:
            return False, "問題データがありません。管理者にお問い合わせください。"
        
        return True, f"{question_count}問の問題が利用可能です。"
        
    except Exception as e:
        return False, f"システムエラー: {str(e)}"


def run_simple_cli_quiz():
    """簡易CLI版クイズ実行（Web化準備用）"""
    try:
        quiz_service = get_quiz_service()
        
        # セッション作成
        session = quiz_service.create_session(question_count=5)
        print(f"\n=== クイズ開始 ({session.total_questions}問) ===")
        
        # 問題実行
        while not session.is_completed:
            question = quiz_service.get_current_question(session.id)
            if not question:
                break
                
            # 問題表示
            progress = quiz_service.get_session_progress(session.id)
            print(f"\n問題 {progress['current_index'] + 1}/{progress['total_questions']}")
            print(f"スコア: {progress['score']}")
            print(f"\n{question.text}")
            
            # 選択肢表示
            for i, option in enumerate(question.options):
                print(f"{i+1}. {option}")
            
            # 回答入力
            try:
                answer = int(input("\n回答を選択してください (1-4): ")) - 1
                if not 0 <= answer <= 3:
                    print("1-4の範囲で入力してください")
                    continue
                    
                # 回答処理
                result = quiz_service.answer_question(session.id, answer)
                
                if result['is_correct']:
                    print("✅ 正解！")
                else:
                    print("❌ 不正解")
                    correct_option = question.options[result['correct_answer']]
                    print(f"正解: {correct_option}")
                
                if result['explanation']:
                    print(f"解説: {result['explanation']}")
                    
            except (ValueError, KeyboardInterrupt):
                print("\nクイズを中断しました")
                return
        
        # 結果表示
        if session.is_completed:
            results = quiz_service.get_session_results(session.id)
            print(f"\n=== 結果 ===")
            print(f"スコア: {results['score']}/{results['total_questions']}")
            print(f"正答率: {results['accuracy']:.1f}%")
            
    except Exception as e:
        print(f"クイズ実行エラー: {e}")


def main():
    """ユーザー向けメイン関数（簡素化版）"""
    logger = None
    
    try:
        # 設定読み込み
        settings = get_settings()
        set_log_level(settings.log_level)
        logger = get_logger()
        
        logger.info("=== クイズアプリケーション起動（簡素版） ===")
        
        # サービス初期化
        initialize_services(settings.database_url)
        
        # クイズ実行可能性チェック
        is_ready, message = check_quiz_readiness()
        print(f"\n{message}")
        
        if not is_ready:
            print("\n📋 解決方法:")
            print("   1. 管理者用アプリを起動: python admin.py")
            print("   2. CSVファイルをインポートしてください")
            return
        
        # 簡易CLI版クイズ実行
        print("\n💡 この簡易版は開発用です。Web版準備中...")
        if input("簡易版クイズを実行しますか？ (y/N): ").lower() == 'y':
            run_simple_cli_quiz()
        
    except KeyboardInterrupt:
        print("\n\nユーザーによる中断")
    except Exception as e:
        if logger:
            logger.error(f"アプリケーションエラー: {e}")
        else:
            print(f"起動エラー: {e}")
        
        print(f"\n❌ エラーが発生しました: {e}")
        print("\n📋 トラブルシューティング:")
        print("   1. admin.py を使用して問題データを確認してください")
        print("   2. データベースファイル(quiz.db)を確認してください")
    
    finally:
        try:
            if logger:
                logger.info("アプリケーション終了処理")
            shutdown_services()
        except Exception as e:
            print(f"終了処理エラー: {e}")


if __name__ == "__main__":
    main()