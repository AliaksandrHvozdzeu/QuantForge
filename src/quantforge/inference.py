"""ChatML inference helpers for Qwen2.5-Instruct models."""

CHAT_FORMAT = "chatml"
IM_END = "<|" + "im_end" + "|>"
STOP_TOKENS = [IM_END, "<|endoftext|>"]

DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful coding assistant."


def llama_kwargs(extra: dict | None = None, system: str | None = None) -> dict:
    kw = {"chat_format": CHAT_FORMAT}
    if extra:
        kw.update(extra)
    return kw


def system_prompt(config: dict | None = None) -> str:
    if config:
        return config.get("chat", {}).get("system", DEFAULT_SYSTEM)
    return DEFAULT_SYSTEM


def chat_completion(
    llm,
    user_message: str,
    *,
    system: str | None = None,
    max_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9,
):
    return llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system or DEFAULT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        stop=STOP_TOKENS,
    )


def extract_reply(response: dict) -> str:
    choice = response["choices"][0]
    if "message" in choice:
        return (choice["message"].get("content") or "").strip()
    return (choice.get("text") or "").strip()
