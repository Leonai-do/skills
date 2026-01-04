---
url: https://ai.pydantic.dev/api/pydantic_graph/beta_step/
date: 2026-01-03T23:41:32.995994
---

Bases: `Step[StateT, DepsT, [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any"), [BaseNode](../nodes/#pydantic_graph.nodes.BaseNode "BaseNode \(pydantic_graph.nodes.BaseNode\)")[StateT, DepsT, [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")] | [End](../nodes/#pydantic_graph.nodes.End "End

  
      dataclass
   \(pydantic_graph.nodes.End\)")[[Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")]]`

A step that wraps a BaseNode type for execution.

NodeStep allows v1-style BaseNode classes to be used as steps in the v2 graph execution system. It validates that the input is of the expected node type and runs it with the appropriate graph context.

Source code in `pydantic_graph/pydantic_graph/beta/step.py`
    
    
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

| 
    
    
    class NodeStep(Step[StateT, DepsT, Any, BaseNode[StateT, DepsT, Any] | End[Any]]):
        """A step that wraps a BaseNode type for execution.
    
        NodeStep allows v1-style BaseNode classes to be used as steps in the
        v2 graph execution system. It validates that the input is of the expected
        node type and runs it with the appropriate graph context.
        """
    
        node_type: type[BaseNode[StateT, DepsT, Any]]
        """The BaseNode type this step executes."""
    
        def __init__(
            self,
            node_type: type[BaseNode[StateT, DepsT, Any]],
            *,
            id: NodeID | None = None,
            label: str | None = None,
        ):
            """Initialize a node step.
    
            Args:
                node_type: The BaseNode class this step will execute
                id: Optional unique identifier, defaults to the node's get_node_id()
                label: Optional human-readable label for this step
            """
            super().__init__(
                id=id or NodeID(node_type.get_node_id()),
                call=self._call_node,
                label=label,
            )
            # `type[BaseNode[StateT, DepsT, Any]]` could actually be a `typing._GenericAlias` like `pydantic_ai._agent_graph.UserPromptNode[~DepsT, ~OutputT]`,
            # so we get the origin to get to the actual class
            self.node_type = get_origin(node_type) or node_type
    
        async def _call_node(self, ctx: StepContext[StateT, DepsT, Any]) -> BaseNode[StateT, DepsT, Any] | End[Any]:
            """Execute the wrapped node with the step context.
    
            Args:
                ctx: The step context containing the node instance to run
    
            Returns:
                The result of running the node, either another BaseNode or End
    
            Raises:
                ValueError: If the input node is not of the expected type
            """
            node = ctx.inputs
            if not isinstance(node, self.node_type):
                raise ValueError(f'Node {node} is not of type {self.node_type}')  # pragma: no cover
            node = cast(BaseNode[StateT, DepsT, Any], node)
            return await node.run(GraphRunContext(state=ctx.state, deps=ctx.deps))
      
  
---|---  
  
####  __init__
    
    
    __init__(
        node_type: [type](https://docs.python.org/3/library/functions.html#type)[[BaseNode](../nodes/#pydantic_graph.nodes.BaseNode "BaseNode \(pydantic_graph.nodes.BaseNode\)")[StateT, DepsT, [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")]],
        *,
        id: NodeID | None = None,
        label: [str](https://docs.python.org/3/library/stdtypes.html#str) | None = None
    )
    

Initialize a node step.

Parameters:

Name | Type | Description | Default  
---|---|---|---  
`node_type` |  `[type](https://docs.python.org/3/library/functions.html#type)[[BaseNode](../nodes/#pydantic_graph.nodes.BaseNode "BaseNode \(pydantic_graph.nodes.BaseNode\)")[StateT, DepsT, [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")]]` |  The BaseNode class this step will execute |  _required_  
`id` |  `NodeID | None` |  Optional unique identifier, defaults to the node's get_node_id() |  `None`  
`label` |  `[str](https://docs.python.org/3/library/stdtypes.html#str) | None` |  Optional human-readable label for this step |  `None`  
Source code in `pydantic_graph/pydantic_graph/beta/step.py`
    
    
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

| 
    
    
    def __init__(
        self,
        node_type: type[BaseNode[StateT, DepsT, Any]],
        *,
        id: NodeID | None = None,
        label: str | None = None,
    ):
        """Initialize a node step.
    
        Args:
            node_type: The BaseNode class this step will execute
            id: Optional unique identifier, defaults to the node's get_node_id()
            label: Optional human-readable label for this step
        """
        super().__init__(
            id=id or NodeID(node_type.get_node_id()),
            call=self._call_node,
            label=label,
        )
        # `type[BaseNode[StateT, DepsT, Any]]` could actually be a `typing._GenericAlias` like `pydantic_ai._agent_graph.UserPromptNode[~DepsT, ~OutputT]`,
        # so we get the origin to get to the actual class
        self.node_type = get_origin(node_type) or node_type
      
  
---|---  
  
####  node_type `instance-attribute`

The BaseNode type this step executes.
