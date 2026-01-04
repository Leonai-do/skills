---
url: https://ai.pydantic.dev/third-party-tools/
date: 2026-01-03T23:40:19.992223
---

Pydantic AI supports integration with various third-party tool libraries, allowing you to leverage existing tool ecosystems in your agents.

See the [MCP Client](../mcp/client/) documentation for how to use MCP servers with Pydantic AI as [toolsets](../toolsets/).

If you'd like to use a tool from LangChain's [community tool library](https://python.langchain.com/docs/integrations/tools/) with Pydantic AI, you can use the [`tool_from_langchain`](../api/ext/#pydantic_ai.ext.langchain.tool_from_langchain "tool_from_langchain") convenience method. Note that Pydantic AI will not validate the arguments in this case -- it's up to the model to provide arguments matching the schema specified by the LangChain tool, and up to the LangChain tool to raise an error if the arguments are invalid.

You will need to install the `langchain-community` package and any others required by the tool in question.

Here is how you can use the LangChain `DuckDuckGoSearchRun` tool, which requires the `ddgs` package:
    
    
    from langchain_community.tools import DuckDuckGoSearchRun
    
    from pydantic_ai import Agent
    from pydantic_ai.ext.langchain import tool_from_langchain
    
    search = DuckDuckGoSearchRun()
    search_tool = tool_from_langchain(search)
    
    agent = Agent(
        'google-gla:gemini-2.5-flash',
        tools=[search_tool],
    )
    
    result = agent.run_sync('What is the release date of Elden Ring Nightreign?')  # (1)!
    print(result.output)
    #> Elden Ring Nightreign is planned to be released on May 30, 2025.
    

  1. The release date of this game is the 30th of May 2025, which is after the knowledge cutoff for Gemini 2.0 (August 2024).

If you'd like to use multiple LangChain tools or a LangChain [toolkit](https://python.langchain.com/docs/concepts/tools/#toolkits), you can use the [`LangChainToolset`](../api/ext/#pydantic_ai.ext.langchain.LangChainToolset "LangChainToolset") [toolset](../toolsets/) which takes a list of LangChain tools:

If you'd like to use a tool from the [ACI.dev tool library](https://www.aci.dev/tools) with Pydantic AI, you can use the [`tool_from_aci`](../api/ext/#pydantic_ai.ext.aci.tool_from_aci "tool_from_aci") convenience method. Note that Pydantic AI will not validate the arguments in this case -- it's up to the model to provide arguments matching the schema specified by the ACI tool, and up to the ACI tool to raise an error if the arguments are invalid.

You will need to install the `aci-sdk` package, set your ACI API key in the `ACI_API_KEY` environment variable, and pass your ACI "linked account owner ID" to the function.

Here is how you can use the ACI.dev `TAVILY__SEARCH` tool:
    
    
    import os
    
    from pydantic_ai import Agent
    from pydantic_ai.ext.aci import tool_from_aci
    
    tavily_search = tool_from_aci(
        'TAVILY__SEARCH',
        linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
    )
    
    agent = Agent(
        'google-gla:gemini-2.5-flash',
        tools=[tavily_search],
    )
    
    result = agent.run_sync('What is the release date of Elden Ring Nightreign?')  # (1)!
    print(result.output)
    #> Elden Ring Nightreign is planned to be released on May 30, 2025.
    

  1. The release date of this game is the 30th of May 2025, which is after the knowledge cutoff for Gemini 2.0 (August 2024).

If you'd like to use multiple ACI.dev tools, you can use the [`ACIToolset`](../api/ext/#pydantic_ai.ext.aci.ACIToolset "ACIToolset") [toolset](../toolsets/) which takes a list of ACI tool names as well as the `linked_account_owner_id`:

With Pydantic AI GatewayDirectly to Provider API

[Learn about Gateway](../gateway)
    
    
    import os
    
    from pydantic_ai import Agent
    from pydantic_ai.ext.aci import ACIToolset
    
    toolset = ACIToolset(
        [
            'OPEN_WEATHER_MAP__CURRENT_WEATHER',
            'OPEN_WEATHER_MAP__FORECAST',
        ],
        linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
    )
    
    agent = Agent('gateway/openai:gpt-5', toolsets=[toolset])
    
    
    
    import os
    
    from pydantic_ai import Agent
    from pydantic_ai.ext.aci import ACIToolset
    
    toolset = ACIToolset(
        [
            'OPEN_WEATHER_MAP__CURRENT_WEATHER',
            'OPEN_WEATHER_MAP__FORECAST',
        ],
        linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
    )
    
    agent = Agent('openai:gpt-5', toolsets=[toolset])
    

## See Also
