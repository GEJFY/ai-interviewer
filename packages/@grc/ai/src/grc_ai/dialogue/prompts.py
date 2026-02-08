"""Prompt templates for interview dialogue."""

from dataclasses import dataclass
from typing import Any


@dataclass
class PromptTemplate:
    """A prompt template with placeholders."""

    template: str
    required_vars: list[str]

    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables."""
        missing = set(self.required_vars) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        return self.template.format(**kwargs)


class PromptManager:
    """Manages prompt templates for different interview scenarios."""

    # System prompts
    INTERVIEW_SYSTEM = PromptTemplate(
        template="""あなたは{organization_name}のGRCアドバイザリー業務を支援するAIインタビュアーです。

## 役割
{use_case_description}

## インタビュー目的
{interview_purpose}

## ガイドライン
1. 丁寧で専門的な言葉遣いを心がけてください
2. 被インタビュー者の回答を傾聴し、必要に応じて深掘り質問を行ってください
3. 曖昧な回答には具体例を求めてください
4. 機密情報の取り扱いには十分注意してください
5. 回答者が答えにくそうな場合は、別の角度から質問してください

## 質問リスト
{questions}

## 注意事項
- 質問は自然な会話の流れで行ってください
- すべての質問を機械的に聞くのではなく、状況に応じて柔軟に対応してください
- 重要な発見があれば、フォローアップ質問で深掘りしてください
""",
        required_vars=[
            "organization_name",
            "use_case_description",
            "interview_purpose",
            "questions",
        ],
    )

    ANONYMOUS_INTERVIEW_SYSTEM = PromptTemplate(
        template="""あなたは{organization_name}の匿名調査を実施するAIインタビュアーです。

## 重要事項
このインタビューは完全匿名で実施されます。回答者を特定する情報は一切記録されません。

## 調査目的
{interview_purpose}

## ガイドライン
1. 回答者が安心して率直に回答できる雰囲気を作ってください
2. 個人を特定する質問は絶対にしないでください
3. 回答に対して批判的な態度を取らないでください
4. 回答者のプライバシーを最大限尊重してください

## 質問リスト
{questions}
""",
        required_vars=["organization_name", "interview_purpose", "questions"],
    )

    # Dynamic prompts
    GENERATE_FOLLOWUP = PromptTemplate(
        template="""以下の回答に対して、より深い理解を得るためのフォローアップ質問を1つ生成してください。

## 元の質問
{original_question}

## 回答
{answer}

## 文脈
{context}

質問のみを出力してください。前置きは不要です。
""",
        required_vars=["original_question", "answer", "context"],
    )

    SUMMARIZE_INTERVIEW = PromptTemplate(
        template="""以下のインタビュー記録を要約してください。

## インタビュー目的
{purpose}

## 記録
{transcript}

## 出力形式
以下の形式でJSON形式で出力してください：
{{
    "summary": "インタビューの概要（200文字以内）",
    "key_findings": ["主要な発見事項1", "主要な発見事項2", ...],
    "risks_identified": ["特定されたリスク1", "特定されたリスク2", ...],
    "follow_up_items": ["フォローアップ項目1", "フォローアップ項目2", ...],
    "sentiment": "positive/neutral/negative"
}}
""",
        required_vars=["purpose", "transcript"],
    )

    GENERATE_OPENING = PromptTemplate(
        template="""インタビューの開始挨拶を生成してください。

## インタビュアー名
{interviewer_name}

## インタビュー目的
{purpose}

## 所要時間目安
{estimated_duration}

## 匿名性
{anonymity_note}

自然で親しみやすい挨拶を生成してください。
""",
        required_vars=["interviewer_name", "purpose", "estimated_duration", "anonymity_note"],
    )

    GENERATE_CLOSING = PromptTemplate(
        template="""インタビューの終了挨拶を生成してください。

## インタビューの要点
{key_points}

## 次のステップ
{next_steps}

感謝の意を込めた自然な終了挨拶を生成してください。
""",
        required_vars=["key_points", "next_steps"],
    )

    # Use case specific prompts
    USE_CASE_DESCRIPTIONS = {
        "compliance_survey": "コンプライアンス意識調査を実施し、組織全体のコンプライアンス文化と認識レベルを評価します。",
        "whistleblower_investigation": "内部通報事案に関する事実確認を行います。公平性と機密性を最優先に対応してください。",
        "audit_process": "業務プロセスのヒアリングを行い、内部統制の整備・運用状況を確認します。",
        "risk_assessment": "事業リスクの特定と評価を行うためのヒアリングを実施します。",
        "knowledge_extraction": "業務ナレッジの抽出と形式知化を行います。経験に基づく暗黙知を引き出してください。",
    }

    @classmethod
    def get_system_prompt(
        cls,
        *,
        organization_name: str,
        use_case_type: str,
        interview_purpose: str,
        questions: list[str],
        is_anonymous: bool = False,
    ) -> str:
        """Generate a system prompt for an interview.

        Args:
            organization_name: Name of the organization
            use_case_type: Type of use case
            interview_purpose: Purpose of the interview
            questions: List of questions to ask
            is_anonymous: Whether the interview is anonymous

        Returns:
            Formatted system prompt
        """
        questions_text = "\n".join(f"- {q}" for q in questions)
        use_case_desc = cls.USE_CASE_DESCRIPTIONS.get(
            use_case_type, "GRCに関するインタビューを実施します。"
        )

        if is_anonymous:
            return cls.ANONYMOUS_INTERVIEW_SYSTEM.format(
                organization_name=organization_name,
                interview_purpose=interview_purpose,
                questions=questions_text,
            )
        else:
            return cls.INTERVIEW_SYSTEM.format(
                organization_name=organization_name,
                use_case_description=use_case_desc,
                interview_purpose=interview_purpose,
                questions=questions_text,
            )
