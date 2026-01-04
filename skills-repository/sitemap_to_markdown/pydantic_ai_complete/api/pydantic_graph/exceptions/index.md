---
url: https://ai.pydantic.dev/api/pydantic_graph/exceptions/
date: 2026-01-03T23:41:41.428197
---

Bases: `GraphRuntimeError`

Error caused by trying to run a node that already has status `'running'`, `'success'`, or `'error'`.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`
    
    
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

| 
    
    
    class GraphNodeStatusError(GraphRuntimeError):
        """Error caused by trying to run a node that already has status `'running'`, `'success'`, or `'error'`."""
    
        def __init__(self, actual_status: 'SnapshotStatus'):
            self.actual_status = actual_status
            super().__init__(f"Incorrect snapshot status {actual_status!r}, must be 'created' or 'pending'.")
    
        @classmethod
        def check(cls, status: 'SnapshotStatus') -> None:
            """Check if the status is valid."""
            if status not in {'created', 'pending'}:
                raise cls(status)
      
  
---|---  
  
####  check `classmethod`

Check if the status is valid.

Source code in `pydantic_graph/pydantic_graph/exceptions.py`

| 
    
    
    @classmethod
    def check(cls, status: 'SnapshotStatus') -> None:
        """Check if the status is valid."""
        if status not in {'created', 'pending'}:
            raise cls(status)
      
  
---|---
