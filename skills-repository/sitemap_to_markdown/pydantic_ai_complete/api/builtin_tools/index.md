---
url: https://ai.pydantic.dev/api/builtin_tools/
date: 2026-01-03T23:40:25.423878
---

Bases: `AbstractBuiltinTool`

A builtin tool that allows your agent to search through uploaded files using vector search.

This tool provides a fully managed Retrieval-Augmented Generation (RAG) system that handles file storage, chunking, embedding generation, and context injection into prompts.

Supported by:

  - OpenAI Responses
  - Google (Gemini)

Source code in `pydantic_ai_slim/pydantic_ai/builtin_tools.py`
    
    
    433
    434
    435
    436
    437
    438
    439
    440
    441
    442
    443
    444
    445
    446
    447
    448
    449
    450
    451
    452
    453
    454

| 
    
    
    @dataclass(kw_only=True)
    class FileSearchTool(AbstractBuiltinTool):
        """A builtin tool that allows your agent to search through uploaded files using vector search.
    
        This tool provides a fully managed Retrieval-Augmented Generation (RAG) system that handles
        file storage, chunking, embedding generation, and context injection into prompts.
    
        Supported by:
    
        * OpenAI Responses
        * Google (Gemini)
        """
    
        file_store_ids: Sequence[str]
        """The file store IDs to search through.
    
        For OpenAI, these are the IDs of vector stores created via the OpenAI API.
        For Google, these are file search store names that have been uploaded and processed via the Gemini Files API.
        """
    
        kind: str = 'file_search'
        """The kind of tool."""
      
  
---|---  
  
The file store IDs to search through.

For OpenAI, these are the IDs of vector stores created via the OpenAI API. For Google, these are file search store names that have been uploaded and processed via the Gemini Files API.
    
    
    kind: [str](https://docs.python.org/3/library/stdtypes.html#str) = 'file_search'
    
