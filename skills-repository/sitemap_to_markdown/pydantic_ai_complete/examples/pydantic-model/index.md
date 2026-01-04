---
url: https://ai.pydantic.dev/examples/pydantic-model/
date: 2026-01-03T23:42:14.371641
---

# Pydantic Model

Simple example of using Pydantic AI to construct a Pydantic model from a text input.

Demonstrates:

## Running the Example

With [dependencies installed and environment variables set](../setup/#usage), run:

This examples uses `openai:gpt-5` by default, but it works well with other models, e.g. you can run it with Gemini using:

(or `PYDANTIC_AI_MODEL=gemini-2.5-flash ...`)

## Example Code

[pydantic_model.py](https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/pydantic_model.py)
    
    
    """Simple example of using Pydantic AI to construct a Pydantic model from a text input.
    
    Run with:
    
        uv run -m pydantic_ai_examples.pydantic_model
    """
    
    import os
    
    import logfire
    from pydantic import BaseModel
    
    from pydantic_ai import Agent
    
    # 'if-token-present' means nothing will be sent (and the example will work) if you don't have logfire configured
    logfire.configure(send_to_logfire='if-token-present')
    logfire.instrument_pydantic_ai()
    
    
    class MyModel(BaseModel):
        city: str
        country: str
    
    
    model = os.getenv('PYDANTIC_AI_MODEL', 'openai:gpt-5')
    print(f'Using model: {model}')
    agent = Agent(model, output_type=MyModel)
    
    if __name__ == '__main__':
        result = agent.run_sync('The windy city in the US of A.')
        print(result.output)
        print(result.usage())
    
