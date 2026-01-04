---
url: https://ai.pydantic.dev/thinking/
date: 2026-01-03T23:40:14.518994
---

# Thinking

Thinking (or reasoning) is the process by which a model works through a problem step-by-step before providing its final answer.

This capability is typically disabled by default and depends on the specific model being used. See the sections below for how to enable thinking for each provider.

## OpenAI

When using the [`OpenAIChatModel`](../api/models/openai/#pydantic_ai.models.openai.OpenAIChatModel "OpenAIChatModel

  
      dataclass
  "), text output inside `<think>` tags are converted to [`ThinkingPart`](../api/messages/#pydantic_ai.messages.ThinkingPart "ThinkingPart

  
      dataclass
  ") objects. You can customize the tags using the [`thinking_tags`](../api/profiles/#pydantic_ai.profiles.ModelProfile.thinking_tags "thinking_tags

  
      class-attribute
      instance-attribute
  ") field on the [model profile](../models/openai/#model-profile).

Some [OpenAI-compatible model providers](../models/openai/#openai-compatible-models) might also support native thinking parts that are not delimited by tags. Instead, they are sent and received as separate, custom fields in the API. Typically, if you are calling the model via the `<provider>:<model>` shorthand, Pydantic AI handles it for you. Nonetheless, you can still configure the fields with [`openai_chat_thinking_field`](../api/profiles/#pydantic_ai.profiles.openai.OpenAIModelProfile.openai_chat_thinking_field "openai_chat_thinking_field

  
      class-attribute
      instance-attribute
  ").

If your provider recommends to send back these custom fields not changed, for caching or interleaved thinking benefits, you can also achieve this with [`openai_chat_send_back_thinking_parts`](../api/profiles/#pydantic_ai.profiles.openai.OpenAIModelProfile.openai_chat_send_back_thinking_parts "openai_chat_send_back_thinking_parts

  
      class-attribute
      instance-attribute
  ").

### OpenAI Responses

The [`OpenAIResponsesModel`](../api/models/openai/#pydantic_ai.models.openai.OpenAIResponsesModel "OpenAIResponsesModel

  
      dataclass
  ") can generate native thinking parts. To enable this functionality, you need to set the [`OpenAIResponsesModelSettings.openai_reasoning_effort`](../api/models/openai/#pydantic_ai.models.openai.OpenAIChatModelSettings.openai_reasoning_effort "openai_reasoning_effort

  
      instance-attribute
  ") and [`OpenAIResponsesModelSettings.openai_reasoning_summary`](../api/models/openai/#pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_reasoning_summary "openai_reasoning_summary

  
      instance-attribute
  ") [model settings](../agents/#model-run-settings).

By default, the unique IDs of reasoning, text, and function call parts from the message history are sent to the model, which can result in errors like `"Item 'rs_123' of type 'reasoning' was provided without its required following item."` if the message history you're sending does not match exactly what was received from the Responses API in a previous response, for example if you're using a [history processor](../message-history/#processing-message-history). To disable this, you can disable the [`OpenAIResponsesModelSettings.openai_send_reasoning_ids`](../api/models/openai/#pydantic_ai.models.openai.OpenAIResponsesModelSettings.openai_send_reasoning_ids "openai_send_reasoning_ids

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings).

openai_thinking_part.py
    
    
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
    
    model = OpenAIResponsesModel('gpt-5')
    settings = OpenAIResponsesModelSettings(
        openai_reasoning_effort='low',
        openai_reasoning_summary='detailed',
    )
    agent = Agent(model, model_settings=settings)
    ...
    

Raw reasoning without summaries

Some OpenAI-compatible APIs (such as LM Studio, vLLM, or OpenRouter with gpt-oss models) may return raw reasoning content without reasoning summaries. In this case, [`ThinkingPart.content`](../api/messages/#pydantic_ai.messages.ThinkingPart.content "content

  
      instance-attribute
  ") will be empty, but the raw reasoning is available in `provider_details['raw_content']`. Following [OpenAI's guidance](https://cookbook.openai.com/examples/responses_api/reasoning_items) that raw reasoning should not be shown directly to users, we store it in `provider_details` rather than in the main `content` field.

## Anthropic

To enable thinking, use the [`AnthropicModelSettings.anthropic_thinking`](../api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModelSettings.anthropic_thinking "anthropic_thinking

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings).

anthropic_thinking_part.py
    
    
    from pydantic_ai import Agent
    from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
    
    model = AnthropicModel('claude-sonnet-4-0')
    settings = AnthropicModelSettings(
        anthropic_thinking={'type': 'enabled', 'budget_tokens': 1024},
    )
    agent = Agent(model, model_settings=settings)
    ...
    

## Google

To enable thinking, use the [`GoogleModelSettings.google_thinking_config`](../api/models/google/#pydantic_ai.models.google.GoogleModelSettings.google_thinking_config "google_thinking_config

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings).

google_thinking_part.py
    
    
    from pydantic_ai import Agent
    from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
    
    model = GoogleModel('gemini-2.5-pro')
    settings = GoogleModelSettings(google_thinking_config={'include_thoughts': True})
    agent = Agent(model, model_settings=settings)
    ...
    

## Bedrock

Although Bedrock Converse doesn't provide a unified API to enable thinking, you can still use [`BedrockModelSettings.bedrock_additional_model_requests_fields`](../api/models/bedrock/#pydantic_ai.models.bedrock.BedrockModelSettings.bedrock_additional_model_requests_fields "bedrock_additional_model_requests_fields

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings) to pass provider-specific configuration:

## Groq

Groq supports different formats to receive thinking parts:

  - `"raw"`: The thinking part is included in the text content inside `<think>` tags, which are automatically converted to [`ThinkingPart`](../api/messages/#pydantic_ai.messages.ThinkingPart "ThinkingPart

  
      dataclass
  ") objects.
  - `"hidden"`: The thinking part is not included in the text content.
  - `"parsed"`: The thinking part has its own structured part in the response which is converted into a [`ThinkingPart`](../api/messages/#pydantic_ai.messages.ThinkingPart "ThinkingPart

  
      dataclass
  ") object.

To enable thinking, use the [`GroqModelSettings.groq_reasoning_format`](../api/models/groq/#pydantic_ai.models.groq.GroqModelSettings.groq_reasoning_format "groq_reasoning_format

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings):

groq_thinking_part.py
    
    
    from pydantic_ai import Agent
    from pydantic_ai.models.groq import GroqModel, GroqModelSettings
    
    model = GroqModel('qwen-qwq-32b')
    settings = GroqModelSettings(groq_reasoning_format='parsed')
    agent = Agent(model, model_settings=settings)
    ...
    

## OpenRouter

To enable thinking, use the [`OpenRouterModelSettings.openrouter_reasoning`](../api/models/openrouter/#pydantic_ai.models.openrouter.OpenRouterModelSettings.openrouter_reasoning "openrouter_reasoning

  
      instance-attribute
  ") [model setting](../agents/#model-run-settings).

openrouter_thinking_part.py
    
    
    from pydantic_ai import Agent
    from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
    
    model = OpenRouterModel('openai/gpt-5')
    settings = OpenRouterModelSettings(openrouter_reasoning={'effort': 'high'})
    agent = Agent(model, model_settings=settings)
    ...
    

## Mistral

Thinking is supported by the `magistral` family of models. It does not need to be specifically enabled.

## Cohere

Thinking is supported by the `command-a-reasoning-08-2025` model. It does not need to be specifically enabled.

## Hugging Face

Text output inside `<think>` tags is automatically converted to [`ThinkingPart`](../api/messages/#pydantic_ai.messages.ThinkingPart "ThinkingPart

  
      dataclass
  ") objects. You can customize the tags using the [`thinking_tags`](../api/profiles/#pydantic_ai.profiles.ModelProfile.thinking_tags "thinking_tags

  
      class-attribute
      instance-attribute
  ") field on the [model profile](../models/openai/#model-profile).

## Outlines

Some local models run through Outlines include in their text output a thinking part delimited by tags. In that case, it will be handled by Pydantic AI that will separate the thinking part from the final answer without the need to specifically enable it. The thinking tags used by default are `"<think>"` and `"</think>"`. If your model uses different tags, you can specify them in the [model profile](../models/openai/#model-profile) using the [`thinking_tags`](../api/profiles/#pydantic_ai.profiles.ModelProfile.thinking_tags "thinking_tags

  
      class-attribute
      instance-attribute
  ") field.

Outlines currently does not support thinking along with structured output. If you provide an `output_type`, the model text output will not contain a thinking part with the associated tags, and you may experience degraded performance.
