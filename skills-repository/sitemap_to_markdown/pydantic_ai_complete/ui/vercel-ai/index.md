---
url: https://ai.pydantic.dev/ui/vercel-ai/
date: 2026-01-03T23:42:47.830933
---

# Vercel AI Data Stream Protocol

Pydantic AI natively supports the [Vercel AI Data Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol) to receive agent run input from, and stream events to, a [Vercel AI Elements](https://ai-sdk.dev/elements) frontend.

## Usage

The [`VercelAIAdapter`](../../api/ui/vercel_ai/#pydantic_ai.ui.vercel_ai.VercelAIAdapter "VercelAIAdapter

  
      dataclass
  ") class is responsible for transforming agent run input received from the frontend into arguments for [`Agent.run_stream_events()`](../../agents/#running-agents), running the agent, and then transforming Pydantic AI events into Vercel AI events. The event stream transformation is handled by the [`VercelAIEventStream`](../../api/ui/vercel_ai/#pydantic_ai.ui.vercel_ai.VercelAIEventStream "VercelAIEventStream

  
      dataclass
  ") class, but you typically won't use this directly.

If you're using a Starlette-based web framework like FastAPI, you can use the [`VercelAIAdapter.dispatch_request()`](../../api/ui/base/#pydantic_ai.ui.UIAdapter.dispatch_request "dispatch_request

  
      async
      classmethod
  ") class method from an endpoint function to directly handle a request and return a streaming response of Vercel AI events. This is demonstrated in the next section.

If you're using a web framework not based on Starlette (e.g. Django or Flask) or need fine-grained control over the input or output, you can create a `VercelAIAdapter` instance and directly use its methods. This is demonstrated in "Advanced Usage" section below.

### Usage with Starlette/FastAPI

Besides the request, [`VercelAIAdapter.dispatch_request()`](../../api/ui/base/#pydantic_ai.ui.UIAdapter.dispatch_request "dispatch_request

  
      async
      classmethod
  ") takes the agent, the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents), and an optional `on_complete` callback function that receives the completed [`AgentRunResult`](../../api/agent/#pydantic_ai.agent.AgentRunResult "AgentRunResult

  
      dataclass
  ") and can optionally yield additional Vercel AI events.

### Advanced Usage

If you're using a web framework not based on Starlette (e.g. Django or Flask) or need fine-grained control over the input or output, you can create a `VercelAIAdapter` instance and directly use its methods, which can be chained to accomplish the same thing as the `VercelAIAdapter.dispatch_request()` class method shown above:

  1. The [`VercelAIAdapter.build_run_input()`](../../api/ui/vercel_ai/#pydantic_ai.ui.vercel_ai.VercelAIAdapter.build_run_input "build_run_input

  
      classmethod
  ") class method takes the request body as bytes and returns a Vercel AI [`RequestData`](../../api/ui/vercel_ai/#pydantic_ai.ui.vercel_ai.request_types.RequestData "RequestData

  
      module-attribute
  ") run input object, which you can then pass to the [`VercelAIAdapter()`](../../api/ui/vercel_ai/#pydantic_ai.ui.vercel_ai.VercelAIAdapter "VercelAIAdapter

  
      dataclass
  ") constructor along with the agent. 
  2. The [`VercelAIAdapter.run_stream()`](../../api/ui/base/#pydantic_ai.ui.UIAdapter.run_stream "run_stream") method runs the agent and returns a stream of Vercel AI events. It supports the same optional arguments as [`Agent.run_stream_events()`](../../agents/#running-agents) and an optional `on_complete` callback function that receives the completed [`AgentRunResult`](../../api/agent/#pydantic_ai.agent.AgentRunResult "AgentRunResult

  
      dataclass
  ") and can optionally yield additional Vercel AI events. 
  3. The [`VercelAIAdapter.encode_stream()`](../../api/ui/base/#pydantic_ai.ui.UIAdapter.encode_stream "encode_stream") method encodes the stream of Vercel AI events as SSE (HTTP Server-Sent Events) strings, which you can then return as a streaming response. 

Note

This example uses FastAPI, but can be modified to work with any web framework.

With Pydantic AI GatewayDirectly to Provider API

[Learn about Gateway](../../gateway) run_stream.py
    
    
    import json
    from http import HTTPStatus
    
    from fastapi import FastAPI
    from fastapi.requests import Request
    from fastapi.responses import Response, StreamingResponse
    from pydantic import ValidationError
    
    from pydantic_ai import Agent
    from pydantic_ai.ui import SSE_CONTENT_TYPE
    from pydantic_ai.ui.vercel_ai import VercelAIAdapter
    
    agent = Agent('gateway/openai:gpt-5')
    
    app = FastAPI()
    
    
    @app.post('/chat')
    async def chat(request: Request) -> Response:
        accept = request.headers.get('accept', SSE_CONTENT_TYPE)
        try:
            run_input = VercelAIAdapter.build_run_input(await request.body())
        except ValidationError as e:
            return Response(
                content=json.dumps(e.json()),
                media_type='application/json',
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
    
        adapter = VercelAIAdapter(agent=agent, run_input=run_input, accept=accept)
        event_stream = adapter.run_stream()
    
        sse_event_stream = adapter.encode_stream(event_stream)
        return StreamingResponse(sse_event_stream, media_type=accept)
    

run_stream.py
    
    
    import json
    from http import HTTPStatus
    
    from fastapi import FastAPI
    from fastapi.requests import Request
    from fastapi.responses import Response, StreamingResponse
    from pydantic import ValidationError
    
    from pydantic_ai import Agent
    from pydantic_ai.ui import SSE_CONTENT_TYPE
    from pydantic_ai.ui.vercel_ai import VercelAIAdapter
    
    agent = Agent('openai:gpt-5')
    
    app = FastAPI()
    
    
    @app.post('/chat')
    async def chat(request: Request) -> Response:
        accept = request.headers.get('accept', SSE_CONTENT_TYPE)
        try:
            run_input = VercelAIAdapter.build_run_input(await request.body())
        except ValidationError as e:
            return Response(
                content=json.dumps(e.json()),
                media_type='application/json',
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
    
        adapter = VercelAIAdapter(agent=agent, run_input=run_input, accept=accept)
        event_stream = adapter.run_stream()
    
        sse_event_stream = adapter.encode_stream(event_stream)
        return StreamingResponse(sse_event_stream, media_type=accept)
    
