# AIプロバイダー仕様書

## 目次

1. [はじめに](#1-はじめに)
2. [アーキテクチャ設計](#2-アーキテクチャ設計)
3. [抽象化レイヤー](#3-抽象化レイヤー)
4. [LLMプロバイダー](#4-llmプロバイダー)
5. [音声サービス](#5-音声サービス)
6. [翻訳サービス](#6-翻訳サービス)
7. [レイテンシ最適化](#7-レイテンシ最適化)
8. [モデル選択ガイド](#8-モデル選択ガイド)
9. [プロンプト設計](#9-プロンプト設計)
10. [コスト最適化](#10-コスト最適化)
11. [エラー処理とフォールバック](#11-エラー処理とフォールバック)
12. [テスト方法](#12-テスト方法)

---

## 1. はじめに

### 1.1 このドキュメントの目的

本ドキュメントでは、AI Interview Toolで使用するAIプロバイダーの抽象化設計と実装について詳細に解説します。マルチクラウド対応のAI基盤を構築する方法を学習できます。

### 1.2 学習ゴール

1. AIプロバイダーの抽象化パターンを理解できる
2. Azure OpenAI、AWS Bedrock、GCP Vertex AIの違いを理解できる
3. リアルタイム対話のためのレイテンシ最適化ができる
4. 音声認識・音声合成サービスを統合できる

### 1.3 対応するAIサービス

| カテゴリ | Azure | AWS | GCP |
|---------|-------|-----|-----|
| LLM | Azure OpenAI (GPT-5.2) | Bedrock (Claude 4.6) | Vertex AI (Gemini 3.0) |
| 音声認識 | Speech Services | Transcribe | Speech-to-Text |
| 音声合成 | Speech Services | Polly | Text-to-Speech |
| 翻訳 | Translator | Translate | Cloud Translation |

---

## 2. アーキテクチャ設計

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AIプロバイダー抽象化レイヤー                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     アプリケーション層                               │   │
│  │   InterviewService / DialogueService / TranscriptionService        │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                         │
│                                  ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       抽象インターフェース                           │   │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐           │   │
│  │  │  AIProvider   │  │ SpeechProvider│  │TranslateProvider│          │   │
│  │  │  (Protocol)   │  │  (Protocol)   │  │   (Protocol)  │           │   │
│  │  └───────────────┘  └───────────────┘  └───────────────┘           │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                         │
│           ┌──────────────────────┼──────────────────────┐                 │
│           ▼                      ▼                      ▼                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐         │
│  │    Azure        │   │     AWS         │   │      GCP        │         │
│  │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │         │
│  │  │Azure      │  │   │  │Bedrock    │  │   │  │Vertex AI  │  │         │
│  │  │OpenAI     │  │   │  │(Claude)   │  │   │  │(Gemini)   │  │         │
│  │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │         │
│  │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │         │
│  │  │Speech     │  │   │  │Transcribe │  │   │  │Speech-to  │  │         │
│  │  │Services   │  │   │  │+ Polly    │  │   │  │Text/TTS   │  │         │
│  │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │         │
│  │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │         │
│  │  │Translator │  │   │  │Translate  │  │   │  │Cloud      │  │         │
│  │  │           │  │   │  │           │  │   │  │Translation│  │         │
│  │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │         │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 設計原則

```
┌─────────────────────────────────────────────────────────────────┐
│                    設計原則                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 依存性逆転の原則 (DIP)                                       │
│     - ビジネスロジックは抽象インターフェースに依存                │
│     - 具体的なプロバイダー実装は交換可能                         │
│                                                                 │
│  2. 開放閉鎖の原則 (OCP)                                         │
│     - 新しいプロバイダーの追加は既存コードを変更せずに可能       │
│     - 拡張に対して開いており、変更に対して閉じている             │
│                                                                 │
│  3. インターフェース分離の原則 (ISP)                             │
│     - LLM、Speech、Translateは別インターフェース                 │
│     - 必要な機能のみに依存                                       │
│                                                                 │
│  4. ファクトリーパターン                                         │
│     - 設定に基づいて適切な実装を生成                             │
│     - プロバイダーの切り替えが容易                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 抽象化レイヤー

### 3.1 AIプロバイダーインターフェース

```python
# packages/@grc/ai/src/grc_ai/base.py

from abc import ABC, abstractmethod
from typing import Protocol, AsyncIterator
from dataclasses import dataclass


@dataclass
class Message:
    """チャットメッセージ

    Attributes:
        role: 発話者のロール (system/user/assistant)
        content: メッセージ内容
    """
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """チャット応答

    Attributes:
        content: 応答テキスト
        model: 使用されたモデル名
        usage: トークン使用量
        finish_reason: 終了理由
    """
    content: str
    model: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int}
    finish_reason: str  # "stop" | "length" | "content_filter"


@dataclass
class ChatChunk:
    """ストリーミング応答のチャンク

    Attributes:
        content: 応答テキストの断片
        is_final: 最後のチャンクかどうか
    """
    content: str
    is_final: bool = False


class AIProvider(Protocol):
    """AIプロバイダーの抽象インターフェース

    全てのLLMプロバイダーはこのインターフェースを実装します。
    Protocolを使用することで、ダックタイピングが可能になります。

    使用例:
        provider: AIProvider = create_ai_provider(config)
        response = await provider.chat(messages)
    """

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """同期的なチャット応答を取得

        Args:
            messages: 会話履歴
            temperature: 生成のランダム性 (0.0-2.0)
            max_tokens: 最大トークン数
            **kwargs: プロバイダー固有のオプション

        Returns:
            チャット応答

        Raises:
            AIProviderError: API呼び出し失敗時
        """
        ...

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """ストリーミングでチャット応答を取得

        リアルタイム対話で使用。応答を段階的に返します。

        Args:
            messages: 会話履歴
            temperature: 生成のランダム性
            max_tokens: 最大トークン数
            **kwargs: プロバイダー固有のオプション

        Yields:
            応答チャンク

        Raises:
            AIProviderError: API呼び出し失敗時
        """
        ...

    async def embed(
        self,
        text: str,
        model: str | None = None,
    ) -> list[float]:
        """テキストを埋め込みベクトルに変換

        RAG（検索拡張生成）で使用。

        Args:
            text: 埋め込み対象のテキスト
            model: 使用する埋め込みモデル

        Returns:
            埋め込みベクトル（1536次元等）

        Raises:
            AIProviderError: API呼び出し失敗時
        """
        ...

    @property
    def provider_name(self) -> str:
        """プロバイダー名を返す"""
        ...

    @property
    def default_model(self) -> str:
        """デフォルトのモデル名を返す"""
        ...
```

### 3.2 ファクトリー実装

```python
# packages/@grc/ai/src/grc_ai/factory.py

from enum import Enum
from dataclasses import dataclass


class AIProviderType(str, Enum):
    """利用可能なAIプロバイダー"""
    AZURE_OPENAI = "azure_openai"
    AWS_BEDROCK = "aws_bedrock"
    GCP_VERTEX = "gcp_vertex"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class AIProviderConfig:
    """AIプロバイダー設定

    Attributes:
        provider: プロバイダータイプ
        model: 使用するモデル名
        temperature: デフォルトの温度パラメータ
        max_tokens: デフォルトの最大トークン数

    Azure OpenAI固有:
        azure_endpoint: Azure OpenAIエンドポイント
        azure_api_key: APIキー
        azure_deployment: デプロイメント名

    AWS Bedrock固有:
        aws_region: AWSリージョン
        aws_access_key_id: アクセスキーID
        aws_secret_access_key: シークレットアクセスキー

    GCP Vertex AI固有:
        gcp_project_id: GCPプロジェクトID
        gcp_location: ロケーション
    """
    provider: AIProviderType
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096

    # Azure
    azure_endpoint: str | None = None
    azure_api_key: str | None = None
    azure_deployment: str | None = None
    azure_api_version: str = "2024-12-01"

    # AWS
    aws_region: str = "ap-northeast-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    # GCP
    gcp_project_id: str | None = None
    gcp_location: str = "asia-northeast1"


def create_ai_provider(config: AIProviderConfig) -> AIProvider:
    """設定に基づいてAIプロバイダーを生成

    ファクトリーパターンにより、設定だけでプロバイダーを切り替え可能。

    Args:
        config: プロバイダー設定

    Returns:
        AIProviderインターフェースを実装したインスタンス

    Raises:
        ValueError: 未対応のプロバイダータイプ

    使用例:
        config = AIProviderConfig(
            provider=AIProviderType.AZURE_OPENAI,
            model="gpt-5.2",
            azure_endpoint="https://xxx.openai.azure.com/",
            azure_api_key="xxx",
            azure_deployment="gpt-52",
        )
        provider = create_ai_provider(config)
    """
    match config.provider:
        case AIProviderType.AZURE_OPENAI:
            from .providers.azure_openai import AzureOpenAIProvider
            return AzureOpenAIProvider(config)

        case AIProviderType.AWS_BEDROCK:
            from .providers.aws_bedrock import AWSBedrockProvider
            return AWSBedrockProvider(config)

        case AIProviderType.GCP_VERTEX:
            from .providers.gcp_vertex import GCPVertexAIProvider
            return GCPVertexAIProvider(config)

        case AIProviderType.OPENAI:
            from .providers.openai_direct import OpenAIProvider
            return OpenAIProvider(config)

        case AIProviderType.ANTHROPIC:
            from .providers.anthropic_direct import AnthropicProvider
            return AnthropicProvider(config)

        case _:
            raise ValueError(f"Unknown provider: {config.provider}")
```

---

## 4. LLMプロバイダー

### 4.1 Azure OpenAI 実装

```python
# packages/@grc/ai/src/grc_ai/providers/azure_openai.py

from openai import AsyncAzureOpenAI
from typing import AsyncIterator


class AzureOpenAIProvider:
    """Azure OpenAI プロバイダー

    Microsoft Azure上でホストされるOpenAIモデルを使用します。
    エンタープライズ環境での利用に適しています。

    特徴:
    - VNet統合による閉域網接続
    - コンテンツフィルタリング
    - SLAによる可用性保証
    - リージョン冗長性

    対応モデル (2026年):
    - gpt-5.2: 最新の高性能モデル
    - gpt-5-nano: 高速・低コストモデル
    - gpt-4o: バランス型モデル
    """

    def __init__(self, config: AIProviderConfig):
        """
        Args:
            config: プロバイダー設定

        Raises:
            ValueError: 必須設定が不足
        """
        if not config.azure_endpoint:
            raise ValueError("Azure endpoint is required")
        if not config.azure_api_key:
            raise ValueError("Azure API key is required")

        self.config = config
        self.client = AsyncAzureOpenAI(
            azure_endpoint=config.azure_endpoint,
            api_key=config.azure_api_key,
            api_version=config.azure_api_version,
        )

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    @property
    def default_model(self) -> str:
        return self.config.azure_deployment or self.config.model

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """チャット応答を取得

        内部処理:
        1. メッセージをOpenAI形式に変換
        2. Azure OpenAI APIを呼び出し
        3. 応答をChatResponseに変換
        """
        # メッセージ形式の変換
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.default_model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                **kwargs,
            )

            return ChatResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
                finish_reason=response.choices[0].finish_reason,
            )

        except Exception as e:
            # エラーをAIProviderErrorに変換
            raise self._handle_error(e)

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """ストリーミングでチャット応答を取得

        リアルタイム対話用。応答を逐次返すことで、
        ユーザーに素早いフィードバックを提供します。

        使用例:
            async for chunk in provider.stream_chat(messages):
                print(chunk.content, end="", flush=True)
        """
        openai_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]

        try:
            stream = await self.client.chat.completions.create(
                model=self.default_model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True,  # ストリーミング有効化
                **kwargs,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield ChatChunk(
                        content=chunk.choices[0].delta.content,
                        is_final=chunk.choices[0].finish_reason is not None,
                    )

        except Exception as e:
            raise self._handle_error(e)

    async def embed(
        self,
        text: str,
        model: str | None = None,
    ) -> list[float]:
        """テキストを埋め込みベクトルに変換

        RAG（Retrieval Augmented Generation）で使用。
        類似テキストの検索に利用します。
        """
        embedding_model = model or "text-embedding-3-large"

        try:
            response = await self.client.embeddings.create(
                model=embedding_model,
                input=text,
            )
            return response.data[0].embedding

        except Exception as e:
            raise self._handle_error(e)

    def _handle_error(self, error: Exception) -> AIProviderError:
        """エラーをAIProviderErrorに変換"""
        from openai import RateLimitError, APIError, AuthenticationError

        if isinstance(error, RateLimitError):
            return AIProviderError(
                code=ErrorCode.AI_RATE_LIMIT,
                message="Rate limit exceeded",
                is_retryable=True,
                retry_after=int(error.headers.get("Retry-After", 60)),
            ).with_cause(error)

        if isinstance(error, AuthenticationError):
            return AIProviderError(
                code=ErrorCode.AI_PROVIDER_ERROR,
                message="Authentication failed",
                is_retryable=False,
            ).with_cause(error)

        return AIProviderError(
            code=ErrorCode.AI_PROVIDER_ERROR,
            message=str(error),
            is_retryable=True,
        ).with_cause(error)
```

### 4.2 AWS Bedrock 実装

```python
# packages/@grc/ai/src/grc_ai/providers/aws_bedrock.py

import boto3
import json
from typing import AsyncIterator


class AWSBedrockProvider:
    """AWS Bedrock プロバイダー

    Amazon Bedrockを使用して様々なLLMにアクセスします。

    特徴:
    - 複数のモデル（Claude, Titan, Llama等）に統一APIでアクセス
    - AWS IAMによる認証
    - PrivateLinkによる閉域網接続
    - 従量課金モデル

    対応モデル (2026年):
    - anthropic.claude-opus-4.5: 最高性能モデル
    - anthropic.claude-sonnet-4.6: バランス型
    - anthropic.claude-4.6-haiku: 高速・低コスト
    - amazon.nova-lite: Amazon独自モデル
    """

    # モデルIDとベンダーのマッピング
    MODEL_VENDORS = {
        "anthropic.claude": "anthropic",
        "amazon.nova": "amazon",
        "amazon.titan": "amazon",
        "meta.llama": "meta",
    }

    def __init__(self, config: AIProviderConfig):
        self.config = config

        # Boto3クライアントの初期化
        session = boto3.Session(
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            region_name=config.aws_region,
        )
        self.client = session.client("bedrock-runtime")

    @property
    def provider_name(self) -> str:
        return "aws_bedrock"

    @property
    def default_model(self) -> str:
        return self.config.model

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """チャット応答を取得

        Bedrockでは、モデルごとに入力形式が異なるため、
        モデルに応じてリクエストを変換します。
        """
        model_id = self.config.model
        vendor = self._get_vendor(model_id)

        # モデルベンダーに応じたリクエスト形式
        if vendor == "anthropic":
            request_body = self._build_anthropic_request(
                messages, temperature, max_tokens
            )
        elif vendor == "amazon":
            request_body = self._build_amazon_request(
                messages, temperature, max_tokens
            )
        else:
            raise ValueError(f"Unsupported model vendor: {vendor}")

        try:
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            response_body = json.loads(response["body"].read())
            return self._parse_response(response_body, vendor)

        except Exception as e:
            raise self._handle_error(e)

    def _build_anthropic_request(
        self,
        messages: list[Message],
        temperature: float,
        max_tokens: int | None,
    ) -> dict:
        """Anthropic Claude形式のリクエストを構築"""
        # システムメッセージを分離
        system_message = None
        chat_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": chat_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature,
        }

        if system_message:
            request["system"] = system_message

        return request

    def _build_amazon_request(
        self,
        messages: list[Message],
        temperature: float,
        max_tokens: int | None,
    ) -> dict:
        """Amazon Titan/Nova形式のリクエストを構築"""
        # 会話履歴を単一のプロンプトに変換
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"Instructions: {msg.content}\n\n"
            elif msg.role == "user":
                prompt += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n"

        prompt += "Assistant: "

        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens or self.config.max_tokens,
                "temperature": temperature,
            },
        }

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """ストリーミングでチャット応答を取得"""
        model_id = self.config.model
        vendor = self._get_vendor(model_id)

        if vendor == "anthropic":
            request_body = self._build_anthropic_request(
                messages, temperature, max_tokens
            )
        else:
            raise ValueError(f"Streaming not supported for vendor: {vendor}")

        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json",
            )

            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                if "delta" in chunk and "text" in chunk["delta"]:
                    yield ChatChunk(
                        content=chunk["delta"]["text"],
                        is_final=chunk.get("stop_reason") is not None,
                    )

        except Exception as e:
            raise self._handle_error(e)

    def _get_vendor(self, model_id: str) -> str:
        """モデルIDからベンダーを判定"""
        for prefix, vendor in self.MODEL_VENDORS.items():
            if model_id.startswith(prefix):
                return vendor
        raise ValueError(f"Unknown model vendor for: {model_id}")

    def _parse_response(self, body: dict, vendor: str) -> ChatResponse:
        """レスポンスを共通形式に変換"""
        if vendor == "anthropic":
            return ChatResponse(
                content=body["content"][0]["text"],
                model=body.get("model", self.config.model),
                usage={
                    "prompt_tokens": body.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": body.get("usage", {}).get("output_tokens", 0),
                },
                finish_reason=body.get("stop_reason", "stop"),
            )
        elif vendor == "amazon":
            return ChatResponse(
                content=body["results"][0]["outputText"],
                model=self.config.model,
                usage={},  # Amazon モデルは使用量を返さない
                finish_reason="stop",
            )

    def _handle_error(self, error: Exception) -> AIProviderError:
        """エラー処理"""
        from botocore.exceptions import ClientError

        if isinstance(error, ClientError):
            error_code = error.response.get("Error", {}).get("Code", "")

            if error_code == "ThrottlingException":
                return AIProviderError(
                    code=ErrorCode.AI_RATE_LIMIT,
                    message="Rate limit exceeded",
                    is_retryable=True,
                    retry_after=60,
                ).with_cause(error)

        return AIProviderError(
            code=ErrorCode.AI_PROVIDER_ERROR,
            message=str(error),
            is_retryable=True,
        ).with_cause(error)
```

### 4.3 GCP Vertex AI 実装

```python
# packages/@grc/ai/src/grc_ai/providers/gcp_vertex.py

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Content, Part
from typing import AsyncIterator


class GCPVertexAIProvider:
    """GCP Vertex AI プロバイダー

    Google Cloud上のAIモデルにアクセスします。

    特徴:
    - Geminiモデルへのアクセス
    - Google検索によるグラウンディング
    - VPC Service Controlsによるセキュリティ
    - カスタムモデルのデプロイ

    対応モデル (2026年):
    - gemini-3.0-pro: 高性能汎用モデル
    - gemini-3.0-flash: 高速レスポンスモデル
    - gemini-3.0-ultra: 最高性能モデル
    """

    def __init__(self, config: AIProviderConfig):
        if not config.gcp_project_id:
            raise ValueError("GCP project ID is required")

        self.config = config

        # Vertex AI の初期化
        aiplatform.init(
            project=config.gcp_project_id,
            location=config.gcp_location,
        )

        self.model = GenerativeModel(config.model)

    @property
    def provider_name(self) -> str:
        return "gcp_vertex"

    @property
    def default_model(self) -> str:
        return self.config.model

    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """チャット応答を取得"""
        # メッセージをVertex AI形式に変換
        contents = self._convert_messages(messages)

        # 生成設定
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or self.config.max_tokens,
        }

        try:
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
            )

            return ChatResponse(
                content=response.text,
                model=self.config.model,
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                },
                finish_reason=response.candidates[0].finish_reason.name,
            )

        except Exception as e:
            raise self._handle_error(e)

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """ストリーミングでチャット応答を取得"""
        contents = self._convert_messages(messages)

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or self.config.max_tokens,
        }

        try:
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield ChatChunk(
                        content=chunk.text,
                        is_final=False,
                    )

            yield ChatChunk(content="", is_final=True)

        except Exception as e:
            raise self._handle_error(e)

    def _convert_messages(self, messages: list[Message]) -> list[Content]:
        """メッセージをVertex AI形式に変換"""
        contents = []

        for msg in messages:
            if msg.role == "system":
                # Geminiではシステムメッセージをuserとして扱う
                contents.append(Content(
                    role="user",
                    parts=[Part.from_text(f"Instructions: {msg.content}")],
                ))
                contents.append(Content(
                    role="model",
                    parts=[Part.from_text("Understood. I will follow these instructions.")],
                ))
            elif msg.role == "user":
                contents.append(Content(
                    role="user",
                    parts=[Part.from_text(msg.content)],
                ))
            elif msg.role == "assistant":
                contents.append(Content(
                    role="model",
                    parts=[Part.from_text(msg.content)],
                ))

        return contents

    def _handle_error(self, error: Exception) -> AIProviderError:
        """エラー処理"""
        return AIProviderError(
            code=ErrorCode.AI_PROVIDER_ERROR,
            message=str(error),
            is_retryable=True,
        ).with_cause(error)
```

---

## 5. 音声サービス

### 5.1 音声サービスインターフェース

```python
# packages/@grc/ai/src/grc_ai/speech/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    """音声認識結果

    Attributes:
        text: 認識されたテキスト
        confidence: 信頼度 (0.0-1.0)
        language: 検出された言語
        is_final: 確定結果かどうか
        timestamp_ms: タイムスタンプ（ミリ秒）
    """
    text: str
    confidence: float
    language: str
    is_final: bool = True
    timestamp_ms: int = 0


@dataclass
class SynthesisResult:
    """音声合成結果

    Attributes:
        audio: 音声データ（バイト列）
        format: 音声フォーマット (wav/mp3/ogg)
        sample_rate: サンプルレート
        duration_ms: 音声長（ミリ秒）
    """
    audio: bytes
    format: str
    sample_rate: int
    duration_ms: int


class SpeechProvider(ABC):
    """音声サービスの抽象インターフェース

    音声認識（STT）と音声合成（TTS）の両方を提供します。
    """

    @abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        language: str = "ja-JP",
        format: str = "wav",
    ) -> TranscriptionResult:
        """音声をテキストに変換（STT）

        Args:
            audio: 音声データ
            language: 言語コード
            format: 音声フォーマット

        Returns:
            認識結果
        """
        ...

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
    ) -> AsyncIterator[TranscriptionResult]:
        """リアルタイム音声認識

        マイク入力などのストリーミング音声を
        リアルタイムでテキストに変換します。

        Args:
            audio_stream: 音声データのストリーム
            language: 言語コード

        Yields:
            認識結果（中間結果含む）
        """
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice: str | None = None,
    ) -> SynthesisResult:
        """テキストを音声に変換（TTS）

        Args:
            text: 読み上げるテキスト
            language: 言語コード
            voice: 音声ID（指定しない場合はデフォルト）

        Returns:
            合成結果
        """
        ...

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice: str | None = None,
    ) -> AsyncIterator[bytes]:
        """ストリーミング音声合成

        長いテキストを段階的に音声化し、
        低遅延で再生を開始できるようにします。

        Args:
            text: 読み上げるテキスト
            language: 言語コード
            voice: 音声ID

        Yields:
            音声データのチャンク
        """
        ...
```

### 5.2 Azure Speech Services 実装

```python
# packages/@grc/ai/src/grc_ai/speech/azure_speech.py

import azure.cognitiveservices.speech as speechsdk
from typing import AsyncIterator
import asyncio


class AzureSpeechProvider:
    """Azure Speech Services プロバイダー

    Microsoftの音声認識・合成サービスを使用します。

    特徴:
    - 高精度な日本語認識
    - 自然な日本語音声（Neural Voice）
    - リアルタイムストリーミング
    - カスタム音声モデル対応

    音声一覧 (日本語):
    - ja-JP-NanamiNeural: 女性、標準
    - ja-JP-KeitaNeural: 男性、標準
    - ja-JP-AoiNeural: 女性、若い
    - ja-JP-DaichiNeural: 男性、若い
    """

    def __init__(self, config: SpeechConfig):
        self.config = config

        # Speech SDK設定
        self.speech_config = speechsdk.SpeechConfig(
            subscription=config.azure_speech_key,
            region=config.azure_speech_region,
        )

        # 出力フォーマット設定
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )

    async def transcribe(
        self,
        audio: bytes,
        language: str = "ja-JP",
        format: str = "wav",
    ) -> TranscriptionResult:
        """音声をテキストに変換"""
        # 音声設定
        self.speech_config.speech_recognition_language = language

        # 音声入力ストリームを作成
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

        # 認識器を作成
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        # 音声データを送信
        audio_stream.write(audio)
        audio_stream.close()

        # 認識を実行
        result = await asyncio.to_thread(recognizer.recognize_once)

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return TranscriptionResult(
                text=result.text,
                confidence=1.0,  # Azure は信頼度を返さない
                language=language,
                is_final=True,
            )
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=language,
                is_final=True,
            )
        else:
            raise SpeechServiceError(
                code=ErrorCode.SPEECH_RECOGNITION_FAILED,
                message=f"Recognition failed: {result.reason}",
            )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
    ) -> AsyncIterator[TranscriptionResult]:
        """リアルタイム音声認識

        マイクからの音声をリアルタイムでテキスト化します。
        中間結果も返すため、ユーザーに素早いフィードバックを提供できます。
        """
        self.speech_config.speech_recognition_language = language

        # プッシュストリームを作成
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config,
        )

        # 結果を格納するキュー
        result_queue = asyncio.Queue()

        # コールバック関数
        def on_recognized(evt):
            asyncio.run_coroutine_threadsafe(
                result_queue.put(TranscriptionResult(
                    text=evt.result.text,
                    confidence=1.0,
                    language=language,
                    is_final=True,
                )),
                asyncio.get_event_loop(),
            )

        def on_recognizing(evt):
            asyncio.run_coroutine_threadsafe(
                result_queue.put(TranscriptionResult(
                    text=evt.result.text,
                    confidence=0.5,
                    language=language,
                    is_final=False,
                )),
                asyncio.get_event_loop(),
            )

        recognizer.recognized.connect(on_recognized)
        recognizer.recognizing.connect(on_recognizing)

        # 認識を開始
        recognizer.start_continuous_recognition()

        try:
            # 音声データを送信
            async for chunk in audio_stream:
                push_stream.write(chunk)

                # 結果があれば返す
                while not result_queue.empty():
                    yield await result_queue.get()

            # ストリーム終了
            push_stream.close()

            # 残りの結果を返す
            while not result_queue.empty():
                yield await result_queue.get()

        finally:
            recognizer.stop_continuous_recognition()

    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice: str | None = None,
    ) -> SynthesisResult:
        """テキストを音声に変換"""
        # 音声を設定
        voice_name = voice or self._get_default_voice(language)
        self.speech_config.speech_synthesis_voice_name = voice_name

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None,  # メモリに出力
        )

        result = await asyncio.to_thread(synthesizer.speak_text, text)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return SynthesisResult(
                audio=result.audio_data,
                format="mp3",
                sample_rate=16000,
                duration_ms=len(result.audio_data) // 32,  # 概算
            )
        else:
            raise SpeechServiceError(
                code=ErrorCode.SPEECH_SYNTHESIS_FAILED,
                message=f"Synthesis failed: {result.reason}",
            )

    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice: str | None = None,
    ) -> AsyncIterator[bytes]:
        """ストリーミング音声合成

        長いテキストを段階的に音声化し、
        最初の音声が生成され次第、再生を開始できます。
        """
        voice_name = voice or self._get_default_voice(language)
        self.speech_config.speech_synthesis_voice_name = voice_name

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None,
        )

        # 結果を格納するキュー
        audio_queue = asyncio.Queue()

        def on_audio_chunk(evt):
            asyncio.run_coroutine_threadsafe(
                audio_queue.put(evt.audio_chunk),
                asyncio.get_event_loop(),
            )

        def on_completed(evt):
            asyncio.run_coroutine_threadsafe(
                audio_queue.put(None),  # 終了マーカー
                asyncio.get_event_loop(),
            )

        synthesizer.synthesizing.connect(on_audio_chunk)
        synthesizer.synthesis_completed.connect(on_completed)

        # 合成を開始
        synthesizer.speak_text_async(text)

        # チャンクを返す
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            yield chunk

    def _get_default_voice(self, language: str) -> str:
        """言語に応じたデフォルト音声を取得"""
        default_voices = {
            "ja-JP": "ja-JP-NanamiNeural",
            "en-US": "en-US-JennyNeural",
            "zh-CN": "zh-CN-XiaoxiaoNeural",
            "ko-KR": "ko-KR-SunHiNeural",
        }
        return default_voices.get(language, "ja-JP-NanamiNeural")
```

---

## 6. 翻訳サービス

### 6.1 翻訳サービスインターフェース

```python
# packages/@grc/ai/src/grc_ai/translation/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranslationResult:
    """翻訳結果

    Attributes:
        text: 翻訳されたテキスト
        source_language: 検出された元言語
        target_language: 翻訳先言語
        confidence: 言語検出の信頼度
    """
    text: str
    source_language: str
    target_language: str
    confidence: float = 1.0


class TranslationProvider(ABC):
    """翻訳サービスの抽象インターフェース"""

    @abstractmethod
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> TranslationResult:
        """テキストを翻訳

        Args:
            text: 翻訳元テキスト
            target_language: 翻訳先言語コード
            source_language: 翻訳元言語（Noneの場合は自動検出）

        Returns:
            翻訳結果
        """
        ...

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """言語を検出

        Args:
            text: 検出対象のテキスト

        Returns:
            言語コード (ja, en, zh, etc.)
        """
        ...
```

---

## 7. レイテンシ最適化

### 7.1 レイテンシクラス

```python
from enum import Enum


class LatencyClass(str, Enum):
    """レイテンシクラスの定義

    リアルタイム対話では、TTFT（Time to First Token）が重要です。
    ユーザーが待っていると感じないためには、200ms以内に応答を
    開始する必要があります。

    ULTRA_FAST: 音声対話に最適。200ms以内にレスポンス開始
    FAST: テキストチャットに適切。500ms以内にレスポンス開始
    STANDARD: バッチ処理向け。1秒以内にレスポンス開始
    SLOW: 非同期処理向け。即時性は不要
    """
    ULTRA_FAST = "ultra_fast"  # TTFT < 200ms
    FAST = "fast"              # TTFT 200-500ms
    STANDARD = "standard"      # TTFT 500ms-1s
    SLOW = "slow"              # TTFT > 1s


# モデルとレイテンシクラスのマッピング
MODEL_LATENCY_CLASSES = {
    # Azure OpenAI
    "gpt-5-nano": LatencyClass.ULTRA_FAST,
    "gpt-4o-mini": LatencyClass.ULTRA_FAST,
    "gpt-5.2": LatencyClass.FAST,
    "gpt-4o": LatencyClass.FAST,

    # AWS Bedrock
    "anthropic.claude-4.6-haiku": LatencyClass.ULTRA_FAST,
    "anthropic.claude-sonnet-4.6": LatencyClass.FAST,
    "anthropic.claude-opus-4.5": LatencyClass.STANDARD,
    "amazon.nova-lite": LatencyClass.ULTRA_FAST,

    # GCP Vertex AI
    "gemini-3.0-flash": LatencyClass.ULTRA_FAST,
    "gemini-3.0-pro": LatencyClass.FAST,
    "gemini-3.0-ultra": LatencyClass.STANDARD,
}


def get_model_for_latency(
    latency_class: LatencyClass,
    provider: AIProviderType,
) -> str:
    """レイテンシ要件に合ったモデルを選択

    使用例:
        # 音声対話には高速モデルを使用
        model = get_model_for_latency(LatencyClass.ULTRA_FAST, AIProviderType.AZURE_OPENAI)
        # -> "gpt-5-nano"
    """
    models_by_provider = {
        AIProviderType.AZURE_OPENAI: {
            LatencyClass.ULTRA_FAST: "gpt-5-nano",
            LatencyClass.FAST: "gpt-5.2",
            LatencyClass.STANDARD: "gpt-4o",
        },
        AIProviderType.AWS_BEDROCK: {
            LatencyClass.ULTRA_FAST: "anthropic.claude-4.6-haiku",
            LatencyClass.FAST: "anthropic.claude-sonnet-4.6",
            LatencyClass.STANDARD: "anthropic.claude-opus-4.5",
        },
        AIProviderType.GCP_VERTEX: {
            LatencyClass.ULTRA_FAST: "gemini-3.0-flash",
            LatencyClass.FAST: "gemini-3.0-pro",
            LatencyClass.STANDARD: "gemini-3.0-ultra",
        },
    }

    return models_by_provider[provider][latency_class]
```

### 7.2 最適化テクニック

```python
# レイテンシ最適化のベストプラクティス

class OptimizedDialogueService:
    """最適化されたインタビュー対話サービス"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def get_response(
        self,
        messages: list[Message],
        require_low_latency: bool = True,
    ) -> AsyncIterator[str]:
        """最適化された応答取得

        低レイテンシが必要な場合:
        1. ストリーミングを使用
        2. max_tokensを制限
        3. temperatureを下げる
        """
        kwargs = {}

        if require_low_latency:
            # 低レイテンシ設定
            kwargs["max_tokens"] = 256  # 短い応答
            kwargs["temperature"] = 0.5  # 決定的な応答

        async for chunk in self.provider.stream_chat(messages, **kwargs):
            yield chunk.content

    async def get_follow_up_question(
        self,
        interview_context: str,
        last_answer: str,
    ) -> str:
        """フォローアップ質問を生成

        フォローアップ質問はリアルタイム性が重要なため、
        高速モデルと短いプロンプトを使用
        """
        # 簡潔なプロンプト
        messages = [
            Message(
                role="system",
                content="インタビュアーとして、次の質問を1文で生成してください。",
            ),
            Message(
                role="user",
                content=f"回答: {last_answer[:200]}",  # 回答を短縮
            ),
        ]

        response = await self.provider.chat(
            messages,
            max_tokens=100,  # 質問は短い
            temperature=0.7,
        )

        return response.content
```

---

## 8. モデル選択ガイド

### 8.1 ユースケース別の推奨モデル

| ユースケース | 推奨モデル | 理由 |
|-------------|-----------|------|
| 音声対話 | gpt-5-nano / claude-haiku / gemini-flash | 低レイテンシ必須 |
| テキストチャット | gpt-5.2 / claude-sonnet / gemini-pro | バランス重視 |
| レポート生成 | gpt-4o / claude-opus / gemini-ultra | 品質重視 |
| 翻訳 | 専用翻訳API推奨 | コスト効率 |
| 要約 | gpt-5.2 / claude-sonnet | 品質とコストのバランス |

### 8.2 コスト比較

```
┌─────────────────────────────────────────────────────────────────┐
│                    コスト比較（1M トークンあたり）               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Azure OpenAI                                                   │
│  ├── gpt-5-nano     : $0.15 / $0.60  (入力/出力)               │
│  ├── gpt-5.2        : $2.50 / $10.00                            │
│  └── gpt-4o         : $5.00 / $15.00                            │
│                                                                 │
│  AWS Bedrock (Claude)                                           │
│  ├── claude-haiku   : $0.25 / $1.25                             │
│  ├── claude-sonnet  : $3.00 / $15.00                            │
│  └── claude-opus    : $15.00 / $75.00                           │
│                                                                 │
│  GCP Vertex AI (Gemini)                                         │
│  ├── gemini-flash   : $0.075 / $0.30                            │
│  ├── gemini-pro     : $1.25 / $5.00                             │
│  └── gemini-ultra   : $10.00 / $30.00                           │
│                                                                 │
│  ※ 2026年2月時点の参考価格                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. プロンプト設計

### 9.1 インタビュー用プロンプト

```python
# packages/@grc/ai/src/grc_ai/dialogue/prompts.py

INTERVIEW_SYSTEM_PROMPT = """あなたは内部監査・コンプライアンス調査のプロフェッショナルインタビュアーです。

## あなたの役割
- 被インタビュー者から業務プロセスや統制活動について情報を収集する
- 事実を客観的に聞き出す
- 深掘り質問で詳細を引き出す

## インタビューの原則
1. オープンクエスチョンを使用する
2. 誘導的な質問は避ける
3. 1度に1つの質問のみ行う
4. 被インタビュー者の発言を言い換えて確認する
5. 沈黙を恐れず、考える時間を与える

## 禁止事項
- 判断や評価を伝えない
- 他者の発言を引用しない
- 結論を先に述べない

## フォローアップ質問のパターン
- 「具体的には、どのような...?」
- 「それは、いつ頃から...?」
- 「その場合、どなたが...?」
- 「例えば、どのような状況で...?」

## 回答の形式
質問のみを出力してください。説明や前置きは不要です。
"""


SUMMARY_SYSTEM_PROMPT = """あなたはインタビュー記録を要約する専門家です。

## 要約の原則
1. 客観的な事実のみを記載
2. 時系列を維持
3. 重要なポイントを優先
4. 専門用語はそのまま使用

## 出力フォーマット
### 概要
（2-3文で全体像を記述）

### 主要な発見事項
- （箇条書きで記載）

### 詳細
（必要に応じてセクション分け）

### 確認が必要な事項
- （不明点や矛盾点があれば記載）
"""
```

### 9.2 プロンプトテンプレート

```python
from string import Template


class PromptTemplates:
    """プロンプトテンプレート集"""

    @staticmethod
    def interview_start(
        topic: str,
        template_questions: list[str],
    ) -> str:
        """インタビュー開始時のプロンプト"""
        questions_text = "\n".join(
            f"- {q}" for q in template_questions
        )

        return Template("""
## インタビュートピック
$topic

## 予定している質問
$questions

まず、自己紹介と本日のインタビューの目的を説明してから、
最初の質問を行ってください。
""").substitute(topic=topic, questions=questions_text)

    @staticmethod
    def follow_up(
        last_answer: str,
        remaining_topics: list[str],
    ) -> str:
        """フォローアップ質問生成用プロンプト"""
        topics_text = "\n".join(f"- {t}" for t in remaining_topics)

        return Template("""
## 直前の回答
$answer

## 未確認のトピック
$topics

回答内容に基づいて、適切なフォローアップ質問を生成してください。
未確認のトピックがあれば、自然な流れでそちらに移行してください。
""").substitute(answer=last_answer, topics=topics_text)

    @staticmethod
    def generate_report(
        transcript: str,
        report_type: str,
    ) -> str:
        """レポート生成用プロンプト"""
        return Template("""
## インタビュー文字起こし
$transcript

## レポートタイプ
$report_type

上記の文字起こしに基づいて、指定されたタイプのレポートを生成してください。
""").substitute(transcript=transcript, report_type=report_type)
```

---

## 10. コスト最適化

### 10.1 コスト最適化戦略

```python
class CostOptimizedProvider:
    """コスト最適化されたAIプロバイダー

    使い分け戦略:
    1. 簡単なタスク → 安価なモデル
    2. 複雑なタスク → 高性能モデル
    3. キャッシュ活用 → API呼び出し削減
    """

    def __init__(
        self,
        fast_provider: AIProvider,  # gpt-5-nano等
        smart_provider: AIProvider,  # gpt-5.2等
        cache: RedisCache,
    ):
        self.fast_provider = fast_provider
        self.smart_provider = smart_provider
        self.cache = cache

    async def chat(
        self,
        messages: list[Message],
        complexity: str = "auto",  # simple / complex / auto
        **kwargs,
    ) -> ChatResponse:
        """コスト最適化されたチャット

        Args:
            messages: 会話履歴
            complexity: タスクの複雑さ
        """
        # キャッシュチェック
        cache_key = self._generate_cache_key(messages)
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # 複雑さを判定
        if complexity == "auto":
            complexity = self._assess_complexity(messages)

        # プロバイダーを選択
        if complexity == "simple":
            response = await self.fast_provider.chat(messages, **kwargs)
        else:
            response = await self.smart_provider.chat(messages, **kwargs)

        # キャッシュに保存（5分間）
        await self.cache.set(cache_key, response, ttl=300)

        return response

    def _assess_complexity(self, messages: list[Message]) -> str:
        """タスクの複雑さを判定

        ヒューリスティクス:
        - 短い入力 → simple
        - 長い入力 → complex
        - 専門用語が多い → complex
        - 計算・論理的推論 → complex
        """
        last_message = messages[-1].content

        # 文字数で判定
        if len(last_message) < 100:
            return "simple"

        # キーワードで判定
        complex_keywords = ["分析", "比較", "計算", "なぜ", "評価"]
        if any(kw in last_message for kw in complex_keywords):
            return "complex"

        return "simple"

    def _generate_cache_key(self, messages: list[Message]) -> str:
        """キャッシュキーを生成"""
        import hashlib
        content = "".join(m.content for m in messages)
        return hashlib.sha256(content.encode()).hexdigest()[:32]
```

### 10.2 バッチ処理

```python
async def batch_embed(
    texts: list[str],
    provider: AIProvider,
    batch_size: int = 100,
) -> list[list[float]]:
    """バッチ埋め込み処理

    大量のテキストを埋め込む際は、バッチ処理でAPI呼び出しを削減。

    Args:
        texts: 埋め込み対象テキストのリスト
        provider: AIプロバイダー
        batch_size: バッチサイズ

    Returns:
        埋め込みベクトルのリスト
    """
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        # バッチで埋め込み
        batch_embeddings = await asyncio.gather(*[
            provider.embed(text) for text in batch
        ])

        embeddings.extend(batch_embeddings)

    return embeddings
```

---

## 11. エラー処理とフォールバック

### 11.1 フォールバック戦略

```python
class ResilientAIProvider:
    """耐障害性のあるAIプロバイダー

    プライマリプロバイダーが失敗した場合、
    フォールバックプロバイダーに切り替えます。
    """

    def __init__(
        self,
        primary: AIProvider,
        fallback: AIProvider,
        circuit_breaker: CircuitBreaker,
    ):
        self.primary = primary
        self.fallback = fallback
        self.circuit_breaker = circuit_breaker

    async def chat(
        self,
        messages: list[Message],
        **kwargs,
    ) -> ChatResponse:
        """耐障害性のあるチャット"""
        try:
            # サーキットブレーカー経由でプライマリを呼び出し
            return await self.circuit_breaker.call(
                lambda: self.primary.chat(messages, **kwargs)
            )

        except CircuitOpenError:
            # サーキットが開いている → フォールバック
            logger.warning(
                f"Primary provider {self.primary.provider_name} circuit open, "
                f"falling back to {self.fallback.provider_name}"
            )
            return await self.fallback.chat(messages, **kwargs)

        except AIProviderError as e:
            if e.is_retryable:
                # リトライ可能 → フォールバック
                logger.warning(
                    f"Primary provider error, falling back: {e}"
                )
                return await self.fallback.chat(messages, **kwargs)
            raise
```

### 11.2 グレースフルデグラデーション

```python
class GracefulDegradationService:
    """段階的縮退を行うサービス

    1. 高性能モデル → 失敗
    2. 標準モデル → 失敗
    3. キャッシュされた類似回答 → 失敗
    4. 定型文
    """

    async def get_response(
        self,
        messages: list[Message],
    ) -> str:
        """段階的縮退でレスポンスを取得"""
        errors = []

        # 1. 高性能モデルを試行
        try:
            response = await self.smart_provider.chat(messages)
            return response.content
        except AIProviderError as e:
            errors.append(e)
            logger.warning(f"Smart provider failed: {e}")

        # 2. 標準モデルを試行
        try:
            response = await self.fast_provider.chat(messages)
            return response.content
        except AIProviderError as e:
            errors.append(e)
            logger.warning(f"Fast provider failed: {e}")

        # 3. キャッシュを検索
        similar_response = await self._find_similar_cached_response(messages)
        if similar_response:
            logger.info("Using cached similar response")
            return similar_response

        # 4. 最終手段: 定型文
        logger.error(
            f"All providers failed, using fallback message. Errors: {errors}"
        )
        return (
            "申し訳ありません。現在システムが混み合っております。"
            "しばらくしてから再度お試しください。"
        )
```

---

## 12. テスト方法

### 12.1 ユニットテスト

```python
# tests/test_ai_providers.py

import pytest
from unittest.mock import AsyncMock, patch


class TestAzureOpenAIProvider:
    """Azure OpenAI プロバイダーのテスト"""

    @pytest.fixture
    def provider(self):
        config = AIProviderConfig(
            provider=AIProviderType.AZURE_OPENAI,
            model="gpt-5.2",
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test-key",
            azure_deployment="gpt-52",
        )
        return AzureOpenAIProvider(config)

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        """正常なチャットレスポンスのテスト"""
        messages = [
            Message(role="user", content="Hello")
        ]

        # モックのレスポンス
        mock_response = AsyncMock()
        mock_response.choices = [
            AsyncMock(
                message=AsyncMock(content="Hello!"),
                finish_reason="stop"
            )
        ]
        mock_response.model = "gpt-5.2"
        mock_response.usage = AsyncMock(
            prompt_tokens=10,
            completion_tokens=5
        )

        with patch.object(
            provider.client.chat.completions,
            "create",
            return_value=mock_response
        ):
            response = await provider.chat(messages)

        assert response.content == "Hello!"
        assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_chat_rate_limit(self, provider):
        """レート制限エラーのテスト"""
        from openai import RateLimitError

        with patch.object(
            provider.client.chat.completions,
            "create",
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=AsyncMock(headers={"Retry-After": "60"}),
                body={}
            )
        ):
            with pytest.raises(AIProviderError) as exc_info:
                await provider.chat([Message(role="user", content="test")])

            assert exc_info.value.code == ErrorCode.AI_RATE_LIMIT
            assert exc_info.value.is_retryable
```

### 12.2 統合テスト

```python
# tests/integration/test_ai_integration.py

import pytest
import os


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="Azure OpenAI credentials not set"
)
class TestAzureOpenAIIntegration:
    """Azure OpenAI 統合テスト"""

    @pytest.fixture
    def provider(self):
        config = AIProviderConfig(
            provider=AIProviderType.AZURE_OPENAI,
            model="gpt-5.2",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        )
        return AzureOpenAIProvider(config)

    @pytest.mark.asyncio
    async def test_real_chat(self, provider):
        """実際のAPIを使用したチャットテスト"""
        messages = [
            Message(role="user", content="What is 2+2?")
        ]

        response = await provider.chat(messages, max_tokens=50)

        assert "4" in response.content
        assert response.usage["prompt_tokens"] > 0
        assert response.usage["completion_tokens"] > 0

    @pytest.mark.asyncio
    async def test_real_stream_chat(self, provider):
        """実際のAPIを使用したストリーミングテスト"""
        messages = [
            Message(role="user", content="Count from 1 to 5")
        ]

        chunks = []
        async for chunk in provider.stream_chat(messages, max_tokens=50):
            chunks.append(chunk.content)

        full_response = "".join(chunks)
        assert "1" in full_response
        assert "5" in full_response
```

---

## 付録

### A. 環境変数一覧

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_API_VERSION=2024-12-01
AZURE_OPENAI_DEPLOYMENT_GPT52=gpt-52

# AWS Bedrock
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=ap-northeast-1

# GCP Vertex AI
GCP_PROJECT_ID=xxx
GCP_LOCATION=asia-northeast1
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp.json

# 音声サービス
AZURE_SPEECH_KEY=xxx
AZURE_SPEECH_REGION=japaneast
```

### B. 関連ドキュメント

- [ログ管理仕様書](./LOGGING.md)
- [エラー処理仕様書](./ERROR_HANDLING.md)
- [セキュリティ仕様書](./SECURITY.md)
- [インフラストラクチャ仕様書](./INFRASTRUCTURE.md)
