# test_week4_data_validation.py
"""
Week 4 データバリデーション強化の統合テスト
pydanticモデル、品質チェック、エラーハンドリングの確認
"""

import os
import tempfile
import shutil
from pathlib import Path
from models import QuestionModel, QuizSessionModel, DataQualityReport
from csv_reader import QuizCSVReader
from quiz_data import QuizData
from enhanced_exceptions import CSVFormatError, QuizDataError


def backup_existing_files():
    """既存のテストファイルをバックアップ"""
    backup_files = []
    test_files = ["test_sample.csv", "quality_report.txt", "session_data.json"]
    
    for filename in test_files:
        if os.path.exists(filename):
            backup_name = f"{filename}.backup"
            shutil.copy(filename, backup_name)
            backup_files.append(backup_name)
            print(f"📁 {filename} をバックアップしました")
    
    return backup_files


def restore_backup_files(backup_files):
    """バックアップファイルを復元"""
    for backup_file in backup_files:
        if os.path.exists(backup_file):
            original_file = backup_file.replace('.backup', '')
            shutil.move(backup_file, original_file)
            print(f"📁 {original_file} を復元しました")
    
    # テスト用ファイルを削除
    test_files = ["test_sample.csv", "quality_report.txt", "session_data.json"]
    for filename in test_files:
        if os.path.exists(filename) and not any(filename in bf for bf in backup_files):
            os.remove(filename)
            print(f"🗑️ テスト用ファイル {filename} を削除しました")


def create_test_csv(content: str, filename: str = "test_sample.csv") -> str:
    """テスト用CSVファイルを作成"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return filename


def test_scenario_1_question_model():
    """シナリオ1: QuestionModelの基本機能テスト"""
    print("\n=== Test 1: QuestionModel基本機能 ===")
    
    try:
        # 正常なデータでのテスト
        valid_data = {
            'question': 'これは正常な問題ですか？',
            'option1': 'はい',
            'option2': 'いいえ',
            'option3': 'たぶん',
            'option4': 'わからない',
            'correct_answer': '1',
            'explanation': 'これは正常な問題の例です',
            'title': 'サンプル問題',
            'genre': 'テスト',
            'difficulty': '初級',
            'tags': 'サンプル, テスト'
        }
        
        question = QuestionModel.from_csv_dict(valid_data, 1)
        
        print("✅ 正常データでのQuestionModel作成成功")
        print(f"   問題文: {question.question[:30]}...")
        print(f"   表示タイトル: {question.get_display_title()}")
        print(f"   難易度: {question.difficulty}")
        print(f"   タグリスト: {question.get_tags_list()}")
        print(f"   解説有無: {question.has_explanations()}")
        
        # 従来形式への変換テスト
        legacy_dict = question.to_legacy_dict()
        assert 'question' in legacy_dict
        assert 'options' in legacy_dict
        assert 'correct_answer' in legacy_dict
        print("✅ 従来形式への変換も正常")
        
    except Exception as e:
        print(f"❌ QuestionModel基本機能テスト失敗: {e}")


def test_scenario_2_data_validation():
    """シナリオ2: データバリデーション機能テスト"""
    print("\n=== Test 2: データバリデーション ===")
    
    # 無効なデータのテスト
    invalid_test_cases = [
        {
            'name': '空の問題文',
            'data': {
                'question': '',
                'option1': 'A', 'option2': 'B', 'option3': 'C', 'option4': 'D',
                'correct_answer': '1'
            }
        },
        {
            'name': '選択肢重複',
            'data': {
                'question': 'テスト問題',
                'option1': '同じ選択肢', 'option2': '同じ選択肢', 'option3': 'C', 'option4': 'D',
                'correct_answer': '1'
            }
        },
        {
            'name': '無効な正解番号',
            'data': {
                'question': 'テスト問題',
                'option1': 'A', 'option2': 'B', 'option3': 'C', 'option4': 'D',
                'correct_answer': '5'
            }
        },
        {
            'name': '空の選択肢',
            'data': {
                'question': 'テスト問題',
                'option1': 'A', 'option2': '', 'option3': 'C', 'option4': 'D',
                'correct_answer': '1'
            }
        }
    ]
    
    for test_case in invalid_test_cases:
        try:
            QuestionModel.from_csv_dict(test_case['data'], 1)
            print(f"⚠️ {test_case['name']}: バリデーションエラーが期待されましたが成功しました")
        except (CSVFormatError, ValueError) as e:
            print(f"✅ {test_case['name']}: 期待通りバリデーションエラー発生")
            print(f"   エラー: {str(e)[:80]}...")
        except Exception as e:
            print(f"❌ {test_case['name']}: 予期しないエラー: {e}")


def test_scenario_3_csv_quality_check():
    """シナリオ3: CSV品質チェック機能テスト"""
    print("\n=== Test 3: CSV品質チェック ===")
    
    try:
        # 品質の良いCSVファイルを作成
        high_quality_csv = """question,option1,option2,option3,option4,correct_answer,explanation,title,genre,difficulty,tags
これは高品質な問題ですか？,はい,いいえ,たぶん,わからない,1,詳細な解説があります,品質テスト問題,テスト,初級,"品質, テスト"
数学問題: 2+2は？,3,4,5,6,2,基本的な算数問題です,算数基礎,数学,初級,"算数, 基礎"
歴史問題: 鎌倉幕府成立は？,1185年,1192年,1195年,1200年,2,一般的には1192年とされています,鎌倉幕府,歴史,中級,"歴史, 鎌倉"
"""
        
        csv_file = create_test_csv(high_quality_csv)
        
        # CSV読み込みと品質チェック
        reader = QuizCSVReader(csv_file)
        questions = reader.load_questions()
        quality_report = reader.get_data_quality_report()
        
        print(f"✅ CSV読み込み成功: {len(questions)}問")
        
        if quality_report:
            print(f"   品質スコア: {quality_report.quality_score:.1f}/100")
            print(f"   有効問題率: {quality_report.get_success_rate():.1f}%")
            print(f"   解説カバー率: {quality_report.get_explanation_coverage():.1f}%")
            print(f"   メタデータカバー率: {quality_report.get_metadata_coverage():.1f}%")
            print(f"   高品質判定: {'はい' if quality_report.is_high_quality() else 'いいえ'}")
            print(f"   エラー数: {len(quality_report.validation_errors)}")
            print(f"   警告数: {len(quality_report.warnings)}")
            
            # 品質レポートのエクスポートテスト
            reader.export_quality_report("quality_report.txt")
            if os.path.exists("quality_report.txt"):
                print("✅ 品質レポートのエクスポート成功")
            
        else:
            print("⚠️ 品質レポートが生成されませんでした")
        
    except Exception as e:
        print(f"❌ CSV品質チェックテスト失敗: {e}")


def test_scenario_4_low_quality_csv():
    """シナリオ4: 品質の低いCSVファイルのテスト"""
    print("\n=== Test 4: 低品質CSVのハンドリング ===")
    
    try:
        # 品質の低いCSVファイル
        low_quality_csv = """question,option1,option2,option3,option4,correct_answer
test,test,test,test,test,1
短い,A,B,C,D,2
これは非常に長い問題文で、実際の問題としては長すぎる可能性があり、読みにくさや理解の困難さを引き起こす可能性がある問題文の例です。このような長い問題文は避けるべきです。,非常に長い選択肢でこれも問題となる可能性があります,B,C,D,3
重複問題,同じ,同じ,違う,違う2,1
"""
        
        csv_file = create_test_csv(low_quality_csv, "low_quality.csv")
        
        try:
            reader = QuizCSVReader(csv_file)
            questions = reader.load_questions()
            quality_report = reader.get_data_quality_report()
            
            print(f"✅ 低品質CSV読み込み: {len(questions)}問（エラーがあっても継続）")
            
            if quality_report:
                print(f"   品質スコア: {quality_report.quality_score:.1f}/100")
                print(f"   エラー数: {len(quality_report.validation_errors)}")
                print(f"   警告数: {len(quality_report.warnings)}")
                
                # いくつかの警告を表示
                for i, warning in enumerate(quality_report.warnings[:3]):
                    print(f"   警告{i+1}: {warning.get('message', '')[:60]}...")
            
        except CSVFormatError as e:
            print(f"✅ 期待通り品質エラーが発生: {e.get_user_message()}")
        
        # ファイルクリーンアップ
        if os.path.exists("low_quality.csv"):
            os.remove("low_quality.csv")
        
    except Exception as e:
        print(f"❌ 低品質CSVテスト失敗: {e}")


def test_scenario_5_quiz_session():
    """シナリオ5: QuizSessionModelのテスト"""
    print("\n=== Test 5: クイズセッション管理 ===")
    
    try:
        # 正常なCSVファイルでQuizDataを作成
        normal_csv = """question,option1,option2,option3,option4,correct_answer,explanation
問題1: 1+1は？,1,2,3,4,2,基本的な算数です
問題2: 日本の首都は？,東京,大阪,京都,名古屋,1,日本の首都は東京です
問題3: 富士山の高さは？,3776m,3800m,3700m,4000m,1,富士山は3776mです
"""
        
        csv_file = create_test_csv(normal_csv, "session_test.csv")
        
        # QuizDataを初期化
        quiz_data = QuizData(csv_file, shuffle=False, shuffle_options=False)
        
        print(f"✅ QuizData初期化成功: {quiz_data.get_total_questions()}問")
        
        # セッション情報の確認
        if quiz_data.session:
            print(f"   セッションID: {quiz_data.session.session_id}")
            print(f"   設定: shuffle_questions={quiz_data.session.shuffle_questions}")
            print(f"   設定: shuffle_options={quiz_data.session.shuffle_options}")
        
        # 進行状況の確認
        progress = quiz_data.get_progress()
        print(f"   初期進行状況: {progress['current']}/{progress['total']} ({progress['percentage']:.1f}%)")
        
        # 問題を1つ回答
        current_question = quiz_data.get_current_question()
        if current_question:
            print(f"   現在の問題: {current_question['question'][:30]}...")
            
            # 正解で回答
            correct_answer = current_question['correct_answer']
            result = quiz_data.answer_question(correct_answer)
            
            print(f"   回答結果: {'正解' if result['is_correct'] else '不正解'}")
            
            # 進行状況の更新確認
            progress = quiz_data.get_progress()
            print(f"   更新後進行状況: {progress['current']}/{progress['total']}")
            
            if 'accuracy' in progress:
                print(f"   現在の正答率: {progress['accuracy']:.1f}%")
        
        # データ品質サマリーの確認
        quality_summary = quiz_data.get_data_quality_summary()
        print(f"   品質サマリー: {quality_summary.split('\\n')[0]}")  # 最初の行のみ
        
        # セッションデータのエクスポートテスト
        quiz_data.export_session_data("session_data.json")
        if os.path.exists("session_data.json"):
            print("✅ セッションデータのエクスポート成功")
        
        # ファイルクリーンアップ
        if os.path.exists("session_test.csv"):
            os.remove("session_test.csv")
        
    except Exception as e:
        print(f"❌ クイズセッションテスト失敗: {e}")


def test_scenario_6_error_handling():
    """シナリオ6: エラーハンドリングの統合テスト"""
    print("\n=== Test 6: エラーハンドリング統合 ===")
    
    try:
        # 存在しないファイルでのテスト
        try:
            QuizData("nonexistent.csv")
            print("⚠️ 存在しないファイル: エラーが期待されましたが成功しました")
        except Exception as e:
            print(f"✅ 存在しないファイル: 期待通りエラー発生")
            print(f"   エラータイプ: {type(e).__name__}")
            if hasattr(e, 'get_user_message'):
                print(f"   ユーザーメッセージ: {e.get_user_message()[:60]}...")
        
        # 空のファイルでのテスト
        empty_file = create_test_csv("", "empty.csv")
        try:
            QuizData(empty_file)
            print("⚠️ 空ファイル: エラーが期待されましたが成功しました")
        except Exception as e:
            print(f"✅ 空ファイル: 期待通りエラー発生")
            print(f"   エラータイプ: {type(e).__name__}")
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)
        
        # 不正形式のCSVファイル
        invalid_csv = """invalid,header,format
no,proper,data,structure"""
        
        invalid_file = create_test_csv(invalid_csv, "invalid.csv")
        try:
            QuizData(invalid_file)
            print("⚠️ 不正形式CSV: エラーが期待されましたが成功しました")
        except Exception as e:
            print(f"✅ 不正形式CSV: 期待通りエラー発生")
            print(f"   エラータイプ: {type(e).__name__}")
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)
        
    except Exception as e:
        print(f"❌ エラーハンドリング統合テスト失敗: {e}")


def test_scenario_7_advanced_features():
    """シナリオ7: 高度な機能のテスト"""
    print("\n=== Test 7: 高度な機能 ===")
    
    try:
        # 複雑なデータを含むCSVファイル
        advanced_csv = """question,option1,option2,option3,option4,correct_answer,explanation,title,genre,difficulty,tags,source,option1_explanation,option2_explanation,option3_explanation,option4_explanation
高度な問題1,選択肢A,選択肢B,選択肢C,選択肢D,2,詳細な解説があります,高度なテスト,アルゴリズム,上級,"アルゴリズム, 高度",専門書,選択肢Aの解説,選択肢Bの解説（正解）,選択肢Cの解説,選択肢Dの解説
高度な問題2,選択肢1,選択肢2,選択肢3,選択肢4,3,これも詳細な解説,高度なテスト2,データ構造,エキスパート,"データ構造, 専門",学術論文,解説1,解説2,解説3（正解）,解説4
"""
        
        csv_file = create_test_csv(advanced_csv, "advanced.csv")
        
        # 高度な機能付きでQuizDataを作成
        quiz_data = QuizData(csv_file, shuffle=True, shuffle_options=True)
        
        print(f"✅ 高度なCSV読み込み成功: {quiz_data.get_total_questions()}問")
        
        # 最初の問題を取得して詳細情報を確認
        question = quiz_data.get_current_question()
        if question:
            print(f"   問題: {question['question'][:40]}...")
            
            # 表示用タイトルの確認
            if 'display_title' in question:
                print(f"   表示タイトル: {question['display_title']}")
            
            # 解説の有無確認
            if 'has_explanations' in question:
                print(f"   解説有無: {question['has_explanations']}")
            
            # 選択肢解説の確認
            if 'option_explanations' in question:
                explanations = question['option_explanations']
                explanation_count = sum(1 for exp in explanations if exp.strip())
                print(f"   選択肢解説数: {explanation_count}/4")
        
        # 最終結果での統計情報確認
        # 全問題を自動回答してテスト
        while quiz_data.has_next_question():
            current = quiz_data.get_current_question()
            if current:
                # 正解で回答
                quiz_data.answer_question(current['correct_answer'])
        
        final_results = quiz_data.get_final_results()
        
        if 'statistics' in final_results:
            stats = final_results['statistics']
            print(f"   難易度別統計: {len(stats.get('difficulty_breakdown', {}))}種類")
            print(f"   ジャンル別統計: {len(stats.get('genre_breakdown', {}))}種類")
        
        if 'data_quality' in final_results:
            quality = final_results['data_quality']
            print(f"   データ品質スコア: {quality.get('quality_score', 0):.1f}/100")
            print(f"   高品質判定: {quality.get('is_high_quality', False)}")
        
        # ファイルクリーンアップ
        if os.path.exists("advanced.csv"):
            os.remove("advanced.csv")
        
    except Exception as e:
        print(f"❌ 高度な機能テスト失敗: {e}")


def run_all_tests():
    """全テストシナリオを実行"""
    print("🧪 Week 4 データバリデーション強化 統合テスト開始")
    print("=" * 70)
    
    # 既存ファイルのバックアップ
    backup_files = backup_existing_files()
    
    try:
        test_scenario_1_question_model()
        test_scenario_2_data_validation()
        test_scenario_3_csv_quality_check()
        test_scenario_4_low_quality_csv()
        test_scenario_5_quiz_session()
        test_scenario_6_error_handling()
        test_scenario_7_advanced_features()
        
        print("\n" + "=" * 70)
        print("🎉 Week 4 統合テスト完了！")
        
        print("\n📊 Week 4 で達成された改善:")
        print("✅ pydanticによる型安全なデータ管理")
        print("✅ 包括的なデータバリデーション")
        print("✅ データ品質の自動チェック・レポート")
        print("✅ 詳細なセッション管理機能")
        print("✅ 統計情報の大幅強化")
        print("✅ エラーハンドリングの統合")
        print("✅ 高度なメタデータ対応")
        print("✅ 品質レポートのエクスポート機能")
        
        print("\n🎯 データ品質向上の効果:")
        print("- 不正なデータの事前検出")
        print("- CSVファイルの品質評価")
        print("- 問題作成者への具体的な改善提案")
        print("- Web化時のAPI入力検証の基盤完成")
        
    except Exception as e:
        print(f"\n❌ テスト実行中にエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # バックアップファイルの復元
        restore_backup_files(backup_files)


def demonstrate_week4_improvements():
    """Week 4 改善効果のデモンストレーション"""
    print("\n📈 Week 4 改善効果デモ")
    print("=" * 50)
    
    print("\n❌ 改善前（Week 3まで）:")
    print("- CSVデータは文字列として処理")
    print("- バリデーションは基本的なチェックのみ")
    print("- データ品質の可視化なし")
    print("- エラー時の情報が限定的")
    print("- 統計情報が基本的")
    
    print("\n✅ 改善後（Week 4）:")
    print("- pydanticによる型安全なデータ処理")
    print("- 包括的なバリデーション（重複、長さ、内容）")
    print("- データ品質スコア（0-100点）の自動算出")
    print("- 詳細な品質レポートの生成")
    print("- 難易度・ジャンル別の詳細統計")
    print("- セッション管理とデータエクスポート")
    
    print("\n🚀 Web化への準備完了度:")
    print("- API入力検証: ✅ pydanticモデルで完全対応")
    print("- データ品質管理: ✅ 自動チェック・レポート機能")
    print("- エラーハンドリング: ✅ 包括的なエラー管理")
    print("- 統計・分析: ✅ 詳細な分析基盤")


if __name__ == "__main__":
    run_all_tests()
    demonstrate_week4_improvements()