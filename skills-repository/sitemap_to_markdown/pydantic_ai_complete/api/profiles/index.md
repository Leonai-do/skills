---
url: https://ai.pydantic.dev/api/profiles/
date: 2026-01-03T23:40:50.154279
---

Non-standard field name used by some providers for model thinking content in Chat Completions API responses.

Plenty of providers use custom field names for thinking content. Ollama and newer versions of vLLM use `reasoning`, while DeepSeek, older vLLM and some others use `reasoning_content`.

Notice that the thinking field configured here is currently limited to `str` type content.

If `openai_chat_send_back_thinking_parts` is set to `'field'`, this field must be set to a non-None value.
