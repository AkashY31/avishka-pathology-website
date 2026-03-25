"""Azure OpenAI client factory with graceful fallback."""

from openai import AzureOpenAI
from core.config import settings

_client: AzureOpenAI | None = None


def get_client() -> AzureOpenAI | None:
    global _client
    if _client is None and settings.azure_configured:
        _client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
    return _client


def chat_completion(messages: list[dict], max_tokens: int = 600) -> str:
    """
    Send messages to Azure OpenAI and return the assistant reply.
    Falls back to a polite offline message if not configured.
    """
    client = get_client()
    if client is None:
        return (
            "I'm currently offline. Please call us at 7355230710 "
            "or email avishka.pathology@outlook.com for assistance."
        )

    response = client.chat.completions.create(
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        messages=messages,
        max_completion_tokens=max_tokens,
        temperature=1.0,
    )
    return response.choices[0].message.content.strip()
