from __future__ import annotations

import importlib
from dataclasses import dataclass
from time import perf_counter

from app.config import settings


@dataclass(frozen=True)
class OpenAIAgentAdapter:
    def run_task(self, input_text: str, config: dict[str, object]) -> dict[str, object]:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for adapter_type 'openai'.")

        try:
            openai_module = importlib.import_module("openai")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The 'openai' package is required for adapter_type 'openai'."
            ) from exc
        openai_client_class = openai_module.OpenAI

        model = str(config.get("model") or "gpt-4.1-mini")
        system_prompt = str(
            config.get("system_prompt")
            or "You are a support QA assistant. Answer concisely and only from known policy facts."
        )
        temperature_raw = config.get("temperature", 0.0)
        max_output_tokens_raw = config.get("max_output_tokens", 180)
        max_output_tokens = (
            int(max_output_tokens_raw)
            if isinstance(max_output_tokens_raw, int | float)
            else 180
        )
        temperature = (
            float(temperature_raw) if isinstance(temperature_raw, int | float) else 0.0
        )

        client = openai_client_class(api_key=settings.openai_api_key)
        started_at = perf_counter()
        response = client.responses.create(
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
        )
        latency_ms = int((perf_counter() - started_at) * 1000)

        output_text = ""
        if hasattr(response, "output_text") and isinstance(response.output_text, str):
            output_text = response.output_text.strip()

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", None)
        completion_tokens = getattr(usage, "output_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        token_usage = {
            "prompt": int(prompt_tokens) if isinstance(prompt_tokens, int) else 0,
            "completion": int(completion_tokens) if isinstance(completion_tokens, int) else 0,
        }
        if isinstance(total_tokens, int):
            token_usage["total"] = total_tokens

        response_id = getattr(response, "id", None)
        finish_reason = getattr(response, "status", None) or "completed"

        return {
            "final_output": output_text or None,
            "latency_ms": latency_ms,
            "token_usage": token_usage,
            "cost": None,
            "termination_reason": str(finish_reason),
            "error": None,
            "trace_events": [
                {"step_index": 0, "event_type": "agent_start", "input": input_text},
                {
                    "step_index": 1,
                    "event_type": "provider_request",
                    "provider": "openai",
                    "model": model,
                    "response_id": str(response_id) if response_id is not None else None,
                },
                {
                    "step_index": 2,
                    "event_type": "final_output",
                    "output": output_text,
                },
            ],
        }
