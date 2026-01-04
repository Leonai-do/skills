---
url: https://ai.pydantic.dev/direct/
date: 2026-01-03T23:40:02.949051
---

# Direct Model Requests

The `direct` module provides low-level methods for making imperative requests to LLMs where the only abstraction is input and output schema translation, enabling you to use all models with the same API.

These methods are thin wrappers around the [`Model`](../api/models/base/#pydantic_ai.models.Model "Model") implementations, offering a simpler interface when you don't need the full functionality of an [`Agent`](../api/agent/#pydantic_ai.agent.Agent "Agent

  
      dataclass
  ").

The following functions are available:

## Basic Example

Here's a simple example demonstrating how to use the direct API to make a basic request:

direct_basic.py
    
    
    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_sync
    
    # Make a synchronous request to the model
    model_response = model_request_sync(
        'anthropic:claude-haiku-4-5',
        [ModelRequest.user_text_prompt('What is the capital of France?')]
    )
    
    print(model_response.parts[0].content)
    #> The capital of France is Paris.
    print(model_response.usage)
    #> RequestUsage(input_tokens=56, output_tokens=7)
    

_(This example is complete, it can be run "as is")_

You can also use the direct API to work with function/tool calling.

Even here we can use Pydantic to generate the JSON schema for the tool:
    
    
    from typing import Literal
    
    from pydantic import BaseModel
    
    from pydantic_ai import ModelRequest, ToolDefinition
    from pydantic_ai.direct import model_request
    from pydantic_ai.models import ModelRequestParameters
    
    
    class Divide(BaseModel):
        """Divide two numbers."""
    
        numerator: float
        denominator: float
        on_inf: Literal['error', 'infinity'] = 'infinity'
    
    
    async def main():
        # Make a request to the model with tool access
        model_response = await model_request(
            'openai:gpt-5-nano',
            [ModelRequest.user_text_prompt('What is 123 / 456?')],
            model_request_parameters=ModelRequestParameters(
                function_tools=[
                    ToolDefinition(
                        name=Divide.__name__.lower(),
                        description=Divide.__doc__,
                        parameters_json_schema=Divide.model_json_schema(),
                    )
                ],
                allow_text_output=True,  # Allow model to either use tools or respond directly
            ),
        )
        print(model_response)
        """
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='divide',
                    args={'numerator': '123', 'denominator': '456'},
                    tool_call_id='pyd_ai_2e0e396768a14fe482df90a29a78dc7b',
                )
            ],
            usage=RequestUsage(input_tokens=55, output_tokens=7),
            model_name='gpt-5-nano',
            timestamp=datetime.datetime(...),
        )
        """
    

_(This example is complete, it can be run "as is" — you'll need to add`asyncio.run(main())` to run `main`)_

## When to Use the direct API vs Agent

The direct API is ideal when:

  1. You need more direct control over model interactions
  2. You want to implement custom behavior around model requests
  3. You're building your own abstractions on top of model interactions

For most application use cases, the higher-level [`Agent`](../api/agent/#pydantic_ai.agent.Agent "Agent

  
      dataclass
  ") API provides a more convenient interface with additional features such as built-in tool execution, retrying, structured output parsing, and more.

## OpenTelemetry or Logfire Instrumentation

As with [agents](../api/agent/#pydantic_ai.agent.Agent "Agent

  
      dataclass
  "), you can enable OpenTelemetry/Logfire instrumentation with just a few extra lines

direct_instrumented.py
    
    
    import logfire
    
    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_sync
    
    logfire.configure()
    logfire.instrument_pydantic_ai()
    
    # Make a synchronous request to the model
    model_response = model_request_sync(
        'anthropic:claude-haiku-4-5',
        [ModelRequest.user_text_prompt('What is the capital of France?')],
    )
    
    print(model_response.parts[0].content)
    #> The capital of France is Paris.
    

_(This example is complete, it can be run "as is")_

You can also enable OpenTelemetry on a per call basis:

direct_instrumented.py
    
    
    import logfire
    
    from pydantic_ai import ModelRequest
    from pydantic_ai.direct import model_request_sync
    
    logfire.configure()
    
    # Make a synchronous request to the model
    model_response = model_request_sync(
        'anthropic:claude-haiku-4-5',
        [ModelRequest.user_text_prompt('What is the capital of France?')],
        instrument=True
    )
    
    print(model_response.parts[0].content)
    #> The capital of France is Paris.
    

See [Debugging and Monitoring](../logfire/) for more details, including how to instrument with plain OpenTelemetry without Logfire.
