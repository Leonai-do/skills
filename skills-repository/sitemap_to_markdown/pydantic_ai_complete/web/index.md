---
url: https://ai.pydantic.dev/web/
date: 2026-01-03T23:40:25.503411
---

# Web Chat UI

Pydantic AI includes a built-in web chat interface that you can use to interact with your agents through a browser.

[![Web Chat UI](../img/web-chat-ui.png)](../img/web-chat-ui.png)

For CLI usage with `clai web`, see the [CLI - Web Chat UI documentation](../cli/#web-chat-ui).

## Installation

Install the `web` extra (installs Starlette and Uvicorn):

## Basic Usage

Create a web app from an agent instance using [`Agent.to_web()`](../api/agent/#pydantic_ai.agent.Agent.to_web "to_web"):

Run the app with any ASGI server:
    
    
    uvicorn my_module:app --host 127.0.0.1 --port 7932
    

## Configuring Models

You can specify additional models to make available in the UI. Models can be provided as a list of model names/instances or a dictionary mapping display labels to model names/instances.

You can specify a list of [builtin tools](../builtin-tools/) that will be shown as options to the user, if the selected model supports them:

Memory Tool

The `memory` builtin tool is not supported via `to_web()` or `clai web`. If your agent needs memory, configure the [`MemoryTool`](../api/builtin_tools/#pydantic_ai.builtin_tools.MemoryTool "MemoryTool

  
      dataclass
  ") directly on the agent at construction time.

You can pass extra instructions that will be included in each agent run:

## Reserved Routes

The web UI app uses the following routes which should not be overwritten:

  - `/` and `/{id}` \- Serves the chat UI
  - `/api/chat` \- Chat endpoint (POST, OPTIONS)
  - `/api/configure` \- Frontend configuration (GET)
  - `/api/health` \- Health check (GET)

The app cannot currently be mounted at a subpath (e.g., `/chat`) because the UI expects these routes at the root. You can add additional routes to the app, but avoid conflicts with these reserved paths.
