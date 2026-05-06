"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from typing import Any

from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import Settings, get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    _USD_PER_1M_INPUT_TOKENS: dict[str, float] = {
        "gpt-4o-mini": 0.15,
        "gpt-4o": 5.00,
    }
    _USD_PER_1M_OUTPUT_TOKENS: dict[str, float] = {
        "gpt-4o-mini": 0.60,
        "gpt-4o": 15.00,
    }

    def __init__(
        self,
        settings: Settings | None = None,
        timeout_seconds: int | None = None,
        max_retries: int = 3,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds or self.settings.timeout_seconds
        self.max_retries = max(1, max_retries)

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Uses OpenAI Chat Completions with retry and timeout.
        Falls back to a deterministic local response if provider access fails.
        """
        if not self.settings.openai_api_key:
            return self._fallback_response(user_prompt, reason="OPENAI_API_KEY is missing")

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    return self._complete_openai(system_prompt=system_prompt, user_prompt=user_prompt)
        except Exception as exc:
            return self._fallback_response(user_prompt, reason=f"provider error: {type(exc).__name__}")

    def _complete_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key, timeout=self.timeout_seconds)
        response: Any = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = ""
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)

        return LLMResponse(
            content=content.strip(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(
                model=self.settings.openai_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ),
        )

    def _fallback_response(self, user_prompt: str, reason: str) -> LLMResponse:
        preview = user_prompt.strip().replace("\n", " ")
        if len(preview) > 240:
            preview = f"{preview[:237]}..."
        content = (
            "[Fallback LLM response] Unable to call remote model; "
            f"reason: {reason}.\n"
            "Prompt summary: "
            f"{preview}"
        )
        return LLMResponse(content=content, input_tokens=None, output_tokens=None, cost_usd=0.0)

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int | None,
        output_tokens: int | None,
    ) -> float | None:
        if input_tokens is None or output_tokens is None:
            return None
        input_rate = self._USD_PER_1M_INPUT_TOKENS.get(model)
        output_rate = self._USD_PER_1M_OUTPUT_TOKENS.get(model)
        if input_rate is None or output_rate is None:
            return None
        return (input_tokens / 1_000_000 * input_rate) + (output_tokens / 1_000_000 * output_rate)
