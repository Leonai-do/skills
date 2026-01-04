---
url: https://ai.pydantic.dev/api/output/
date: 2026-01-03T23:40:50.028620
---

Bases: `[Generic](https://docs.python.org/3/library/typing.html#typing.Generic "typing.Generic")[OutputDataT]`

Marker class to use a prompt to tell the model what to output and optionally customize the prompt.

Example: 

prompted_output.py
    
    
    from pydantic import BaseModel
    
    from pydantic_ai import Agent, PromptedOutput
    
    from tool_output import Vehicle
    
    
    class Device(BaseModel):
        name: str
        kind: str
    
    
    agent = Agent(
        'openai:gpt-4o',
        output_type=PromptedOutput(
            [Vehicle, Device],
            name='Vehicle or device',
            description='Return a vehicle or device.'
        ),
    )
    result = agent.run_sync('What is a MacBook?')
    print(repr(result.output))
    #> Device(name='MacBook', kind='laptop')
    
    agent = Agent(
        'openai:gpt-4o',
        output_type=PromptedOutput(
            [Vehicle, Device],
            template='Gimme some JSON: {schema}'
        ),
    )
    result = agent.run_sync('What is a Ford Explorer?')
    print(repr(result.output))
    #> Vehicle(name='Ford Explorer', wheels=4)
    

Source code in `pydantic_ai_slim/pydantic_ai/output.py`
    
    
    190
    191
    192
    193
    194
    195
    196
    197
    198
    199
    200
    201
    202
    203
    204
    205
    206
    207
    208
    209
    210
    211
    212
    213
    214
    215
    216
    217
    218
    219
    220
    221
    222
    223
    224
    225
    226
    227
    228
    229
    230
    231
    232
    233
    234
    235
    236
    237
    238
    239
    240
    241
    242
    243
    244
    245
    246
    247
    248
    249
    250
    251
    252
    253
    254
    255
    256

| 
    
    
    @dataclass(init=False)
    class PromptedOutput(Generic[OutputDataT]):
        """Marker class to use a prompt to tell the model what to output and optionally customize the prompt.
    
        Example:
        ```python {title="prompted_output.py" requires="tool_output.py"}
        from pydantic import BaseModel
    
        from pydantic_ai import Agent, PromptedOutput
    
        from tool_output import Vehicle
    
    
        class Device(BaseModel):
            name: str
            kind: str
    
    
        agent = Agent(
            'openai:gpt-4o',
            output_type=PromptedOutput(
                [Vehicle, Device],
                name='Vehicle or device',
                description='Return a vehicle or device.'
            ),
        )
        result = agent.run_sync('What is a MacBook?')
        print(repr(result.output))
        #> Device(name='MacBook', kind='laptop')
    
        agent = Agent(
            'openai:gpt-4o',
            output_type=PromptedOutput(
                [Vehicle, Device],
                template='Gimme some JSON: {schema}'
            ),
        )
        result = agent.run_sync('What is a Ford Explorer?')
        print(repr(result.output))
        #> Vehicle(name='Ford Explorer', wheels=4)
        ```
        """
    
        outputs: OutputTypeOrFunction[OutputDataT] | Sequence[OutputTypeOrFunction[OutputDataT]]
        """The output types or functions."""
        name: str | None
        """The name of the structured output that will be passed to the model. If not specified and only one output is provided, the name of the output type or function will be used."""
        description: str | None
        """The description that will be passed to the model. If not specified and only one output is provided, the docstring of the output type or function will be used."""
        template: str | None
        """Template for the prompt passed to the model.
        The '{schema}' placeholder will be replaced with the output JSON schema.
        If not specified, the default template specified on the model's profile will be used.
        """
    
        def __init__(
            self,
            outputs: OutputTypeOrFunction[OutputDataT] | Sequence[OutputTypeOrFunction[OutputDataT]],
            *,
            name: str | None = None,
            description: str | None = None,
            template: str | None = None,
        ):
            self.outputs = outputs
            self.name = name
            self.description = description
            self.template = template
      
  
---|---  
  
####  outputs `instance-attribute`

The output types or functions.

####  name `instance-attribute`

The name of the structured output that will be passed to the model. If not specified and only one output is provided, the name of the output type or function will be used.

####  description `instance-attribute`
    
    
    description: [str](https://docs.python.org/3/library/stdtypes.html#str) | None = description
    

The description that will be passed to the model. If not specified and only one output is provided, the docstring of the output type or function will be used.

####  template `instance-attribute`
    
    
    template: [str](https://docs.python.org/3/library/stdtypes.html#str) | None = template
    

Template for the prompt passed to the model. The '{schema}' placeholder will be replaced with the output JSON schema. If not specified, the default template specified on the model's profile will be used.
