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
            agent.history.append(
                DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000)
            )

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.MAIN
        assert "本題" in hint

    def test_phase_transitions_to_deep_dive(self, agent):
        """カバレッジが60%以上で深掘りフェーズに遷移すること。"""
        # Need user_turns/max(total_questions*2, 1) >= 0.6 → user_turns >= 12 for 10 questions
        for i in range(24):
            role = "user" if i % 2 == 0 else "ai"
            agent.history.append(
                DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000)
            )

        hint = agent._get_phase_hint()
        assert agent.phase == InterviewPhase.DEEP_DIVE
        assert "深掘り" in hint

    def test_phase_transitions_to_closing(self, agent):
        """カバレッジが85%以上でクロージングフェーズに遷移すること。"""
        # Need user_turns/max(total_questions*2, 1) >= 0.85 → user_turns >= 17 for 10 questions
        for i in range(40):
            role = "user" if i % 2 == 0 else "ai"
            agent.history.append(
                DialogueTurn(role=role, content=f"turn {i}", timestamp_ms=i * 1000)
            )

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


# --- 時間管理テスト ---


class TestTimeManagement:
    """時間管理機能のテスト。"""

    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        provider.chat.return_value = ChatResponse(
            content="AIの応答", model="test", finish_reason="stop"
        )
        return provider

    def test_time_hint_before_start(self, mock_provider):
        """開始前のtime_hintがduration_minutesを含むこと。"""
        ctx = InterviewContext(
            interview_id="time-test-001",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1", "Q2", "Q3"],
            metadata={"duration_minutes": 15},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        hint = agent._get_time_hint()
        assert "15分" in hint
        assert "3問" in hint

    def test_time_hint_default_duration(self, mock_provider):
        """duration_minutes未設定時にデフォルト30分が使われること。"""
        ctx = InterviewContext(
            interview_id="time-test-002",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        hint = agent._get_time_hint()
        assert "30分" in hint

    def test_time_hint_during_interview(self, mock_provider):
        """インタビュー中のtime_hintに経過/残り時間が含まれること。"""
        import time

        ctx = InterviewContext(
            interview_id="time-test-003",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 60},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        agent.is_started = True
        # Simulate history with a recent start timestamp
        now_ms = int(time.time() * 1000)
        agent.history.append(
            DialogueTurn(role="ai", content="こんにちは", timestamp_ms=now_ms - 300000)
        )  # 5 min ago

        hint = agent._get_time_hint()
        assert "経過" in hint
        assert "残り" in hint

    def test_time_hint_warning_5min(self, mock_provider):
        """残り5分以内でまとめ準備の指示が出ること。"""
        import time

        ctx = InterviewContext(
            interview_id="time-test-004",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 30},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        agent.is_started = True
        # Simulate: started 26 minutes ago (4 min remaining)
        now_ms = int(time.time() * 1000)
        agent.history.append(
            DialogueTurn(role="ai", content="start", timestamp_ms=now_ms - 26 * 60000)
        )

        hint = agent._get_time_hint()
        assert "残り" in hint
        assert "まとめ" in hint

    def test_time_hint_warning_2min(self, mock_provider):
        """残り2分以内でクロージング指示が出ること。"""
        import time

        ctx = InterviewContext(
            interview_id="time-test-005",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 30},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        agent.is_started = True
        # Simulate: started 29 minutes ago (1 min remaining)
        now_ms = int(time.time() * 1000)
        agent.history.append(
            DialogueTurn(role="ai", content="start", timestamp_ms=now_ms - 29 * 60000)
        )

        hint = agent._get_time_hint()
        assert "クロージング" in hint

    def test_time_hint_exceeded(self, mock_provider):
        """時間超過で超過メッセージが出ること。"""
        import time

        ctx = InterviewContext(
            interview_id="time-test-006",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 15},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        agent.is_started = True
        # Simulate: started 20 minutes ago (exceeded by 5 min)
        now_ms = int(time.time() * 1000)
        agent.history.append(
            DialogueTurn(role="ai", content="start", timestamp_ms=now_ms - 20 * 60000)
        )

        hint = agent._get_time_hint()
        assert "時間超過" in hint
        assert "持ち越し" in hint

    def test_time_hint_in_system_prompt(self, mock_provider):
        """time_hintがシステムプロンプトに含まれること。"""
        ctx = InterviewContext(
            interview_id="time-test-007",
            organization_name="テスト社",
            use_case_type="audit_process",
            interview_purpose="テスト",
            questions=["Q1"],
            metadata={"duration_minutes": 45},
        )
        agent = InterviewAgent(provider=mock_provider, context=ctx)
        prompt = agent._build_system_prompt()
        assert "時間管理" in prompt
        assert "45分" in prompt

    def test_prompt_manager_time_hint_parameter(self):
        """PromptManager.get_system_promptにtime_hintが渡せること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
            time_hint="【残り約3分】クロージングに入ってください。",
        )
        assert "残り約3分" in prompt

    def test_prompt_manager_default_time_hint(self):
        """time_hint未指定時にデフォルトが使われること。"""
        prompt = PromptManager.get_system_prompt(
            organization_name="テスト社",
            use_case_type="compliance_survey",
            interview_purpose="テスト",
            questions=["Q1"],
        )
        assert "ペース" in prompt


# --- カバレッジ評価テスト ---


class TestCoverageAssessment:
    """カバレッジ評価機能のテスト。"""

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
            interview_id="coverage-test-001",
            organization_name="カバレッジテスト社",
            use_case_type="audit_process",
            interview_purpose="カバレッジテスト",
            questions=["質問1: 業務フローは？", "質問2: リスクは？", "質問3: 改善案は？"],
        )

    @pytest.fixture
    def agent(self, mock_provider, context_with_questions):
        return InterviewAgent(provider=mock_provider, context=context_with_questions)

    @pytest.mark.asyncio
    async def test_assess_coverage_empty_history(self, agent):
        """履歴が空の場合、カバレッジ0%が返されること。"""
        result = await agent.assess_coverage()
        assert result["overall_percentage"] == 0
        assert len(result["questions"]) == 3
        assert all(q["status"] == "unanswered" for q in result["questions"])
        assert result["suggest_end"] is False

    @pytest.mark.asyncio
    async def test_assess_coverage_with_valid_json(self, agent, mock_provider):
        """AIが正しいJSONを返した場合、パース結果が返されること。"""
        agent.history.append(DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000))
        agent.history.append(
            DialogueTurn(role="user", content="業務フローは...", timestamp_ms=2000)
        )

        mock_provider.chat.return_value = ChatResponse(
            content='{"overall_percentage": 40, "questions": [{"question": "Q1", "status": "answered", "percentage": 80}, {"question": "Q2", "status": "unanswered", "percentage": 0}, {"question": "Q3", "status": "partial", "percentage": 40}], "suggest_end": false}',
            model="test",
            finish_reason="stop",
        )

        result = await agent.assess_coverage()
        assert result["overall_percentage"] == 40
        assert len(result["questions"]) == 3
        assert result["suggest_end"] is False

    @pytest.mark.asyncio
    async def test_assess_coverage_json_fallback(self, agent, mock_provider):
        """AIがJSONでない応答を返した場合、フォールバック推定が使われること。"""
        agent.history.append(DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000))
        agent.history.append(DialogueTurn(role="user", content="回答", timestamp_ms=2000))

        mock_provider.chat.return_value = ChatResponse(
            content="JSONでない応答です。", model="test", finish_reason="stop"
        )

        result = await agent.assess_coverage()
        assert isinstance(result["overall_percentage"], int)
        assert "questions" in result
        assert "suggest_end" in result

    @pytest.mark.asyncio
    async def test_assess_coverage_markdown_code_block(self, agent, mock_provider):
        """AI応答がMarkdownコードブロック付きJSONの場合もパースできること。"""
        agent.history.append(DialogueTurn(role="ai", content="Hi", timestamp_ms=1000))
        agent.history.append(DialogueTurn(role="user", content="Hello", timestamp_ms=2000))

        mock_provider.chat.return_value = ChatResponse(
            content='```json\n{"overall_percentage": 75, "questions": [], "suggest_end": false}\n```',
            model="test",
            finish_reason="stop",
        )

        result = await agent.assess_coverage()
        assert result["overall_percentage"] == 75


# --- 持ち越し (carry_over) テスト ---


class TestCarryOver:
    """セッション持ち越し機能のテスト。"""

    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        provider.chat.return_value = ChatResponse(
            content="AIの応答", model="test", finish_reason="stop"
        )
        return provider

    @pytest.fixture
    def context(self):
        return InterviewContext(
            interview_id="carry-over-test-001",
            organization_name="持ち越しテスト社",
            use_case_type="risk_assessment",
            interview_purpose="リスク評価",
            questions=["Q1: 現状は？", "Q2: リスクは？", "Q3: 対策は？", "Q4: 優先度は？"],
        )

    @pytest.fixture
    def agent(self, mock_provider, context):
        return InterviewAgent(provider=mock_provider, context=context)

    def test_generate_carry_over_without_coverage(self, agent):
        """coverage引数なしでcarry_overが生成されること。"""
        agent.history = [
            DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000),
            DialogueTurn(role="user", content="よろしく", timestamp_ms=2000),
            DialogueTurn(role="ai", content="Q1について", timestamp_ms=3000),
            DialogueTurn(role="user", content="現状は...", timestamp_ms=4000),
        ]

        result = agent.generate_carry_over()
        assert result["carry_over"] is True
        assert result["previous_interview_id"] == "carry-over-test-001"
        assert result["coverage_percentage"] == 0
        assert result["total_turns"] == 4
        # 2 user messages → covered 2 of 4 questions → unanswered = ["Q3: 対策は？", "Q4: 優先度は？"]
        assert len(result["unanswered_questions"]) == 2

    def test_generate_carry_over_with_coverage(self, agent):
        """coverage引数ありでcarry_overにカバレッジ情報が含まれること。"""
        agent.history = [
            DialogueTurn(role="ai", content="Hi", timestamp_ms=1000),
            DialogueTurn(role="user", content="Hello", timestamp_ms=2000),
        ]

        coverage = {
            "overall_percentage": 60,
            "questions": [
                {"question": "Q1", "status": "answered", "percentage": 100},
                {"question": "Q2", "status": "partial", "percentage": 50},
                {"question": "Q3", "status": "unanswered", "percentage": 0},
                {"question": "Q4", "status": "unanswered", "percentage": 0},
            ],
            "suggest_end": False,
        }

        result = agent.generate_carry_over(coverage)
        assert result["coverage_percentage"] == 60
        # partial + unanswered = 3 questions
        assert len(result["unanswered_questions"]) == 3
        assert "Q2" in result["unanswered_questions"][0]

    def test_load_carry_over(self, agent):
        """load_carry_overでコンテキストにcarry_overが設定されること。"""
        carry_over = {
            "carry_over": True,
            "previous_interview_id": "prev-001",
            "coverage_percentage": 45,
            "unanswered_questions": ["Q3", "Q4"],
            "total_turns": 8,
        }

        agent.load_carry_over(carry_over)
        assert agent.context.metadata["carry_over"] == carry_over
        assert agent.context.metadata["carry_over"]["previous_interview_id"] == "prev-001"

    def test_carry_over_in_system_prompt(self, agent):
        """carry_over読み込み後、システムプロンプトにmetadataが反映されること。"""
        carry_over = {
            "carry_over": True,
            "previous_interview_id": "prev-001",
            "unanswered_questions": ["Q3", "Q4"],
        }
        agent.load_carry_over(carry_over)

        # metadata にcarry_overが入っていることを確認
        assert "carry_over" in agent.context.metadata

    def test_get_transcript_after_carry_over(self, agent):
        """carry_over読み込み後もget_transcriptが正常に動作すること。"""
        agent.load_carry_over({"carry_over": True, "unanswered_questions": ["Q3"]})
        agent.history.append(DialogueTurn(role="ai", content="前回の続き", timestamp_ms=1000))

        transcript = agent.get_transcript()
        assert len(transcript) == 1
        assert transcript[0]["content"] == "前回の続き"


# --- 品質スコアリングテスト ---


class TestQualityScoring:
    """インタビュー品質スコアリング機能のテスト。"""

    @pytest.fixture
    def mock_provider(self):
        provider = AsyncMock()
        provider.chat.return_value = ChatResponse(
            content="AIの応答", model="test", finish_reason="stop"
        )
        return provider

    @pytest.fixture
    def context(self):
        return InterviewContext(
            interview_id="quality-test-001",
            organization_name="品質テスト社",
            use_case_type="compliance_survey",
            interview_purpose="品質評価テスト",
            questions=["Q1: 現状は？", "Q2: リスクは？", "Q3: 対策は？"],
        )

    @pytest.fixture
    def agent(self, mock_provider, context):
        return InterviewAgent(provider=mock_provider, context=context)

    @pytest.mark.asyncio
    async def test_evaluate_quality_empty_history(self, agent):
        """履歴が空の場合、スコア0が返されること。"""
        result = await agent.evaluate_quality()
        assert result["overall_score"] == 0
        assert result["recommendation"] == "retry"
        assert result["strengths"] == []
        assert result["improvements"] == []

    @pytest.mark.asyncio
    async def test_evaluate_quality_valid_json(self, agent, mock_provider):
        """AIが正しいJSON評価を返した場合、パース結果が返されること。"""
        agent.history = [
            DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000),
            DialogueTurn(role="user", content="詳細な回答です", timestamp_ms=2000),
        ]

        mock_provider.chat.return_value = ChatResponse(
            content='{"overall_score": 4.2, "dimensions": {"depth": {"score": 4, "comment": "good"}, "coverage": {"score": 4, "comment": "ok"}, "rapport": {"score": 5, "comment": "excellent"}, "evidence": {"score": 3, "comment": "fair"}, "actionability": {"score": 5, "comment": "great"}}, "strengths": ["good rapport"], "improvements": ["more evidence"], "recommendation": "accept"}',
            model="test",
            finish_reason="stop",
        )

        result = await agent.evaluate_quality()
        assert result["overall_score"] == 4.2
        assert result["dimensions"]["depth"]["score"] == 4
        assert result["recommendation"] == "accept"
        assert len(result["strengths"]) == 1
        assert len(result["improvements"]) == 1

    @pytest.mark.asyncio
    async def test_evaluate_quality_json_fallback(self, agent, mock_provider):
        """AIがJSONでない応答を返した場合、フォールバック推定が使われること。"""
        agent.history = [
            DialogueTurn(role="ai", content="こんにちは", timestamp_ms=1000),
            DialogueTurn(
                role="user",
                content="現状の業務フローについて詳しくお話しします。まず承認プロセスがあり...",
                timestamp_ms=2000,
            ),
        ]

        mock_provider.chat.return_value = ChatResponse(
            content="JSONでない応答", model="test", finish_reason="stop"
        )

        result = await agent.evaluate_quality()
        assert isinstance(result["overall_score"], float)
        assert "dimensions" in result
        assert "depth" in result["dimensions"]
        assert "recommendation" in result

    @pytest.mark.asyncio
    async def test_evaluate_quality_dimensions(self, agent, mock_provider):
        """5つの評価軸すべてが含まれること。"""
        agent.history = [
            DialogueTurn(role="ai", content="Hi", timestamp_ms=1000),
            DialogueTurn(role="user", content="Hello", timestamp_ms=2000),
        ]

        mock_provider.chat.return_value = ChatResponse(
            content="not json", model="test", finish_reason="stop"
        )

        result = await agent.evaluate_quality()
        expected_dims = ["depth", "coverage", "rapport", "evidence", "actionability"]
        for dim in expected_dims:
            assert dim in result["dimensions"]
            assert "score" in result["dimensions"][dim]

    @pytest.mark.asyncio
    async def test_evaluate_quality_recommendation_values(self, agent, mock_provider):
        """recommendationが有効な値であること。"""
        agent.history = [
            DialogueTurn(role="ai", content="Hi", timestamp_ms=1000),
            DialogueTurn(role="user", content="a", timestamp_ms=2000),
        ]

        mock_provider.chat.return_value = ChatResponse(
            content="fallback", model="test", finish_reason="stop"
        )

        result = await agent.evaluate_quality()
        assert result["recommendation"] in ("accept", "supplement", "retry")
