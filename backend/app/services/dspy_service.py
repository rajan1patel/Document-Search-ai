import dspy
from typing import Optional

from app.core.config import settings


# ──────────────────────────────────────────────
# DSPy Signatures
# ──────────────────────────────────────────────

class ChatSignature(dspy.Signature):
    """You are a helpful document assistant. Answer the user's question based strictly on the provided document context. If the context doesn't contain enough information, say so clearly. Use the conversation history for context about previous questions."""

    context: str = dspy.InputField(
        desc="Relevant excerpts from the user's documents"
    )
    conversation_history: str = dspy.InputField(
        desc="Previous messages in the conversation, formatted as role: message pairs"
    )
    question: str = dspy.InputField(
        desc="The user's current question"
    )
    answer: str = dspy.OutputField(
        desc="A thorough, accurate answer based on the context and conversation history"
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

        # Build the LM
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

    def format_context(self, sources: list[dict]) -> str:
        """Convert search results into a single context block for the prompt."""
        if not sources:
            return "No relevant documents found."

        blocks = []
        for i, src in enumerate(sources, 1):
            filename = src.get("filename", "Unknown")
            page = src.get("page")
            chunk = src.get("chunk", "")
            page_info = f" (page {page})" if page else ""
            blocks.append(
                f"[Source {i}] — {filename}{page_info}:\n{chunk}\n"
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
        self._ensure_initialized()

        context_str = self.format_context(sources)
        history_str = self.format_history(history or [])

        answer = self._agent.forward(
            context=context_str,
            history=history_str,
            question=query,
        )

        return answer


# Singleton shared across the app
dspy_service = DspyService()
