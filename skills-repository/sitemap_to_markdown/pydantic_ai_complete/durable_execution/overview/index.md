---
url: https://ai.pydantic.dev/durable_execution/overview/
date: 2026-01-03T23:41:46.605189
---

# Durable Execution

Pydantic AI allows you to build durable agents that can preserve their progress across transient API failures and application errors or restarts, and handle long-running, asynchronous, and human-in-the-loop workflows with production-grade reliability. Durable agents have full support for [streaming](../../agents/#streaming-all-events) and [MCP](../../mcp/client/), with the added benefit of fault tolerance.

Pydantic AI natively supports three durable execution solutions:

These integrations only use Pydantic AI's public interface, so they also serve as a reference for integrating with other durable systems.
