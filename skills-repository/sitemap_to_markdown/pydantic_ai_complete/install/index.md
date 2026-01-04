---
url: https://ai.pydantic.dev/install/
date: 2026-01-03T23:40:08.637417
---

# Installation

Pydantic AI is available on PyPI as [`pydantic-ai`](https://pypi.org/project/pydantic-ai/) so installation is as simple as:

(Requires Python 3.10+)

This installs the `pydantic_ai` package, core dependencies, and libraries required to use all the models included in Pydantic AI. If you want to install only those dependencies required to use a specific model, you can install the "slim" version of Pydantic AI.

## Use with Pydantic Logfire

Pydantic AI has an excellent (but completely optional) integration with [Pydantic Logfire](https://pydantic.dev/logfire) to help you view and understand agent runs.

Logfire comes included with `pydantic-ai` (but not the "slim" version), so you can typically start using it immediately by following the [Logfire setup docs](../logfire/#using-logfire).

## Running Examples

We distribute the [`pydantic_ai_examples`](https://github.com/pydantic/pydantic-ai/tree/main/examples/pydantic_ai_examples) directory as a separate PyPI package ([`pydantic-ai-examples`](https://pypi.org/project/pydantic-ai-examples/)) to make examples extremely easy to customize and run.

To install examples, use the `examples` optional group:

To run the examples, follow instructions in the [examples docs](../examples/setup/).

## Slim Install

If you know which model you're going to use and want to avoid installing superfluous packages, you can use the [`pydantic-ai-slim`](https://pypi.org/project/pydantic-ai-slim/) package. For example, if you're using just [`OpenAIChatModel`](../api/models/openai/#pydantic_ai.models.openai.OpenAIChatModel "OpenAIChatModel

  
      dataclass
  "), you would run:

`pydantic-ai-slim` has the following optional groups:

You can also install dependencies for multiple models and use cases, for example:
