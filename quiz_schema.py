"""
クイズスキーマ定義 - 統一スキーマ版
"""

from typing import Dict, List, Any


class QuizSchema:
    """クイズの統一スキーマ定義とバリデーション"""
    
    # 統一スキーマ定義
    SCHEMA = {
        "name": "統一スキーマ",
        "description": "選択肢ごとの解説を含む標準形式",
        "required": ["question", "option1", "option2", "option3", "option4", "correct_answer"],
        "optional": ["title", "genre", "difficulty", "tags", "explanation", "source",
                    "option1_explanation", "option2_explanation", "option3_explanation", "option4_explanation"],
        "display_fields": ["title", "genre", "difficulty"],
        "field_labels": {
            "question": "問題文",
            "title": "問題タイトル", 
            "genre": "ジャンル",
            "difficulty": "難易度",
            "tags": "タグ",
            "source": "出典",
            "explanation": "全体解説",
            "option1_explanation": "選択肢1の解説",
            "option2_explanation": "選択肢2の解説",
            "option3_explanation": "選択肢3の解説",
            "option4_explanation": "選択肢4の解説"
        }
    }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """統一スキーマを取得"""
        return cls.SCHEMA
    
    @classmethod
    def validate_csv_headers(cls, headers: List[str]) -> Dict[str, Any]:
        """
        CSVヘッダーをバリデーション
        
        Args:
            headers (List[str]): CSVファイルのヘッダー
            
        Returns:
            Dict: バリデーション結果
        """
        schema = cls.get_schema()
        headers_set = set(headers)
        
        # 必須フィールドのチェック
        required_fields = set(schema["required"])
        missing_required = required_fields - headers_set
        
        # 利用可能なフィールドを特定
        all_allowed_fields = set(schema["required"] + schema["optional"])
        available_fields = headers_set.intersection(all_allowed_fields)
        
        # 未知のフィールドを特定
        unknown_fields = headers_set - all_allowed_fields
        
        # 表示対象フィールドを特定
        display_fields = []
        for field in schema.get("display_fields", []):
            if field in headers_set:
                display_fields.append(field)
        
        return {
            "schema_info": schema,
            "is_valid": len(missing_required) == 0,
            "missing_required": list(missing_required),
            "available_fields": list(available_fields),
            "unknown_fields": list(unknown_fields),
            "display_fields": display_fields,
            "warnings": cls._generate_warnings(missing_required, unknown_fields)
        }
    
    @classmethod
    def _generate_warnings(cls, missing_required: set, unknown_fields: set) -> List[str]:
        """警告メッセージを生成"""
        warnings = []
        
        if missing_required:
            warnings.append(f"必須フィールドが不足: {', '.join(missing_required)}")
        
        if unknown_fields:
            warnings.append(f"未知のフィールド: {', '.join(unknown_fields)}")
        
        return warnings
    
    @classmethod
    def get_field_label(cls, field_name: str) -> str:
        """フィールド名に対応する日本語ラベルを取得"""
        schema = cls.get_schema()
        return schema.get("field_labels", {}).get(field_name, field_name)