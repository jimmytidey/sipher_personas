"""Gemini API caller factory for the LLM clustering notebooks."""

import httpx


def make_gemini_caller(api_key: str, model: str):
    """Return a _gemini_chat(system, user) callable bound to the given key and model."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def _gemini_chat(system: str, user: str, temperature: float = 0.3, timeout: int = 300) -> str:
        """Call Gemini native API. Prints thinking, returns final response text."""
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature,
                "thinkingConfig": {"includeThoughts": True},
            },
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        print(f"  POST {url}", flush=True)
        with httpx.Client(timeout=timeout) as http:
            resp = http.post(url, headers=headers, json=payload)
        print(f"  HTTP {resp.status_code}", flush=True)
        if resp.status_code != 200:
            print(f"  Response body: {resp.text}", flush=True)
            resp.raise_for_status()
        data     = resp.json()
        parts    = data["candidates"][0]["content"]["parts"]
        thoughts = [p["text"] for p in parts if p.get("thought")]
        response = [p["text"] for p in parts if not p.get("thought")]
        if thoughts:
            print(f"\n\u2500\u2500 Gemini thinking \u2500\u2500\n{''.join(thoughts)}\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n", flush=True)
        return "".join(response)

    return _gemini_chat
