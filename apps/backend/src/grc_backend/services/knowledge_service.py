"""Knowledge management and RAG service.

Provides semantic search and retrieval-augmented generation
for interview support and knowledge base management.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge with embedding."""

    chunk_id: UUID
    content: str
    embedding: list[float]
    source_id: UUID | None = None
    source_type: str | None = None  # "interview", "document", "manual"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchResult:
    """A search result from the knowledge base."""

    chunk: KnowledgeChunk
    score: float  # Similarity score (0-1)
    highlights: list[str] = field(default_factory=list)


@dataclass
class RAGContext:
    """Context for RAG-based generation."""

    query: str
    relevant_chunks: list[SearchResult]
    combined_context: str


class KnowledgeService:
    """Service for knowledge management and RAG.

    Handles:
    - Embedding generation
    - Vector storage and retrieval
    - Semantic search
    - RAG context building
    """

    def __init__(
        self,
        ai_provider=None,
        vector_dimension: int = 1536,
    ):
        """Initialize the knowledge service.

        Args:
            ai_provider: AI provider for embeddings
            vector_dimension: Dimension of embedding vectors
        """
        self.ai_provider = ai_provider
        self.vector_dimension = vector_dimension

        # In-memory store for demo (use pgvector/vector DB in production)
        self._chunks: dict[UUID, KnowledgeChunk] = {}

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.ai_provider:
            return await self.ai_provider.embed(text)
        else:
            # Mock embedding for testing
            import hashlib

            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_val % (2**32))
            return np.random.randn(self.vector_dimension).tolist()

    async def add_knowledge(
        self,
        content: str,
        source_id: UUID | None = None,
        source_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[UUID]:
        """Add knowledge content to the store.

        Content is chunked and embedded for semantic search.

        Args:
            content: Text content to add
            source_id: Source document/interview ID
            source_type: Type of source
            metadata: Additional metadata
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            List of chunk IDs
        """
        # Chunk the content
        chunks = self._chunk_text(content, chunk_size, chunk_overlap)

        chunk_ids = []
        for chunk_text in chunks:
            # Generate embedding
            embedding = await self.generate_embedding(chunk_text)

            # Create chunk
            chunk = KnowledgeChunk(
                chunk_id=uuid4(),
                content=chunk_text,
                embedding=embedding,
                source_id=source_id,
                source_type=source_type,
                metadata=metadata or {},
            )

            # Store chunk
            self._chunks[chunk.chunk_id] = chunk
            chunk_ids.append(chunk.chunk_id)

        logger.info(f"Added {len(chunk_ids)} knowledge chunks from source {source_id}")
        return chunk_ids

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within last 100 chars
                for sep in ["。", ".", "！", "!", "？", "?", "\n\n"]:
                    last_sep = text.rfind(sep, end - 100, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break

            chunks.append(text[start:end].strip())
            start = end - overlap

        return chunks

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
        source_type: str | None = None,
    ) -> list[SearchResult]:
        """Search the knowledge base.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum similarity score
            source_type: Filter by source type

        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)

        # Calculate similarity with all chunks
        results = []
        for chunk in self._chunks.values():
            # Filter by source type if specified
            if source_type and chunk.source_type != source_type:
                continue

            # Cosine similarity
            score = self._cosine_similarity(query_embedding, chunk.embedding)

            if score >= min_score:
                results.append(
                    SearchResult(
                        chunk=chunk,
                        score=score,
                        highlights=self._extract_highlights(query, chunk.content),
                    )
                )

        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _extract_highlights(self, query: str, content: str, window: int = 100) -> list[str]:
        """Extract highlighted snippets from content.

        Args:
            query: Search query
            content: Content to extract from
            window: Characters around match

        Returns:
            List of highlighted snippets
        """
        highlights = []
        query_lower = query.lower()
        content_lower = content.lower()

        # Find query terms in content
        for term in query_lower.split():
            if len(term) < 3:
                continue

            pos = content_lower.find(term)
            if pos >= 0:
                start = max(0, pos - window)
                end = min(len(content), pos + len(term) + window)
                snippet = content[start:end]

                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                highlights.append(snippet)

        return highlights[:3]  # Limit highlights

    async def build_rag_context(
        self,
        query: str,
        limit: int = 5,
        max_context_length: int = 3000,
    ) -> RAGContext:
        """Build RAG context for a query.

        Args:
            query: User query
            limit: Maximum chunks to include
            max_context_length: Maximum context length

        Returns:
            RAGContext with relevant information
        """
        # Search for relevant chunks
        results = await self.search(query, limit=limit)

        # Build combined context
        context_parts = []
        total_length = 0

        for result in results:
            chunk_text = result.chunk.content
            if total_length + len(chunk_text) > max_context_length:
                break
            context_parts.append(chunk_text)
            total_length += len(chunk_text)

        combined_context = "\n\n---\n\n".join(context_parts)

        return RAGContext(
            query=query,
            relevant_chunks=results,
            combined_context=combined_context,
        )

    async def augment_query(
        self,
        query: str,
        context: RAGContext,
    ) -> str:
        """Augment a query with RAG context for AI generation.

        Args:
            query: Original user query
            context: RAG context

        Returns:
            Augmented prompt for AI
        """
        if not context.relevant_chunks:
            return query

        augmented = f"""以下の関連情報を参考にして、質問に回答してください。

## 関連情報
{context.combined_context}

## 質問
{query}

## 回答
"""
        return augmented

    async def extract_knowledge_from_interview(
        self,
        interview_id: UUID,
        transcript: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[UUID]:
        """Extract and store knowledge from an interview.

        Args:
            interview_id: Interview ID
            transcript: Interview transcript
            metadata: Additional metadata

        Returns:
            List of created chunk IDs
        """
        # Extract key information using AI (if available)
        if self.ai_provider:
            from grc_ai import ChatMessage

            extraction_prompt = """
以下のインタビュー記録から、ナレッジベースに保存すべき重要な情報を抽出してください。

## 抽出対象
- 業務プロセスの説明
- 統制活動の詳細
- リスクの特定
- システムや手順の説明
- ベストプラクティス
- 課題や改善点

## インタビュー記録
{transcript}

## 出力形式
抽出した情報を、それぞれ独立したパラグラフとして出力してください。
各パラグラフは、その情報だけで意味が通じるようにしてください。
"""
            messages = [
                ChatMessage(
                    role="user",
                    content=extraction_prompt.format(transcript=transcript),
                )
            ]
            response = await self.ai_provider.chat(messages=messages)
            extracted_content = response.content
        else:
            # Use raw transcript if no AI provider
            extracted_content = transcript

        # Add to knowledge base
        return await self.add_knowledge(
            content=extracted_content,
            source_id=interview_id,
            source_type="interview",
            metadata={
                **(metadata or {}),
                "extracted_at": datetime.utcnow().isoformat(),
            },
        )

    async def get_interview_suggestions(
        self,
        current_topic: str,
        interview_context: str,
        limit: int = 3,
    ) -> list[str]:
        """Get suggested questions/topics based on knowledge base.

        Args:
            current_topic: Current discussion topic
            interview_context: Recent interview context
            limit: Maximum suggestions

        Returns:
            List of suggested questions/topics
        """
        # Search for related knowledge
        context = await self.build_rag_context(
            f"{current_topic} {interview_context}",
            limit=limit,
        )

        if not context.relevant_chunks:
            return []

        # Generate suggestions using AI
        if self.ai_provider:
            from grc_ai import ChatMessage

            suggestion_prompt = f"""
現在のインタビューコンテキストと関連するナレッジに基づいて、
次に聞くべき質問や掘り下げるべきトピックを提案してください。

## 現在のトピック
{current_topic}

## 最近のコンテキスト
{interview_context}

## 関連するナレッジ
{context.combined_context}

## 出力形式
- 提案1
- 提案2
- 提案3

箇条書きで{limit}個の提案を出力してください。
"""
            messages = [ChatMessage(role="user", content=suggestion_prompt)]
            response = await self.ai_provider.chat(messages=messages)

            # Parse suggestions
            suggestions = []
            for line in response.content.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    suggestions.append(line[2:])
                elif line.startswith("・"):
                    suggestions.append(line[1:].strip())

            return suggestions[:limit]
        else:
            # Return topics from knowledge chunks
            topics = []
            for result in context.relevant_chunks:
                # Extract first sentence as topic
                first_sentence = result.chunk.content.split("。")[0]
                if first_sentence and len(first_sentence) < 100:
                    topics.append(f"{first_sentence}について詳しく教えてください")

            return topics[:limit]


# Singleton instance
_knowledge_service: KnowledgeService | None = None


def get_knowledge_service() -> KnowledgeService:
    """Get or create the knowledge service singleton."""
    global _knowledge_service
    if _knowledge_service is None:
        # TODO: Initialize with AI provider from settings
        _knowledge_service = KnowledgeService()
    return _knowledge_service
