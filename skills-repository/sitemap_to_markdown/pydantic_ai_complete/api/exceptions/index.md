---
url: https://ai.pydantic.dev/api/exceptions/
date: 2026-01-03T23:40:33.137543
---

Bases: `[Exception](https://docs.python.org/3/library/exceptions.html#Exception)`

Exception to raise when a tool function should be retried.

The agent will return the message to the model and ask it to try calling the function/tool again.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`
    
    
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
    65
    66
    67
    68
    69

| 
    
    
    class ModelRetry(Exception):
        """Exception to raise when a tool function should be retried.
    
        The agent will return the message to the model and ask it to try calling the function/tool again.
        """
    
        message: str
        """The message to return to the model."""
    
        def __init__(self, message: str):
            self.message = message
            super().__init__(message)
    
        def __eq__(self, other: Any) -> bool:
            return isinstance(other, self.__class__) and other.message == self.message
    
        def __hash__(self) -> int:
            return hash((self.__class__, self.message))
    
        @classmethod
        def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> core_schema.CoreSchema:
            """Pydantic core schema to allow `ModelRetry` to be (de)serialized."""
            schema = core_schema.typed_dict_schema(
                {
                    'message': core_schema.typed_dict_field(core_schema.str_schema()),
                    'kind': core_schema.typed_dict_field(core_schema.literal_schema(['model-retry'])),
                }
            )
            return core_schema.no_info_after_validator_function(
                lambda dct: ModelRetry(dct['message']),
                schema,
                serialization=core_schema.plain_serializer_function_ser_schema(
                    lambda x: {'message': x.message, 'kind': 'model-retry'},
                    return_schema=schema,
                ),
            )
      
  
---|---  
  
####  message `instance-attribute`

The message to return to the model.

####  __get_pydantic_core_schema__ `classmethod`
    
    
    __get_pydantic_core_schema__(_: [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any"), __: [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")) -> CoreSchema
    

Pydantic core schema to allow `ModelRetry` to be (de)serialized.

Source code in `pydantic_ai_slim/pydantic_ai/exceptions.py`
    
    
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
    65
    66
    67
    68
    69

| 
    
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _: Any, __: Any) -> core_schema.CoreSchema:
        """Pydantic core schema to allow `ModelRetry` to be (de)serialized."""
        schema = core_schema.typed_dict_schema(
            {
                'message': core_schema.typed_dict_field(core_schema.str_schema()),
                'kind': core_schema.typed_dict_field(core_schema.literal_schema(['model-retry'])),
            }
        )
        return core_schema.no_info_after_validator_function(
            lambda dct: ModelRetry(dct['message']),
            schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: {'message': x.message, 'kind': 'model-retry'},
                return_schema=schema,
            ),
        )
      
  
---|---
