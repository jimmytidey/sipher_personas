"""Claude API caller factory for the LLM clustering notebooks."""

import httpx

_CLAUDE_URL        = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"


def make_claude_caller(api_key: str, model: str, thinking_budget: int = 8000):
    """Return a _claude_chat(system, user) callable bound to the given key and model."""

    def _claude_chat(system: str, user: str, timeout: int = 300) -> str:
        """Call Claude Messages API. Prints thinking (if any), returns final response text."""
        payload: dict = {
            "model":      model,
            "max_tokens": 16000,
            "system":     system,
            "messages":   [{"role": "user", "content": user}],
        }
        headers = {
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }
        if thinking_budget > 0:
            payload["thinking"]    = {"type": "enabled", "budget_tokens": thinking_budget}
            payload["temperature"] = 1  # extended thinking requires temperature=1
        else:
            payload["temperature"] = 0.3

        print(f"  POST {_CLAUDE_URL}", flush=True)
        with httpx.Client(timeout=timeout) as http:
            resp = http.post(_CLAUDE_URL, headers=headers, json=payload)
        print(f"  HTTP {resp.status_code}", flush=True)
        if resp.status_code != 200:
            print(f"  Response body: {resp.text}", flush=True)
            resp.raise_for_status()
        data = resp.json()

        thinking_parts = [b["thinking"] for b in data["content"] if b.get("type") == "thinking"]
        text_parts     = [b["text"]     for b in data["content"] if b.get("type") == "text"]
        if thinking_parts:
            print(f"\n\u2500\u2500 Claude thinking \u2500\u2500\n{''.join(thinking_parts)}\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n", flush=True)
        return "".join(text_parts)

    return _claude_chat
