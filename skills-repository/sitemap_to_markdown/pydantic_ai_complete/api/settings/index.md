---
url: https://ai.pydantic.dev/api/settings/
date: 2026-01-03T23:40:55.936255
---

An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the tokens with top_p probability mass.

So 0.1 means only the tokens comprising the top 10% probability mass are considered.

You should either alter `temperature` or `top_p`, but not both.

Supported by:

  - Gemini
  - Anthropic
  - OpenAI
  - Groq
  - Cohere
  - Mistral
  - Bedrock
  - Outlines (Transformers, LlamaCpp, SgLang, VLLMOffline)

