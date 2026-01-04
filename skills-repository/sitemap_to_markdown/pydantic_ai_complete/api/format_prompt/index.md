---
url: https://ai.pydantic.dev/api/format_prompt/
date: 2026-01-03T23:40:42.767832
---


    format_as_xml(
        obj: [Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any"),
        root_tag: [str](https://docs.python.org/3/library/stdtypes.html#str) | None = None,
        item_tag: [str](https://docs.python.org/3/library/stdtypes.html#str) = "item",
        none_str: [str](https://docs.python.org/3/library/stdtypes.html#str) = "null",
        indent: [str](https://docs.python.org/3/library/stdtypes.html#str) | None = "  ",
        include_field_info: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal "typing.Literal")["once"] | [bool](https://docs.python.org/3/library/functions.html#bool) = False,
    ) -> [str](https://docs.python.org/3/library/stdtypes.html#str)
    

Format a Python object as XML.

This is useful since LLMs often find it easier to read semi-structured data (e.g. examples) as XML, rather than JSON etc.

Supports: `str`, `bytes`, `bytearray`, `bool`, `int`, `float`, `date`, `datetime`, `time`, `timedelta`, `Enum`, `Mapping`, `Iterable`, `dataclass`, and `BaseModel`.

Parameters:

Name | Type | Description | Default  
---|---|---|---  
`obj` |  `[Any](https://docs.python.org/3/library/typing.html#typing.Any "typing.Any")` |  Python Object to serialize to XML. |  _required_  
`root_tag` |  `[str](https://docs.python.org/3/library/stdtypes.html#str) | None` |  Outer tag to wrap the XML in, use `None` to omit the outer tag. |  `None`  
`item_tag` |  `[str](https://docs.python.org/3/library/stdtypes.html#str)` |  Tag to use for each item in an iterable (e.g. list), this is overridden by the class name for dataclasses and Pydantic models. |  `'item'`  
`none_str` |  `[str](https://docs.python.org/3/library/stdtypes.html#str)` |  String to use for `None` values. |  `'null'`  
`indent` |  `[str](https://docs.python.org/3/library/stdtypes.html#str) | None` |  Indentation string to use for pretty printing. |  `' '`  
`include_field_info` |  `[Literal](https://docs.python.org/3/library/typing.html#typing.Literal "typing.Literal")['once'] | [bool](https://docs.python.org/3/library/functions.html#bool)` |  Whether to include attributes like Pydantic `Field` attributes and dataclasses `field()` `metadata` as XML attributes. In both cases the allowed `Field` attributes and `field()` metadata keys are `title` and `description`. If a field is repeated in the data (e.g. in a list) by setting `once` the attributes are included only in the first occurrence of an XML element relative to the same field. |  `False`  
  
Returns:

Type | Description  
---|---  
`[str](https://docs.python.org/3/library/stdtypes.html#str)` |  XML representation of the object.  
  
Example: 

format_as_xml_example.py
    
    
    from pydantic_ai import format_as_xml
    
    print(format_as_xml({'name': 'John', 'height': 6, 'weight': 200}, root_tag='user'))
    '''
    <user>
      <name>John</name>
      <height>6</height>
      <weight>200</weight>
    </user>
    '''
    

Source code in `pydantic_ai_slim/pydantic_ai/format_prompt.py`
    
    
    17
    18
    19
    20
    21
    22
    23
    24
    25
    26
    27
    28
    29
    30
    31
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

| 
    
    
    def format_as_xml(
        obj: Any,
        root_tag: str | None = None,
        item_tag: str = 'item',
        none_str: str = 'null',
        indent: str | None = '  ',
        include_field_info: Literal['once'] | bool = False,
    ) -> str:
        """Format a Python object as XML.
    
        This is useful since LLMs often find it easier to read semi-structured data (e.g. examples) as XML,
        rather than JSON etc.
    
        Supports: `str`, `bytes`, `bytearray`, `bool`, `int`, `float`, `date`, `datetime`, `time`, `timedelta`, `Enum`,
        `Mapping`, `Iterable`, `dataclass`, and `BaseModel`.
    
        Args:
            obj: Python Object to serialize to XML.
            root_tag: Outer tag to wrap the XML in, use `None` to omit the outer tag.
            item_tag: Tag to use for each item in an iterable (e.g. list), this is overridden by the class name
                for dataclasses and Pydantic models.
            none_str: String to use for `None` values.
            indent: Indentation string to use for pretty printing.
            include_field_info: Whether to include attributes like Pydantic `Field` attributes and dataclasses `field()`
                `metadata` as XML attributes. In both cases the allowed `Field` attributes and `field()` metadata keys are
                `title` and `description`. If a field is repeated in the data (e.g. in a list) by setting `once`
                the attributes are included only in the first occurrence of an XML element relative to the same field.
    
        Returns:
            XML representation of the object.
    
        Example:
        ```python {title="format_as_xml_example.py" lint="skip"}
        from pydantic_ai import format_as_xml
    
        print(format_as_xml({'name': 'John', 'height': 6, 'weight': 200}, root_tag='user'))
        '''
        <user>
          <name>John</name>
          <height>6</height>
          <weight>200</weight>
        </user>
        '''
        ```
        """
        el = _ToXml(
            data=obj,
            item_tag=item_tag,
            none_str=none_str,
            include_field_info=include_field_info,
        ).to_xml(root_tag)
        if root_tag is None and el.text is None:
            join = '' if indent is None else '\n'
            return join.join(_rootless_xml_elements(el, indent))
        else:
            if indent is not None:
                ElementTree.indent(el, space=indent)
            return ElementTree.tostring(el, encoding='unicode')
      
  
---|---
