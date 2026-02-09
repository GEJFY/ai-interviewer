"""LLM Model configurations and selection.

Provides model definitions for multiple providers with cost/performance tiers.
Updated for 2026 with the latest available models including GPT-5.2, Claude Sonnet 4.6 Opus, and Gemini 3.0.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ModelTier(str, Enum):
    """Model performance/cost tiers."""

    ECONOMY = "economy"  # Lowest cost, good for simple tasks
    STANDARD = "standard"  # Balanced cost/performance
    PREMIUM = "premium"  # High performance, higher cost
    FLAGSHIP = "flagship"  # Best performance, highest cost


class ModelCapability(str, Enum):
    """Model capabilities."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    AUDIO = "audio"
    REASONING = "reasoning"  # For o1/o3 style models
    CODE = "code"  # Enhanced code generation
    MULTIMODAL = "multimodal"  # Full multimodal support
    REALTIME = "realtime"  # Optimized for real-time interaction


class LatencyClass(str, Enum):
    """Model latency classification for real-time requirements."""

    ULTRA_FAST = "ultra_fast"  # <200ms TTFT, ideal for real-time dialogue
    FAST = "fast"  # 200-500ms TTFT, good for interactive use
    STANDARD = "standard"  # 500ms-1s TTFT, acceptable for most tasks
    SLOW = "slow"  # >1s TTFT, better for batch/async processing


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""

    model_id: str
    display_name: str
    provider: str
    tier: ModelTier
    capabilities: list[ModelCapability]
    context_window: int
    max_output_tokens: int
    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    supports_json_mode: bool = True
    supports_streaming: bool = True
    supports_tools: bool = True
    latency_class: LatencyClass = LatencyClass.STANDARD  # Real-time suitability
    description: str = ""


# =============================================================================
# OpenAI Models (Direct API)
# =============================================================================

OPENAI_MODELS = {
    # GPT-5 Series - Latest Flagship (2026)
    "gpt-5.2": ModelConfig(
        model_id="gpt-5.2",
        display_name="GPT-5.2",
        provider="openai",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=500000,
        max_output_tokens=32768,
        input_cost_per_1k=0.02,
        output_cost_per_1k=0.08,
        latency_class=LatencyClass.STANDARD,  # Not ideal for real-time
        description="Most advanced GPT model with full multimodal and reasoning",
    ),
    "gpt-5-nano": ModelConfig(
        model_id="gpt-5-nano",
        display_name="GPT-5 Nano",
        provider="openai",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=16384,
        input_cost_per_1k=0.0001,
        output_cost_per_1k=0.0004,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time dialogue
        description="Ultra-efficient GPT-5 for real-time dialogue and high-volume tasks",
    ),
    # GPT-4o Series - Still widely used
    "gpt-4o": ModelConfig(
        model_id="gpt-4o",
        display_name="GPT-4o",
        provider="openai",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=16384,
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01,
        latency_class=LatencyClass.FAST,  # Good for interactive use
        description="Proven GPT-4 model with vision support, good for real-time",
    ),
    "gpt-4o-mini": ModelConfig(
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        provider="openai",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=16384,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time
        description="Ultra-fast GPT-4o for real-time dialogue",
    ),
    # GPT-5 Mini - Cost-effective (2026)
    "gpt-5-mini": ModelConfig(
        model_id="gpt-5-mini",
        display_name="GPT-5 Mini",
        provider="openai",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=256000,
        max_output_tokens=16384,
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.002,
        latency_class=LatencyClass.FAST,
        description="Balanced GPT-5 for cost-effective interactive use",
    ),
    # o-Series - Reasoning models (NOT for real-time - use for analysis)
    "o4-mini": ModelConfig(
        model_id="o4-mini",
        display_name="o4 Mini",
        provider="openai",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE],
        context_window=200000,
        max_output_tokens=100000,
        input_cost_per_1k=0.0011,
        output_cost_per_1k=0.0044,
        supports_streaming=False,
        latency_class=LatencyClass.SLOW,
        description="Cost-effective reasoning model (not for real-time)",
    ),
    "o3": ModelConfig(
        model_id="o3",
        display_name="o3",
        provider="openai",
        tier=ModelTier.FLAGSHIP,
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE],
        context_window=200000,
        max_output_tokens=100000,
        input_cost_per_1k=0.02,
        output_cost_per_1k=0.08,
        supports_streaming=False,
        latency_class=LatencyClass.SLOW,  # NOT for real-time - use for post-analysis
        description="Deep reasoning model for complex analysis (not real-time)",
    ),
    "o3-mini": ModelConfig(
        model_id="o3-mini",
        display_name="o3 Mini",
        provider="openai",
        tier=ModelTier.PREMIUM,
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
        context_window=200000,
        max_output_tokens=100000,
        input_cost_per_1k=0.0011,
        output_cost_per_1k=0.0044,
        supports_streaming=False,
        latency_class=LatencyClass.SLOW,  # NOT for real-time
        description="Efficient reasoning model (not for real-time)",
    ),
    # Embedding
    "text-embedding-3-large": ModelConfig(
        model_id="text-embedding-3-large",
        display_name="Embedding 3 Large",
        provider="openai",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.EMBEDDING],
        context_window=8191,
        max_output_tokens=0,
        input_cost_per_1k=0.00013,
        output_cost_per_1k=0,
        supports_json_mode=False,
        supports_streaming=False,
        supports_tools=False,
        description="Best embedding model for semantic search",
    ),
    "text-embedding-3-small": ModelConfig(
        model_id="text-embedding-3-small",
        display_name="Embedding 3 Small",
        provider="openai",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.EMBEDDING],
        context_window=8191,
        max_output_tokens=0,
        input_cost_per_1k=0.00002,
        output_cost_per_1k=0,
        supports_json_mode=False,
        supports_streaming=False,
        supports_tools=False,
        description="Cost-effective embedding model",
    ),
}

# =============================================================================
# Anthropic Claude Models
# =============================================================================

ANTHROPIC_MODELS = {
    # Claude Sonnet 4.6 Opus - Latest Flagship (2026)
    "claude-sonnet-4.6-opus": ModelConfig(
        model_id="claude-sonnet-4.6-opus",
        display_name="Claude Sonnet 4.6 Opus",
        provider="anthropic",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=500000,
        max_output_tokens=32768,
        input_cost_per_1k=0.018,
        output_cost_per_1k=0.09,
        latency_class=LatencyClass.SLOW,  # NOT for real-time - use for post-analysis
        description="Most powerful Claude model with deep reasoning (not real-time)",
    ),
    "claude-4.6-sonnet": ModelConfig(
        model_id="claude-4.6-sonnet",
        display_name="Claude 4.6 Sonnet",
        provider="anthropic",
        tier=ModelTier.PREMIUM,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.CODE,
            ModelCapability.REALTIME,
        ],
        context_window=400000,
        max_output_tokens=16384,
        input_cost_per_1k=0.004,
        output_cost_per_1k=0.02,
        latency_class=LatencyClass.FAST,  # Good for interactive dialogue
        description="Balanced Claude with good latency for interactive use",
    ),
    "claude-4.6-haiku": ModelConfig(
        model_id="claude-4.6-haiku",
        display_name="Claude 4.6 Haiku",
        provider="anthropic",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.002,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time dialogue
        description="Ultra-fast Claude for real-time interview dialogue",
    ),
    # Claude 3.5 Series - Still supported
    "claude-3-5-sonnet-20241022": ModelConfig(
        model_id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        provider="anthropic",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        latency_class=LatencyClass.FAST,  # Good for real-time
        description="Reliable Claude 3.5 with good real-time performance",
    ),
}

# =============================================================================
# Azure OpenAI / Azure AI Foundry Models
# =============================================================================

AZURE_OPENAI_MODELS = {
    # GPT-5 Series on Azure AI Foundry
    "azure-gpt-5.2": ModelConfig(
        model_id="gpt-5.2",
        display_name="Azure GPT-5.2",
        provider="azure_openai",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=500000,
        max_output_tokens=32768,
        input_cost_per_1k=0.02,
        output_cost_per_1k=0.08,
        latency_class=LatencyClass.STANDARD,  # Not ideal for real-time
        description="GPT-5.2 on Azure AI Foundry (use for analysis, not real-time)",
    ),
    "azure-gpt-5-nano": ModelConfig(
        model_id="gpt-5-nano",
        display_name="Azure GPT-5 Nano",
        provider="azure_openai",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=16384,
        input_cost_per_1k=0.0001,
        output_cost_per_1k=0.0004,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time dialogue
        description="Ultra-fast GPT-5 Nano on Azure for real-time interview",
    ),
    # Claude via Azure AI Foundry
    "azure-claude-sonnet-4.6-opus": ModelConfig(
        model_id="claude-sonnet-4.6-opus",
        display_name="Azure Claude Sonnet 4.6 Opus",
        provider="azure_openai",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.REASONING,
            ModelCapability.CODE,
        ],
        context_window=500000,
        max_output_tokens=32768,
        input_cost_per_1k=0.018,
        output_cost_per_1k=0.09,
        latency_class=LatencyClass.SLOW,  # NOT for real-time - use for analysis
        description="Claude Opus via Azure AI Foundry (not for real-time)",
    ),
    "azure-claude-4.6-sonnet": ModelConfig(
        model_id="claude-4.6-sonnet",
        display_name="Azure Claude 4.6 Sonnet",
        provider="azure_openai",
        tier=ModelTier.PREMIUM,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=400000,
        max_output_tokens=16384,
        input_cost_per_1k=0.004,
        output_cost_per_1k=0.02,
        latency_class=LatencyClass.FAST,  # Good for interactive dialogue
        description="Claude 4.6 Sonnet via Azure AI Foundry (good for dialogue)",
    ),
    # GPT-4o on Azure
    "azure-gpt-4o": ModelConfig(
        model_id="gpt-4o",
        display_name="Azure GPT-4o",
        provider="azure_openai",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=16384,
        input_cost_per_1k=0.0025,
        output_cost_per_1k=0.01,
        latency_class=LatencyClass.FAST,  # Good for real-time
        description="GPT-4o on Azure with good real-time performance",
    ),
}

# =============================================================================
# AWS Bedrock Models
# =============================================================================

AWS_BEDROCK_MODELS = {
    # Claude Sonnet 4.6 Opus on Bedrock - Latest
    "bedrock-claude-sonnet-4.6-opus": ModelConfig(
        model_id="anthropic.claude-sonnet-4.6-opus-v1:0",
        display_name="Claude Sonnet 4.6 Opus (Bedrock)",
        provider="aws_bedrock",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=500000,
        max_output_tokens=32768,
        input_cost_per_1k=0.018,
        output_cost_per_1k=0.09,
        latency_class=LatencyClass.SLOW,  # NOT for real-time - use for analysis
        description="Claude Opus on Bedrock for deep analysis (not real-time)",
    ),
    "bedrock-claude-4.6-sonnet": ModelConfig(
        model_id="anthropic.claude-4.6-sonnet-v1:0",
        display_name="Claude 4.6 Sonnet (Bedrock)",
        provider="aws_bedrock",
        tier=ModelTier.PREMIUM,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=400000,
        max_output_tokens=16384,
        input_cost_per_1k=0.004,
        output_cost_per_1k=0.02,
        latency_class=LatencyClass.FAST,  # Good for interactive dialogue
        description="Claude 4.6 Sonnet via Bedrock (good for dialogue)",
    ),
    "bedrock-claude-4.6-haiku": ModelConfig(
        model_id="anthropic.claude-4.6-haiku-v1:0",
        display_name="Claude 4.6 Haiku (Bedrock)",
        provider="aws_bedrock",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0005,
        output_cost_per_1k=0.002,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time dialogue
        description="Ultra-fast Claude Haiku for real-time interview",
    ),
    # Claude 3.5 on Bedrock - Still supported
    "bedrock-claude-3-5-sonnet": ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        display_name="Claude 3.5 Sonnet (Bedrock)",
        provider="aws_bedrock",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=200000,
        max_output_tokens=8192,
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        latency_class=LatencyClass.FAST,  # Good for real-time
        description="Claude 3.5 Sonnet with good real-time performance",
    ),
    # Amazon Nova Series
    "amazon-nova-premier": ModelConfig(
        model_id="amazon.nova-premier-v1:0",
        display_name="Amazon Nova Premier",
        provider="aws_bedrock",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.REASONING,
            ModelCapability.MULTIMODAL,
        ],
        context_window=500000,
        max_output_tokens=16384,
        input_cost_per_1k=0.012,
        output_cost_per_1k=0.048,
        latency_class=LatencyClass.STANDARD,  # Not ideal for real-time
        description="Amazon's flagship model (use for analysis)",
    ),
    "amazon-nova-pro": ModelConfig(
        model_id="amazon.nova-pro-v1:0",
        display_name="Amazon Nova Pro",
        provider="aws_bedrock",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=300000,
        max_output_tokens=5000,
        input_cost_per_1k=0.0008,
        output_cost_per_1k=0.0032,
        latency_class=LatencyClass.FAST,  # Good for interactive use
        description="Amazon Nova Pro with good real-time performance",
    ),
    "amazon-nova-lite": ModelConfig(
        model_id="amazon.nova-lite-v1:0",
        display_name="Amazon Nova Lite",
        provider="aws_bedrock",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=300000,
        max_output_tokens=5000,
        input_cost_per_1k=0.00006,
        output_cost_per_1k=0.00024,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time
        description="Ultra-fast Nova Lite for real-time dialogue",
    ),
    # Amazon Nova Micro - Ultra-low cost
    "amazon-nova-micro": ModelConfig(
        model_id="amazon.nova-micro-v1:0",
        display_name="Amazon Nova Micro",
        provider="aws_bedrock",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=5000,
        input_cost_per_1k=0.000035,
        output_cost_per_1k=0.00014,
        latency_class=LatencyClass.ULTRA_FAST,
        description="Ultra-low cost text-only model for simple tasks",
    ),
    # Llama Series
    "meta-llama-4-70b": ModelConfig(
        model_id="meta.llama4-70b-instruct-v1:0",
        display_name="Llama 4 70B (Bedrock)",
        provider="aws_bedrock",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=8192,
        input_cost_per_1k=0.00099,
        output_cost_per_1k=0.00099,
        latency_class=LatencyClass.FAST,  # Good for interactive use
        description="Llama 4 on Bedrock with good latency",
    ),
}

# =============================================================================
# GCP Vertex AI Models
# =============================================================================

GCP_VERTEX_MODELS = {
    # Gemini 3.0 Series - Latest (2026)
    "gemini-3.0-pro-preview": ModelConfig(
        model_id="gemini-3.0-pro-preview",
        display_name="Gemini 3.0 Pro Preview",
        provider="gcp_vertex",
        tier=ModelTier.FLAGSHIP,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=2000000,
        max_output_tokens=32768,
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.06,
        latency_class=LatencyClass.STANDARD,  # Not ideal for real-time
        description="Gemini 3.0 Pro with 2M context (use for analysis)",
    ),
    "gemini-3.0-flash-preview": ModelConfig(
        model_id="gemini-3.0-flash-preview",
        display_name="Gemini 3.0 Flash Preview",
        provider="gcp_vertex",
        tier=ModelTier.PREMIUM,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
            ModelCapability.REALTIME,
        ],
        context_window=1000000,
        max_output_tokens=16384,
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.004,
        latency_class=LatencyClass.FAST,  # Good for interactive dialogue
        description="Fast Gemini 3.0 Flash for real-time dialogue",
    ),
    "gemini-3.0-flash-lite": ModelConfig(
        model_id="gemini-3.0-flash-lite",
        display_name="Gemini 3.0 Flash Lite",
        provider="gcp_vertex",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.CODE, ModelCapability.REALTIME],
        context_window=500000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0001,
        output_cost_per_1k=0.0004,
        latency_class=LatencyClass.ULTRA_FAST,  # Excellent for real-time
        description="Ultra-fast Gemini for real-time interview",
    ),
    # Gemini 2.5 Series - GA (2025-2026)
    "gemini-2.5-pro": ModelConfig(
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        provider="gcp_vertex",
        tier=ModelTier.PREMIUM,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.REASONING,
            ModelCapability.CODE,
            ModelCapability.MULTIMODAL,
        ],
        context_window=1000000,
        max_output_tokens=65536,
        input_cost_per_1k=0.00125,
        output_cost_per_1k=0.01,
        latency_class=LatencyClass.STANDARD,
        description="GA version Gemini 2.5 Pro with thinking capabilities",
    ),
    "gemini-2.5-flash": ModelConfig(
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        provider="gcp_vertex",
        tier=ModelTier.STANDARD,
        capabilities=[
            ModelCapability.CHAT,
            ModelCapability.VISION,
            ModelCapability.AUDIO,
            ModelCapability.CODE,
            ModelCapability.REALTIME,
        ],
        context_window=1000000,
        max_output_tokens=65536,
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
        latency_class=LatencyClass.FAST,
        description="GA version fast and cost-effective with thinking",
    ),
    "gemini-2.5-flash-lite": ModelConfig(
        model_id="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash Lite",
        provider="gcp_vertex",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=1000000,
        max_output_tokens=65536,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.ULTRA_FAST,
        description="Ultra-fast and free GA model for high-volume tasks",
    ),
    # Gemini 2.0 Series - Still widely used
    "gemini-2.0-flash": ModelConfig(
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        provider="gcp_vertex",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.AUDIO, ModelCapability.REALTIME],
        context_window=1000000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0,  # Free tier available
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.FAST,  # Good for real-time
        description="Proven Gemini 2.0 with excellent latency",
    ),
    "gemini-2.0-flash-thinking": ModelConfig(
        model_id="gemini-2.0-flash-thinking-exp",
        display_name="Gemini 2.0 Flash Thinking",
        provider="gcp_vertex",
        tier=ModelTier.PREMIUM,
        capabilities=[ModelCapability.CHAT, ModelCapability.REASONING],
        context_window=1000000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.SLOW,  # Reasoning takes time
        description="Reasoning-enhanced Gemini (not for real-time)",
    ),
}

# =============================================================================
# Local LLM Models (Ollama)
# =============================================================================

LOCAL_MODELS = {
    "gemma3-1b": ModelConfig(
        model_id="gemma3:1b",
        display_name="Gemma 3 1B",
        provider="local",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.REALTIME],
        context_window=32768,
        max_output_tokens=8192,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.FAST,
        description="Ultra-lightweight local model for testing (1B params)",
    ),
    "gemma3-4b": ModelConfig(
        model_id="gemma3:4b",
        display_name="Gemma 3 4B",
        provider="local",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.VISION, ModelCapability.REALTIME],
        context_window=128000,
        max_output_tokens=8192,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.FAST,
        description="Compact local model with vision support (4B params)",
    ),
    "phi4": ModelConfig(
        model_id="phi4",
        display_name="Phi-4 14B",
        provider="local",
        tier=ModelTier.STANDARD,
        capabilities=[ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.REASONING],
        context_window=16384,
        max_output_tokens=4096,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.STANDARD,
        description="High-quality local model for code and reasoning (14B params)",
    ),
    "llama3.2-1b": ModelConfig(
        model_id="llama3.2:1b",
        display_name="Llama 3.2 1B",
        provider="local",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.CHAT, ModelCapability.REALTIME],
        context_window=131072,
        max_output_tokens=4096,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        latency_class=LatencyClass.ULTRA_FAST,
        description="Ultra-lightweight Llama for rapid testing (1B params)",
    ),
    "nomic-embed-text": ModelConfig(
        model_id="nomic-embed-text",
        display_name="Nomic Embed Text",
        provider="local",
        tier=ModelTier.ECONOMY,
        capabilities=[ModelCapability.EMBEDDING],
        context_window=8192,
        max_output_tokens=0,
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        supports_json_mode=False,
        supports_streaming=False,
        supports_tools=False,
        description="Local embedding model for semantic search",
    ),
}

# =============================================================================
# All Models Registry
# =============================================================================

ALL_MODELS: dict[str, ModelConfig] = {
    **OPENAI_MODELS,
    **ANTHROPIC_MODELS,
    **AZURE_OPENAI_MODELS,
    **AWS_BEDROCK_MODELS,
    **GCP_VERTEX_MODELS,
    **LOCAL_MODELS,
}


def get_model(model_id: str) -> ModelConfig | None:
    """Get model configuration by ID."""
    return ALL_MODELS.get(model_id)


def get_models_by_provider(provider: str) -> list[ModelConfig]:
    """Get all models for a provider."""
    return [m for m in ALL_MODELS.values() if m.provider == provider]


def get_models_by_tier(tier: ModelTier) -> list[ModelConfig]:
    """Get all models in a tier."""
    return [m for m in ALL_MODELS.values() if m.tier == tier]


def get_models_by_capability(capability: ModelCapability) -> list[ModelConfig]:
    """Get all models with a specific capability."""
    return [m for m in ALL_MODELS.values() if capability in m.capabilities]


def get_models_by_latency(latency: LatencyClass) -> list[ModelConfig]:
    """Get all models with a specific latency class."""
    return [m for m in ALL_MODELS.values() if m.latency_class == latency]


def get_realtime_models(provider: str | None = None) -> list[ModelConfig]:
    """Get models suitable for real-time dialogue.

    Returns models with ULTRA_FAST or FAST latency and REALTIME capability.
    These are recommended for interview dialogue where low latency is critical.

    Args:
        provider: Optional filter by provider

    Returns:
        List of models suitable for real-time use, sorted by latency
    """
    suitable_latencies = {LatencyClass.ULTRA_FAST, LatencyClass.FAST}
    models = [
        m for m in ALL_MODELS.values()
        if m.latency_class in suitable_latencies
        and ModelCapability.REALTIME in m.capabilities
        and (provider is None or m.provider == provider)
    ]
    # Sort by latency (ULTRA_FAST first) then by cost
    latency_order = {LatencyClass.ULTRA_FAST: 0, LatencyClass.FAST: 1}
    models.sort(key=lambda m: (latency_order.get(m.latency_class, 2), m.input_cost_per_1k))
    return models


def get_recommended_realtime_model(
    provider: str | None = None,
    tier: ModelTier = ModelTier.ECONOMY,
) -> ModelConfig | None:
    """Get the recommended model for real-time interview dialogue.

    Prioritizes low latency over model capability for responsive dialogue.

    Args:
        provider: Preferred provider (optional)
        tier: Preferred tier (economy for cost, premium for quality)

    Returns:
        Recommended ModelConfig for real-time dialogue
    """
    candidates = get_realtime_models(provider)
    if not candidates:
        return None

    # Filter by tier proximity
    def score(m: ModelConfig) -> tuple:
        tier_order = [ModelTier.ECONOMY, ModelTier.STANDARD, ModelTier.PREMIUM, ModelTier.FLAGSHIP]
        tier_diff = abs(tier_order.index(m.tier) - tier_order.index(tier))
        latency_score = 0 if m.latency_class == LatencyClass.ULTRA_FAST else 1
        return (latency_score, tier_diff, m.input_cost_per_1k)

    candidates.sort(key=score)
    return candidates[0]


def get_recommended_model(
    provider: str | None = None,
    tier: ModelTier = ModelTier.STANDARD,
    capability: ModelCapability = ModelCapability.CHAT,
) -> ModelConfig | None:
    """Get recommended model based on criteria.

    Args:
        provider: Preferred provider (optional)
        tier: Desired performance tier
        capability: Required capability

    Returns:
        Recommended ModelConfig or None
    """
    candidates = [
        m for m in ALL_MODELS.values()
        if capability in m.capabilities
        and (provider is None or m.provider == provider)
    ]

    if not candidates:
        return None

    # Sort by tier proximity and cost
    def score(m: ModelConfig) -> tuple:
        tier_order = [ModelTier.ECONOMY, ModelTier.STANDARD, ModelTier.PREMIUM, ModelTier.FLAGSHIP]
        tier_diff = abs(tier_order.index(m.tier) - tier_order.index(tier))
        return (tier_diff, m.input_cost_per_1k + m.output_cost_per_1k)

    candidates.sort(key=score)
    return candidates[0]


# Default recommendations by use case (2026 Updated)
# IMPORTANT: For real-time interview dialogue, use LOW-LATENCY models!
RECOMMENDED_MODELS = {
    # =========================================================================
    # REAL-TIME DIALOGUE (Low Latency Required)
    # For interview conversations, use ultra-fast/fast models
    # =========================================================================
    "interview_dialogue": "claude-4.6-haiku",  # ULTRA_FAST - Best for real-time interview
    "interview_dialogue_premium": "claude-4.6-sonnet",  # FAST - Higher quality dialogue
    "quick_response": "gpt-5-nano",  # ULTRA_FAST - Ultra-low latency

    # Provider-specific real-time recommendations
    "azure_realtime": "azure-gpt-5-nano",  # ULTRA_FAST on Azure
    "azure_realtime_premium": "azure-claude-4.6-sonnet",  # FAST on Azure
    "aws_realtime": "bedrock-claude-4.6-haiku",  # ULTRA_FAST on Bedrock
    "aws_realtime_premium": "bedrock-claude-4.6-sonnet",  # FAST on Bedrock
    "gcp_realtime": "gemini-3.0-flash-lite",  # ULTRA_FAST on GCP
    "gcp_realtime_premium": "gemini-3.0-flash-preview",  # FAST on GCP

    # =========================================================================
    # POST-INTERVIEW ANALYSIS (Latency Not Critical)
    # For report generation, deep analysis - use flagship models
    # =========================================================================
    "report_generation": "gpt-5.2",  # Strong structured output
    "complex_analysis": "o3",  # Deep reasoning (async/batch)
    "interview_summary": "claude-sonnet-4.6-opus",  # Best quality summary
    "post_analysis": "claude-sonnet-4.6-opus",  # Deep post-interview analysis

    # =========================================================================
    # GENERAL PURPOSE
    # =========================================================================
    "embedding": "text-embedding-3-large",  # Best semantic search
    "cost_effective": "gpt-5-nano",  # Ultra budget-friendly

    # Provider-specific flagship (for analysis, not real-time)
    "azure_flagship": "azure-gpt-5.2",
    "azure_claude": "azure-claude-sonnet-4.6-opus",
    "aws_flagship": "bedrock-claude-sonnet-4.6-opus",
    "gcp_flagship": "gemini-3.0-pro-preview",
    "gcp_fast": "gemini-3.0-flash-preview",

    # Use-case specific
    "multimodal_analysis": "gemini-3.0-pro-preview",  # Best multimodal with 2M context
    "code_generation": "gpt-5.2",  # Strong code capabilities
    "long_document": "gemini-3.0-pro-preview",  # 2M context window

    # Local LLM (開発・テスト用)
    "local_test": "gemma3-1b",  # 最軽量テスト用
    "local_quality": "phi4",  # ローカル高品質
    "local_realtime": "llama3.2-1b",  # ローカル超高速
    "local_embedding": "nomic-embed-text",  # ローカルエンベディング
}


# Provider capability matrix (updated with real-time model recommendations)
PROVIDER_CAPABILITIES = {
    "openai": {
        "latest_model": "gpt-5.2",
        "economy_model": "gpt-5-nano",
        "reasoning_model": "o3",
        "realtime_model": "gpt-5-nano",  # ULTRA_FAST for dialogue
        "realtime_premium": "gpt-4o",  # FAST for quality dialogue
        "supports_vision": True,
        "supports_audio": True,
        "supports_tools": True,
        "supports_realtime": True,
    },
    "anthropic": {
        "latest_model": "claude-sonnet-4.6-opus",
        "economy_model": "claude-4.6-haiku",
        "reasoning_model": "claude-sonnet-4.6-opus",
        "realtime_model": "claude-4.6-haiku",  # ULTRA_FAST for dialogue
        "realtime_premium": "claude-4.6-sonnet",  # FAST for quality dialogue
        "supports_vision": True,
        "supports_audio": False,
        "supports_tools": True,
        "supports_realtime": True,
    },
    "azure_openai": {
        "latest_model": "azure-gpt-5.2",
        "claude_model": "azure-claude-sonnet-4.6-opus",
        "economy_model": "azure-gpt-5-nano",
        "realtime_model": "azure-gpt-5-nano",  # ULTRA_FAST for dialogue
        "realtime_premium": "azure-claude-4.6-sonnet",  # FAST for quality dialogue
        "supports_vision": True,
        "supports_audio": True,
        "supports_tools": True,
        "enterprise_features": True,
        "supports_realtime": True,
    },
    "aws_bedrock": {
        "latest_model": "bedrock-claude-sonnet-4.6-opus",
        "economy_model": "amazon-nova-lite",
        "native_model": "amazon-nova-premier",
        "realtime_model": "bedrock-claude-4.6-haiku",  # ULTRA_FAST for dialogue
        "realtime_premium": "bedrock-claude-4.6-sonnet",  # FAST for quality dialogue
        "realtime_native": "amazon-nova-lite",  # ULTRA_FAST native option
        "supports_vision": True,
        "supports_audio": False,
        "supports_tools": True,
        "supports_realtime": True,
    },
    "gcp_vertex": {
        "latest_model": "gemini-3.0-pro-preview",
        "fast_model": "gemini-3.0-flash-preview",
        "economy_model": "gemini-3.0-flash-lite",
        "ga_model": "gemini-2.5-pro",  # GA安定版
        "ga_fast_model": "gemini-2.5-flash",  # GA高速版
        "realtime_model": "gemini-3.0-flash-lite",  # ULTRA_FAST for dialogue
        "realtime_premium": "gemini-3.0-flash-preview",  # FAST for quality dialogue
        "supports_vision": True,
        "supports_audio": True,
        "supports_tools": True,
        "max_context": 2000000,
        "supports_realtime": True,
    },
    "local": {
        "latest_model": "phi4",
        "economy_model": "gemma3-1b",
        "realtime_model": "llama3.2-1b",  # ULTRA_FAST for dialogue
        "embedding_model": "nomic-embed-text",
        "supports_vision": False,
        "supports_audio": False,
        "supports_tools": False,
        "supports_realtime": True,
        "requires_ollama": True,
    },
}


# =============================================================================
# Latency Strategy for Real-time Interview Dialogue
# =============================================================================
"""
REAL-TIME DIALOGUE STRATEGY:

For AI interview dialogue, response latency is CRITICAL for natural conversation.
- Target: <500ms Time-To-First-Token (TTFT)
- Acceptable: 500ms-1s TTFT
- Not suitable: >1s TTFT (user will notice significant delay)

Model Selection Guidelines:
1. INTERVIEW DIALOGUE (real-time):
   - Use ULTRA_FAST models: Claude 4.6 Haiku, GPT-5 Nano, Gemini Flash Lite
   - Or FAST models: Claude 4.6 Sonnet, GPT-4o, Gemini 3.0 Flash

2. POST-INTERVIEW ANALYSIS (async):
   - Use FLAGSHIP models: Claude Sonnet 4.6 Opus, GPT-5.2, o3
   - Higher quality analysis, latency not critical

3. HYBRID APPROACH (recommended):
   - Real-time: Claude 4.6 Haiku or GPT-5 Nano (< 200ms TTFT)
   - Background analysis: Claude Sonnet 4.6 Opus (higher quality summary)
   - This provides responsive UX while maintaining analysis quality

Provider-specific recommendations for Japan:
- Azure: azure-gpt-5-nano (Japan East region for lowest latency)
- AWS: bedrock-claude-4.6-haiku (Tokyo region)
- GCP: gemini-3.0-flash-lite (Tokyo region)
"""
