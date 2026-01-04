---
url: https://ai.pydantic.dev/api/pydantic_graph/beta_node/
date: 2026-01-03T23:41:33.047348
---

Bases: `[Generic](https://docs.python.org/3/library/typing.html#typing.Generic "typing.Generic")[InputT, OutputT]`

Fork node that creates parallel execution branches.

A Fork node splits the execution flow into multiple parallel branches, enabling concurrent execution of downstream nodes. It can either map a sequence across multiple branches or duplicate data to each branch.

Source code in `pydantic_graph/pydantic_graph/beta/node.py`
    
    
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

| 
    
    
    @dataclass
    class Fork(Generic[InputT, OutputT]):
        """Fork node that creates parallel execution branches.
    
        A Fork node splits the execution flow into multiple parallel branches,
        enabling concurrent execution of downstream nodes. It can either map
        a sequence across multiple branches or duplicate data to each branch.
        """
    
        id: ForkID
        """Unique identifier for this fork node."""
    
        is_map: bool
        """Determines fork behavior.
    
        If True, InputT must be Sequence[OutputT] and each element is sent to a separate branch.
        If False, InputT must be OutputT and the same data is sent to all branches.
        """
        downstream_join_id: JoinID | None
        """Optional identifier of a downstream join node that should be jumped to if mapping an empty iterable."""
    
        def _force_variance(self, inputs: InputT) -> OutputT:  # pragma: no cover
            """Force type variance for proper generic typing.
    
            This method exists solely for type checking purposes and should never be called.
    
            Args:
                inputs: Input data to be forked.
    
            Returns:
                Output data type (never actually returned).
    
            Raises:
                RuntimeError: Always, as this method should never be executed.
            """
            raise RuntimeError('This method should never be called, it is just defined for typing purposes.')
      
  
---|---  
  
####  id `instance-attribute`

Unique identifier for this fork node.

####  is_map `instance-attribute`

Determines fork behavior.

If True, InputT must be Sequence[OutputT] and each element is sent to a separate branch. If False, InputT must be OutputT and the same data is sent to all branches.

####  downstream_join_id `instance-attribute`
    
    
    downstream_join_id: JoinID | None
    

Optional identifier of a downstream join node that should be jumped to if mapping an empty iterable.
