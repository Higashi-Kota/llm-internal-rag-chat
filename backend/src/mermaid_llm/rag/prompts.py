"""RAG prompt templates."""

# pyright: reportUnknownMemberType=false
# LangChain ChatPromptTemplate.from_messages return type is not fully annotated

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# System prompt for RAG chat
RAG_SYSTEM_PROMPT = """あなたは提供された文書に基づいて質問に回答するアシスタントです。

以下のルールに従ってください：
1. 回答は必ず提供されたコンテキスト（参照文書）に基づいてください
2. コンテキストに情報がない場合は、「提供された文書にはその情報が含まれていません」と正直に伝えてください
3. 回答は日本語で、簡潔かつ正確に行ってください
4. 必要に応じて、参照した文書の情報を引用してください

## 参照文書
{context}
"""

# Alternative English system prompt
RAG_SYSTEM_PROMPT_EN = """You are an assistant that answers questions based on the provided documents.

Follow these rules:
1. Always base your answers on the provided context (reference documents)
2. If the information is not in the context, honestly say "The provided documents do not contain that information"
3. Answer concisely and accurately
4. Quote from the reference documents when appropriate

## Reference Documents
{context}
"""


def create_rag_prompt(language: str = "ja") -> ChatPromptTemplate:
    """Create a RAG prompt template.

    Args:
        language: Language for system prompt ("ja" or "en").

    Returns:
        ChatPromptTemplate for RAG.
    """
    system_prompt = RAG_SYSTEM_PROMPT if language == "ja" else RAG_SYSTEM_PROMPT_EN

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


# Default prompt template
rag_prompt = create_rag_prompt()
