import logging
import dspy
from typing import Optional
from collections import defaultdict

from app.core.config import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# DSPy Signatures
# ──────────────────────────────────────────────

class ChatSignature(dspy.Signature):
    """You are a precise document assistant. Follow these rules strictly:

    1. Answer ONLY using the provided document context. Do NOT use outside knowledge or make up information.
    2. If the context doesn't contain enough information to answer completely, say so clearly — do not fill in gaps.
    3. Reference source filenames when presenting information (e.g. "According to [filename.pdf]...").
    4. When multiple chunks from the same file contain relevant info, consolidate them into a coherent answer.
    5. Be thorough, specific, and well-structured. Use bullet points or sections for complex answers.
    6. If the question refers to a previous conversation turn, use the conversation history for continuity.
    7. Do NOT mention "the context" or "the provided documents" — just answer naturally as an AI assistant.
    """

    context: str = dspy.InputField(
        desc="Document excerpts grouped by source file. Each group contains filename, page numbers, and relevant text excerpts."
    )
    conversation_history: str = dspy.InputField(
        desc="Previous messages in the conversation, formatted as role: message pairs"
    )
    question: str = dspy.InputField(
        desc="The user's current question"
    )
    answer: str = dspy.OutputField(
        desc="A thorough, accurate answer based strictly on the context, citing sources naturally"
    )


# ──────────────────────────────────────────────
# DSPy Module — Document Chat Agent
# ──────────────────────────────────────────────

class DocChatAgent(dspy.Module):
    """DSPy module that answers questions using retrieved document context."""

    def __init__(self):
        super().__init__()
        self.answer_question = dspy.ChainOfThought(ChatSignature)

    def forward(self, context: str, history: str, question: str) -> str:
        prediction = self.answer_question(
            context=context,
            conversation_history=history,
            question=question,
        )
        return prediction.answer


# ──────────────────────────────────────────────
# Service Wrapper
# ──────────────────────────────────────────────

class DspyService:
    """Wraps DSPy configuration and the chat agent for use in the FastAPI app."""

    def __init__(self):
        self._lm: Optional[dspy.LM] = None
        self._agent: Optional[DocChatAgent] = None
        self._initialized: bool = False

    # ── Lazy initialisation ──────────────────

    def _ensure_initialized(self):
        if self._initialized:
            return

        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Add a valid OpenRouter API key to the .env file."
            )

        # Build the LM
        logger.info(
            "Initializing DSPy with model=%s, base_url=%s",
            settings.LLM_MODEL,
            settings.LLM_BASE_URL,
        )
        self._lm = dspy.LM(
            model=f"openrouter/{settings.LLM_MODEL}",
            api_key=settings.OPENROUTER_API_KEY,
            api_base=settings.LLM_BASE_URL,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
        dspy.configure(lm=self._lm)

        # Build the agent module
        self._agent = DocChatAgent()
        self._initialized = True

    # ── Public helpers ───────────────────────

    def format_history(self, history: list[dict]) -> str:
        """Convert a list of {role, content} messages into a plain-text summary."""
        if not history:
            return "No previous conversation."

        lines = []
        for msg in history:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def group_sources_by_file(sources: list[dict]) -> list[dict]:
        """Group search results by filename. Returns a list of dicts:
        {filename, chunks: [{page, chunk, score}], avg_score, total_chunks}
        """
        if not sources:
            return []

        groups = defaultdict(list)
        for src in sources:
            filename = src.get("filename", "Unknown")
            groups[filename].append(src)

        result = []
        for filename, items in groups.items():
            avg_score = sum(item.get("score", 0) for item in items) / len(items)
            chunks = [
                {
                    "page": item.get("page"),
                    "chunk": item.get("chunk", ""),
                    "score": item.get("score", 0),
                }
                for item in items
            ]
            result.append({
                "filename": filename,
                "chunks": chunks,
                "avg_score": round(avg_score, 4),
                "total_chunks": len(chunks),
            })

        # Sort by average score descending
        result.sort(key=lambda g: g["avg_score"], reverse=True)
        return result

    def format_context(self, sources: list[dict]) -> str:
        """Convert search results into a single context block for the prompt,
        grouped by source file."""
        if not sources:
            return "No relevant documents found."

        groups = self.group_sources_by_file(sources)
        blocks = []
        for i, group in enumerate(groups, 1):
            filename = group["filename"]
            chunks = group["chunks"]
            page_info = ", ".join(
                f"p.{c['page']}" for c in chunks if c["page"] is not None
            )
            page_str = f" (pages: {page_info})" if page_info else ""

            excerpts = "\n".join(
                f"  [{i}.{j}] {c['chunk']}" for j, c in enumerate(chunks, 1)
            )
            blocks.append(
                f"[Source {i}] — {filename}{page_str}:\n{excerpts}\n"
            )
        return "\n".join(blocks)

    # ── Chat ─────────────────────────────────

    async def generate_answer(
        self,
        query: str,
        sources: list[dict],
        history: list[dict] | None = None,
    ) -> str:
        """Generate a DSPy-powered answer using the retrieved document sources."""
        try:
            self._ensure_initialized()
        except Exception as e:
            logger.error("Failed to initialize DSPy: %s", e, exc_info=True)
            raise RuntimeError(
                "AI model is not configured. Please set a valid OPENROUTER_API_KEY in the .env file."
            ) from e

        if not sources:
            return (
                "I couldn't find any relevant documents to answer your question. "
                "Please try uploading documents first or rephrase your query."
            )

        context_str = self.format_context(sources)
        history_str = self.format_history(history or [])

        try:
            answer = self._agent.forward(
                context=context_str,
                history=history_str,
                question=query,
            )
            return answer
        except Exception as e:
            logger.error("DSPy LLM call failed: %s", e, exc_info=True)
            raise RuntimeError(
                f"AI model call failed: {e}. "
                "Please check your OpenRouter API key and credit balance."
            ) from e


# Singleton shared across the app
dspy_service = DspyService()
