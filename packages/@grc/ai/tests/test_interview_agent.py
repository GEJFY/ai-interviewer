"""インタビューエージェントのユニットテスト。

テスト対象: packages/@grc/ai/src/grc_ai/dialogue/interview_agent.py
"""

from unittest.mock import AsyncMock

import pytest

from grc_ai.base import ChatResponse
from grc_ai.dialogue.interview_agent import (
    DialogueTurn,
    InterviewAgent,
    InterviewContext,
    InterviewPhase,
)
from grc_ai.dialogue.prompts import PromptManager, PromptTemplate

# --- テストフィクスチャ ---


@pytest.fixture
def mock_provider():
    """モックAIプロバイダー。"""
    provider = AsyncMock()
    provider.chat.return_value = ChatResponse(
        content="AIの応答テスト",
        model="test-model",
        finish_reason="stop",
    )
    return provider


@pytest.fixture
def interview_context():
    """テスト用インタビューコンテキスト。"""
    return InterviewContext(
        interview_id="test-interview-001",
        organization_name="テスト株式会社",
        use_case_type="compliance_survey",
        interview_purpose="コンプライアンス意識の確認",
        questions=["現在の業務フローを教えてください", "リスクと感じる点はありますか"],
    )


@pytest.fixture
def agent(mock_provider, interview_context):
    """テスト用InterviewAgent。"""
    return InterviewAgent(provider=mock_provider, context=interview_context)


# --- InterviewContext / DialogueTurn テスト ---


class TestDataClasses:
    """データクラスのテスト。"""

    def test_interview_context_defaults(self):
        """InterviewContextのデフォルト値が正しいこと。"""
        ctx = InterviewContext(
            interview_id="id-1",
            organization_name="Org",
            use_case_type="test",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert ctx.is_anonymous is False
        assert ctx.language == "ja"
        assert ctx.metadata == {}

    def test_dialogue_turn(self):
        """DialogueTurnが正しく作成されること。"""
        turn = DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000)
        assert turn.role == "ai"
        assert turn.content == "こんにちは"


# --- InterviewAgent テスト ---


class TestInterviewAgent:
    """InterviewAgent のテスト。"""

    def test_init_builds_system_prompt(self, agent):
        """_build_system_prompt()が組織名とフェーズヒントを含むこと。"""
        prompt = agent._build_system_prompt()
        assert len(prompt) > 0
        assert "テスト株式会社" in prompt
        assert "フェーズ" in prompt

    def test_init_state(self, agent):
        """初期状態が正しいこと。"""
        assert agent.is_started is False
        assert agent.is_completed is False
        assert agent.history == []
        assert agent.current_question_index == 0
        assert agent.phase == InterviewPhase.ICE_BREAKING

    @pytest.mark.asyncio
    async def test_start_returns_opening_message(self, agent, mock_provider):
        """start()がオープニングメッセージを返すこと。"""
        result = await agent.start()
        assert result == "AIの応答テスト"
        assert agent.is_started is True
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_records_turn(self, agent):
        """start()がAIターンを記録すること。"""
        await agent.start()
        assert len(agent.history) == 1
        assert agent.history[0].role == "ai"

    @pytest.mark.asyncio
    async def test_start_twice_raises(self, agent):
        """start()の二重呼び出しでRuntimeErrorが発生すること。"""
        await agent.start()
        with pytest.raises(RuntimeError, match="already started"):
            await agent.start()

    @pytest.mark.asyncio
    async def test_respond_processes_message(self, agent, mock_provider):
        """respond()がユーザーメッセージを処理してAI応答を返すこと。"""
        await agent.start()
        mock_provider.chat.reset_mock()

        result = await agent.respond("業務フローは〜です")
        assert result == "AIの応答テスト"
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_records_both_turns(self, agent):
        """respond()がユーザーとAIの両ターンを記録すること。"""
        await agent.start()
        await agent.respond("テスト回答")

        # start()のAIターン + respond()のuser + AIターン = 3
        assert len(agent.history) == 3
        assert agent.history[1].role == "user"
        assert agent.history[1].content == "テスト回答"
        assert agent.history[2].role == "ai"

    @pytest.mark.asyncio
    async def test_respond_before_start_raises(self, agent):
        """start()前のrespond()でRuntimeErrorが発生すること。"""
        with pytest.raises(RuntimeError, match="not started"):
            await agent.respond("test")

    @pytest.mark.asyncio
    async def test_respond_after_completed_raises(self, agent, mock_provider):
        """完了後のrespond()でRuntimeErrorが発生すること。"""
        # JSONサマリーレスポンスを設定
        mock_provider.chat.return_value = ChatResponse(
            content='{"summary": "test", "key_findings": [], "risks_identified": [], "follow_up_items": [], "sentiment": "neutral"}',
            model="test",
            finish_reason="stop",
        )
        await agent.start()
        await agent.end()

        with pytest.raises(RuntimeError, match="already completed"):
            await agent.respond("test")

    @pytest.mark.asyncio
    async def test_end_sets_completed(self, agent, mock_provider):
        """end()がis_completedをTrueに設定すること。"""
        # summarize用のJSON応答
        mock_provider.chat.return_value = ChatResponse(
            content='{"summary": "テスト", "key_findings": ["発見1"], "risks_identified": [], "follow_up_items": [], "sentiment": "neutral"}',
            model="test",
            finish_reason="stop",
        )
        await agent.start()
        await agent.end()
        assert agent.is_completed is True

    @pytest.mark.asyncio
    async def test_summarize_returns_dict(self, agent, mock_provider):
        """summarize()がdict形式で返却すること。"""
        mock_provider.chat.return_value = ChatResponse(
            content='{"summary": "概要", "key_findings": ["F1"], "risks_identified": [], "follow_up_items": [], "sentiment": "neutral"}',
            model="test",
            finish_reason="stop",
        )
        await agent.start()
        summary = await agent.summarize()
        assert isinstance(summary, dict)
        assert "summary" in summary
        assert summary["summary"] == "概要"

    @pytest.mark.asyncio
    async def test_summarize_fallback_on_invalid_json(self, agent, mock_provider):
        """summarize()がJSONパース失敗時にフォールバック構造を返すこと。"""
        mock_provider.chat.return_value = ChatResponse(
            content="これはJSONではありません",
            model="test",
            finish_reason="stop",
        )
        await agent.start()
        summary = await agent.summarize()
        assert isinstance(summary, dict)
        assert "summary" in summary
        assert "key_findings" in summary

    def test_get_transcript_empty(self, agent):
        """履歴がない場合、空リストを返すこと。"""
        transcript = agent.get_transcript()
        assert transcript == []

    @pytest.mark.asyncio
    async def test_get_transcript_returns_turns(self, agent):
        """get_transcript()が全ターンのdict listを返すこと。"""
        await agent.start()
        await agent.respond("回答です")

        transcript = agent.get_transcript()
        assert len(transcript) == 3
        assert transcript[0]["role"] == "ai"
        assert transcript[1]["role"] == "user"
        assert "timestamp_ms" in transcript[0]


# --- PromptTemplate テスト ---


class TestPromptTemplate:
    """PromptTemplate のテスト。"""

    def test_format_replaces_placeholders(self):
        """プレースホルダーが置換されること。"""
        template = PromptTemplate(
            template="Hello {name}, welcome to {place}!",
            required_vars=["name", "place"],
        )
        result = template.format(name="太郎", place="東京")
        assert result == "Hello 太郎, welcome to 東京!"

    def test_format_missing_vars_raises(self):
        """必須変数が不足でValueErrorが発生すること。"""
        template = PromptTemplate(
            template="Hello {name}!",
            required_vars=["name"],
        )
        with pytest.raises(ValueError, match="Missing required variables"):
            template.format()


# --- PromptManager テスト ---


class TestPromptManager:
    """PromptManager のテスト。"""

    def test_get_system_prompt_standard(self):
        """標準インタビューのプロンプトが生成されること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="コンプライアンス調査",
            questions=["Q1", "Q2"],
        )
        assert "テスト社" in prompt
        assert "Q1" in prompt

    def test_get_system_prompt_anonymous(self):
        """匿名インタビューのプロンプトが生成されること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="匿名調査",
            questions=["Q1"],
            is_anonymous=True,
        )
        assert "匿名" in prompt

    def test_get_system_prompt_unknown_use_case(self):
        """不明なuse_case_typeでフォールバックが使われること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="unknown_type",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "GRCに関するインタビュー" in prompt

    def test_generate_followup_format(self):
        """GENERATE_FOLLOWUPテンプレートがフォーマットできること。"""
        result = PromptManager.GENERATE_FOLLOWUP.format(
            original_question="業務フローは？",
            answer="承認プロセスがあります",
            context="内部統制評価",
        )
        assert "業務フローは？" in result

    def test_summarize_interview_format(self):
        """SUMMARIZE_INTERVIEWテンプレートがフォーマットできること。"""
        result = PromptManager.SUMMARIZE_INTERVIEW.format(
            purpose="コンプライアンス調査",
            transcript="AI: こんにちは\n回答者: よろしくお願いします",
        )
        assert "コンプライアンス調査" in result

    def test_system_prompt_contains_phase_hint(self):
        """システムプロンプトにphase_hintが含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
            phase_hint="フェーズ2: 本題",
        )
        assert "フェーズ2: 本題" in prompt

    def test_system_prompt_default_phase_hint(self):
        """phase_hint未指定時にデフォルトが使われること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "アイスブレイク" in prompt

    def test_anonymous_prompt_contains_phase_hint(self):
        """匿名プロンプトにもphase_hintが含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="匿名テスト",
            questions=["Q1"],
            is_anonymous=True,
            phase_hint="フェーズ3: 深掘り",
        )
        assert "フェーズ3: 深掘り" in prompt


# --- フェーズ管理テスト ---


class TestInterviewPhaseManagement:
    """インタビューフェーズ管理のテスト。"""

    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        provider.chat.return_value = ChatResponse(
            content="AIの応答", model="test", finish_reason="stop"
        )
        return provider

    @pytest.fixture
    def context_with_questions(self):
        return InterviewContext(
            interview_id="phase-test-001",
            organization_name="フェーズテスト社",
            use_case_type="audit_process",
            interview_purpose="フェーズ管理テスト",
            questions=[f"質問{i}" for i in range(1, 11)],  # 10 questions
        )

    @pytest.fixture
    def agent(self, mock_provider, context_with_questions):
        return InterviewAgent(provider=mock_provider, context=context_with_questions)

    def test_initial_phase_is_ice_breaking(self, agent):
        """初期フェーズがアイスブレイクであること。"""
        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.ICE_BREAKING
        assert "アイスブレイク" in hint

    def test_phase_ice_breaking_with_few_turns(self, agent):
        """ユーザーターン数が少ない場合、アイスブレイクのままであること。"""
        agent.history.append(DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000))
        agent.history.append(DialogueTurn(role="user", content="よろしく", timestamp_ms=2000))
        agent.history.append(DialogueTurn(role="ai", content="ありがとう", timestamp_ms=3000))
        agent.history.append(DialogueTurn(role="user", content="はい", timestamp_ms=4000))

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.ICE_BREAKING
        assert "ラポール" in hint

    def test_phase_transitions_to_main(self, agent):
        """ターン数が増えるとメインフェーズに遷移すること。"""
        # 3 user turns → main phase (3 user turns, 10 questions → ratio = 3/20 = 0.15 < 0.6)
        for i in range(6):
            role = "user" if i % 2 == 0 else "ai"
            agent.history.append(DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000))

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.MAIN
        assert "本題" in hint

    def test_phase_transitions_to_deep_dive(self, agent):
        """カバレッジが60%以上で深掘りフェーズに遷移すること。"""
        # Need user_turns/max(total_questions*2, 1) >= 0.6 → user_turns >= 12 for 10 questions
        for i in range(24):
            role = "user" if i % 2 == 0 else "ai"
            agent.history.append(DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000))

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.DEEP_DIVE
        assert "深掘り" in hint

    def test_phase_transitions_to_closing(self, agent):
        """カバレッジが85%以上でクロージングフェーズに遷移すること。"""
        # Need user_turns/max(total_questions*2, 1) >= 0.85 → user_turns >= 17 for 10 questions
        for i in range(40):
            role = "user" if i % 2 == 0 else "ai"
            agent.history.append(DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000))

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.CLOSING
        assert "クロージング" in hint

    def test_phase_hint_injected_into_system_prompt(self, agent):
        """フェーズヒントがシステムプロンプトに注入されること。"""
        prompt = agent._build_system_prompt()
        assert "フェーズ1: アイスブレイク" in prompt
        assert "フェーズテスト社" in prompt

    def test_phase_enum_values(self):
        """InterviewPhaseのenum値が正しいこと。"""
        assert InterviewPhase.ICE_BREAKING == "ice_breaking"
        assert InterviewPhase.MAIN == "main"
        assert InterviewPhase.DEEP_DIVE == "deep_dive"
        assert InterviewPhase.CLOSING == "closing"


# --- プロンプト内容検証テスト ---


class TestPromptContent:
    """プロンプトの内容が要件を満たしているかの検証テスト。"""

    def test_standard_prompt_has_four_phases(self):
        """標準プロンプトに4フェーズが定義されていること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "フェーズ1" in prompt
        assert "フェーズ2" in prompt
        assert "フェーズ3" in prompt
        assert "フェーズ4" in prompt

    def test_standard_prompt_has_facilitation_techniques(self):
        """標準プロンプトにファシリテーション技法が含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "相槌" in prompt
        assert "傾聴" in prompt
        assert "パラフレーズ" in prompt
        assert "プロービング" in prompt

    def test_standard_prompt_has_aizuchi_examples(self):
        """標準プロンプトに相槌の具体例が含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "なるほど" in prompt
        assert "そうなんですね" in prompt
        assert "興味深いですね" in prompt

    def test_standard_prompt_has_behavioral_rules(self):
        """標準プロンプトに行動規範が含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "一度に複数の質問をしない" in prompt
        assert "誘導的な質問を避け" in prompt

    def test_anonymous_prompt_has_anonymity_emphasis(self):
        """匿名プロンプトに匿名性の強調が含まれること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="匿名テスト",
            questions=["Q1"],
            is_anonymous=True,
        )
        assert "完全匿名" in prompt
        assert "個人を特定" in prompt
        assert "非批判的" in prompt

    def test_anonymous_prompt_has_four_phases(self):
        """匿名プロンプトにも4フェーズが定義されていること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="匿名テスト",
            questions=["Q1"],
            is_anonymous=True,
        )
        assert "フェーズ1" in prompt
        assert "フェーズ2" in prompt
        assert "フェーズ3" in prompt
        assert "フェーズ4" in prompt

    @pytest.mark.asyncio
    async def test_start_uses_duration_from_metadata(self):
        """start()がmetadataのduration_minutesを使用すること。"""
        provider = AsyncMock()
        provider.chat.return_value = ChatResponse(
            content="こんにちは！本日は60分のインタビューです。",
            model="test",
            finish_reason="stop",
        )

        ctx = InterviewContext(
            interview_id="duration-test",
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 60},
        )
        agent = InterviewAgent(provider=provider, context=ctx)
        await agent.start()

        # The opening prompt should contain "約60分"
        call_args = provider.chat.call_args
        messages = call_args[0][0]
        user_msg = [m for m in messages if m.role == "user"][0]
        assert "約60分" in user_msg.content
