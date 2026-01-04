---
url: https://ai.pydantic.dev/api/ext/
date: 2026-01-03T23:40:42.822194
---

Creates a Pydantic AI tool proxy from a LangChain tool.

Parameters:

Name | Type | Description | Default  
---|---|---|---  
`langchain_tool` |  `LangChainTool` |  The LangChain tool to wrap. |  _required_  
  
Returns:

Type | Description  
---|---  
`[Tool](../tools/#pydantic_ai.tools.Tool "Tool

  
      dataclass
   \(pydantic_ai.tools.Tool\)")` |  A Pydantic AI tool that corresponds to the LangChain tool.  
Source code in `pydantic_ai_slim/pydantic_ai/ext/langchain.py`
    
    
    32
    33
    34
    35
    36
    37
    38
    39
    40
    41
    42
    43
    44
    45
    46
    47
    48
    49
    50
    51
    52
    53
    54
    55
    56
    57
    58
    59
    60
    61
    62
    63
    64

| 
    
    
    def tool_from_langchain(langchain_tool: LangChainTool) -> Tool:
        """Creates a Pydantic AI tool proxy from a LangChain tool.
    
        Args:
            langchain_tool: The LangChain tool to wrap.
    
        Returns:
            A Pydantic AI tool that corresponds to the LangChain tool.
        """
        function_name = langchain_tool.name
        function_description = langchain_tool.description
        inputs = langchain_tool.args.copy()
        required = sorted({name for name, detail in inputs.items() if 'default' not in detail})
        schema: JsonSchemaValue = langchain_tool.get_input_jsonschema()
        if 'additionalProperties' not in schema:
            schema['additionalProperties'] = False
        if required:
            schema['required'] = required
    
        defaults = {name: detail['default'] for name, detail in inputs.items() if 'default' in detail}
    
        # restructures the arguments to match langchain tool run
        def proxy(*args: Any, **kwargs: Any) -> str:
            assert not args, 'This should always be called with kwargs'
            kwargs = defaults | kwargs
            return langchain_tool.run(kwargs)
    
        return Tool.from_schema(
            function=proxy,
            name=function_name,
            description=function_description,
            json_schema=schema,
        )
      
  
---|---
