---
url: https://ai.pydantic.dev/api/models/cerebras/
date: 2026-01-03T23:41:02.571178
---

Bases: `[OpenAIChatModel](../openai/#pydantic_ai.models.openai.OpenAIChatModel "OpenAIChatModel

  
      dataclass
   \(pydantic_ai.models.openai.OpenAIChatModel\)")`

A model that uses Cerebras's OpenAI-compatible API.

Cerebras provides ultra-fast inference powered by the Wafer-Scale Engine (WSE).

Apart from `__init__`, all methods are private or match those of the base class.

Source code in `pydantic_ai_slim/pydantic_ai/models/cerebras.py`
    
    
    61
    62
    63
    64
    65
    66
    67
    68
    69
    70
    71
    72
    73
    74
    75
    76
    77
    78
    79
    80
    81
    82
    83
    84
    85
    86
    87
    88
    89
    90
    91
    92
    93
    94
    95
    96

| 
    
    
    @dataclass(init=False)
    class CerebrasModel(OpenAIChatModel):
        """A model that uses Cerebras's OpenAI-compatible API.
    
        Cerebras provides ultra-fast inference powered by the Wafer-Scale Engine (WSE).
    
        Apart from `__init__`, all methods are private or match those of the base class.
        """
    
        def __init__(
            self,
            model_name: CerebrasModelName,
            *,
            provider: Literal['cerebras'] | Provider[AsyncOpenAI] = 'cerebras',
            profile: ModelProfileSpec | None = None,
            settings: CerebrasModelSettings | None = None,
        ):
            """Initialize a Cerebras model.
    
            Args:
                model_name: The name of the Cerebras model to use.
                provider: The provider to use. Defaults to 'cerebras'.
                profile: The model profile to use. Defaults to a profile based on the model name.
                settings: Model-specific settings that will be used as defaults for this model.
            """
            super().__init__(model_name, provider=provider, profile=profile, settings=settings)
    
        @override
        def prepare_request(
            self,
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> tuple[ModelSettings | None, ModelRequestParameters]:
            merged_settings, customized_parameters = super().prepare_request(model_settings, model_request_parameters)
            new_settings = _cerebras_settings_to_openai_settings(cast(CerebrasModelSettings, merged_settings or {}))
            return new_settings, customized_parameters
      
  
---|---  
  
####  __init__

Initialize a Cerebras model.

Parameters:

Name | Type | Description | Default  
---|---|---|---  
`model_name` |  `CerebrasModelName` |  The name of the Cerebras model to use. |  _required_  
`provider` |  `[Literal](https://docs.python.org/3/library/typing.html#typing.Literal "typing.Literal")['cerebras'] | [Provider](../../providers/#pydantic_ai.providers.Provider "pydantic_ai.providers.Provider")[AsyncOpenAI]` |  The provider to use. Defaults to 'cerebras'. |  `'cerebras'`  
`profile` |  `ModelProfileSpec | None` |  The model profile to use. Defaults to a profile based on the model name. |  `None`  
`settings` |  `CerebrasModelSettings | None` |  Model-specific settings that will be used as defaults for this model. |  `None`  
Source code in `pydantic_ai_slim/pydantic_ai/models/cerebras.py`
    
    
    70
    71
    72
    73
    74
    75
    76
    77
    78
    79
    80
    81
    82
    83
    84
    85
    86

| 
    
    
    def __init__(
        self,
        model_name: CerebrasModelName,
        *,
        provider: Literal['cerebras'] | Provider[AsyncOpenAI] = 'cerebras',
        profile: ModelProfileSpec | None = None,
        settings: CerebrasModelSettings | None = None,
    ):
        """Initialize a Cerebras model.
    
        Args:
            model_name: The name of the Cerebras model to use.
            provider: The provider to use. Defaults to 'cerebras'.
            profile: The model profile to use. Defaults to a profile based on the model name.
            settings: Model-specific settings that will be used as defaults for this model.
        """
        super().__init__(model_name, provider=provider, profile=profile, settings=settings)
      
  
---|---
