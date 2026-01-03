"""Type-safe LLM client wrapper for LangChain."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

logger = logging.getLogger(__name__)


class LLMClient:
    """Type-safe wrapper for LangChain ChatOpenAI client."""

    def __init__(
        self,
        model: str,
        api_key: str | None,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the LLM client.

        Args:
            model: The model name to use.
            api_key: The OpenAI API key.
            temperature: The sampling temperature.
        """
        self._model = model
        self._api_key = SecretStr(api_key) if api_key else None
        self._temperature = temperature
        self._llm: ChatOpenAI | None = None

    def _get_llm(self) -> ChatOpenAI:
        """Get or create the ChatOpenAI instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self._model,
                api_key=self._api_key,
                temperature=self._temperature,
            )
        return self._llm

    def _extract_text_content(  # noqa: C901
        self, content: str | list[Any] | Any
    ) -> str:
        """Extract text from LLM response content.

        LangChain's AIMessage.content type is not fully typed, so we handle
        multiple possible content formats from different LLM providers.

        Args:
            content: The content from AIMessage (str, list, or other).

        Returns:
            The extracted text content.

        Raises:
            ValueError: If content type is unexpected.
        """
        if isinstance(content, str):
            return content

        # Handle list content (multimodal responses from some providers)
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:  # type: ignore[reportUnknownVariableType]
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    # Content block format: {"type": "text", "text": "..."}
                    text_value: Any = item.get(  # type: ignore[reportUnknownMemberType]
                        "text"
                    )
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            return "".join(text_parts)

        raise ValueError(f"Unexpected content type: {type(content)}")

    async def invoke_with_prompt(
        self,
        prompt_template: ChatPromptTemplate,
        variables: dict[str, str],
    ) -> str:
        """Invoke the LLM with a prompt template.

        Args:
            prompt_template: The ChatPromptTemplate to use.
            variables: The variables to fill in the template.

        Returns:
            The text content of the response.

        Raises:
            ValueError: If the response content is not a string.
        """
        llm = self._get_llm()
        # LangChain's type system is partially typed, using Any for chain operations
        chain = prompt_template | llm  # type: ignore[operator]
        result: AIMessage = await chain.ainvoke(  # type: ignore[reportUnknownMemberType]
            variables
        )

        # LangChain AIMessage.content can be str or list of content blocks
        content: str | list[Any] = result.content  # type: ignore[reportUnknownMemberType]
        return self._extract_text_content(content)


def create_prompt_template(
    system_message: str,
    user_template: str = "{prompt}",
) -> ChatPromptTemplate:
    """Create a ChatPromptTemplate with type-safe construction.

    Args:
        system_message: The system message content.
        user_template: The user message template (default: "{prompt}").

    Returns:
        A ChatPromptTemplate instance.
    """
    # Type ignore for langchain's partially typed from_messages
    return ChatPromptTemplate.from_messages(  # type: ignore[return-value]
        [
            ("system", system_message),
            ("user", user_template),
        ]
    )
