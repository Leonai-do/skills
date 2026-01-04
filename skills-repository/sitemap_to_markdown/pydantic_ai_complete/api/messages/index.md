---
url: https://ai.pydantic.dev/api/messages/
date: 2026-01-03T23:40:43.814738
---


    @dataclass(repr=False)
    class ModelResponse:
        """A response from a model, e.g. a message from the model to the Pydantic AI app."""
    
        parts: Sequence[ModelResponsePart]
        """The parts of the model message."""
    
        _: KW_ONLY
    
        usage: RequestUsage = field(default_factory=RequestUsage)
        """Usage information for the request.
    
        This has a default to make tests easier, and to support loading old messages where usage will be missing.
        """
    
        model_name: str | None = None
        """The name of the model that generated the response."""
    
        timestamp: datetime = field(default_factory=_now_utc)
        """The timestamp when the response was received locally.
    
        This is always a high-precision local datetime. Provider-specific timestamps
        (if available) are stored in `provider_details['timestamp']`.
        """
    
        kind: Literal['response'] = 'response'
        """Message type identifier, this is available on all parts as a discriminator."""
    
        provider_name: str | None = None
        """The name of the LLM provider that generated the response."""
    
        provider_url: str | None = None
        """The base URL of the LLM provider that generated the response."""
    
        provider_details: Annotated[
            dict[str, Any] | None,
            # `vendor_details` is deprecated, but we still want to support deserializing model responses stored in a DB before the name was changed
            pydantic.Field(validation_alias=pydantic.AliasChoices('provider_details', 'vendor_details')),
        ] = None
        """Additional data returned by the provider that can't be mapped to standard fields."""
    
        provider_response_id: Annotated[
            str | None,
            # `vendor_id` is deprecated, but we still want to support deserializing model responses stored in a DB before the name was changed
            pydantic.Field(validation_alias=pydantic.AliasChoices('provider_response_id', 'vendor_id')),
        ] = None
        """request ID as specified by the model provider. This can be used to track the specific request to the model."""
    
        finish_reason: FinishReason | None = None
        """Reason the model finished generating the response, normalized to OpenTelemetry values."""
    
        run_id: str | None = None
        """The unique identifier of the agent run in which this message originated."""
    
        metadata: dict[str, Any] | None = None
        """Additional data that can be accessed programmatically by the application but is not sent to the LLM."""
    
        @property
        def text(self) -> str | None:
            """Get the text in the response."""
            texts: list[str] = []
            last_part: ModelResponsePart | None = None
            for part in self.parts:
                if isinstance(part, TextPart):
                    # Adjacent text parts should be joined together, but if there are parts in between
                    # (like built-in tool calls) they should have newlines between them
                    if isinstance(last_part, TextPart):
                        texts[-1] += part.content
                    else:
                        texts.append(part.content)
                last_part = part
            if not texts:
                return None
    
            return '\n\n'.join(texts)
    
        @property
        def thinking(self) -> str | None:
            """Get the thinking in the response."""
            thinking_parts = [part.content for part in self.parts if isinstance(part, ThinkingPart)]
            if not thinking_parts:
                return None
            return '\n\n'.join(thinking_parts)
    
        @property
        def files(self) -> list[BinaryContent]:
            """Get the files in the response."""
            return [part.content for part in self.parts if isinstance(part, FilePart)]
    
        @property
        def images(self) -> list[BinaryImage]:
            """Get the images in the response."""
            return [file for file in self.files if isinstance(file, BinaryImage)]
    
        @property
        def tool_calls(self) -> list[ToolCallPart]:
            """Get the tool calls in the response."""
            return [part for part in self.parts if isinstance(part, ToolCallPart)]
    
        @property
        def builtin_tool_calls(self) -> list[tuple[BuiltinToolCallPart, BuiltinToolReturnPart]]:
            """Get the builtin tool calls and results in the response."""
            calls = [part for part in self.parts if isinstance(part, BuiltinToolCallPart)]
            if not calls:
                return []
            returns_by_id = {part.tool_call_id: part for part in self.parts if isinstance(part, BuiltinToolReturnPart)}
            return [
                (call_part, returns_by_id[call_part.tool_call_id])
                for call_part in calls
                if call_part.tool_call_id in returns_by_id
            ]
    
        @deprecated('`price` is deprecated, use `cost` instead')
        def price(self) -> genai_types.PriceCalculation:  # pragma: no cover
            return self.cost()
    
        def cost(self) -> genai_types.PriceCalculation:
            """Calculate the cost of the usage.
    
            Uses [`genai-prices`](https://github.com/pydantic/genai-prices).
            """
            assert self.model_name, 'Model name is required to calculate price'
            # Try matching on provider_api_url first as this is more specific, then fall back to provider_id.
            if self.provider_url:
                try:
                    return calc_price(
                        self.usage,
                        self.model_name,
                        provider_api_url=self.provider_url,
                        genai_request_timestamp=self.timestamp,
                    )
                except LookupError:
                    pass
            return calc_price(
                self.usage,
                self.model_name,
                provider_id=self.provider_name,
                genai_request_timestamp=self.timestamp,
            )
    
        def otel_events(self, settings: InstrumentationSettings) -> list[LogRecord]:
            """Return OpenTelemetry events for the response."""
            result: list[LogRecord] = []
    
            def new_event_body():
                new_body: dict[str, Any] = {'role': 'assistant'}
                ev = LogRecord(attributes={'event.name': 'gen_ai.assistant.message'}, body=new_body)
                result.append(ev)
                return new_body
    
            body = new_event_body()
            for part in self.parts:
                if isinstance(part, ToolCallPart):
                    body.setdefault('tool_calls', []).append(
                        {
                            'id': part.tool_call_id,
                            'type': 'function',
                            'function': {
                                'name': part.tool_name,
                                **({'arguments': part.args} if settings.include_content else {}),
                            },
                        }
                    )
                elif isinstance(part, TextPart | ThinkingPart):
                    kind = part.part_kind
                    body.setdefault('content', []).append(
                        {'kind': kind, **({'text': part.content} if settings.include_content else {})}
                    )
                elif isinstance(part, FilePart):
                    body.setdefault('content', []).append(
                        {
                            'kind': 'binary',
                            'media_type': part.content.media_type,
                            **(
                                {'binary_content': part.content.base64}
                                if settings.include_content and settings.include_binary_content
                                else {}
                            ),
                        }
                    )
    
            if content := body.get('content'):
                text_content = content[0].get('text')
                if content == [{'kind': 'text', 'text': text_content}]:
                    body['content'] = text_content
    
            return result
    
        def otel_message_parts(self, settings: InstrumentationSettings) -> list[_otel_messages.MessagePart]:
            parts: list[_otel_messages.MessagePart] = []
            for part in self.parts:
                if isinstance(part, TextPart):
                    parts.append(
                        _otel_messages.TextPart(
                            type='text',
                            **({'content': part.content} if settings.include_content else {}),
                        )
                    )
                elif isinstance(part, ThinkingPart):
                    parts.append(
                        _otel_messages.ThinkingPart(
                            type='thinking',
                            **({'content': part.content} if settings.include_content else {}),
                        )
                    )
                elif isinstance(part, FilePart):
                    converted_part = _otel_messages.BinaryDataPart(type='binary', media_type=part.content.media_type)
                    if settings.include_content and settings.include_binary_content:
                        converted_part['content'] = part.content.base64
                    parts.append(converted_part)
                elif isinstance(part, BaseToolCallPart):
                    call_part = _otel_messages.ToolCallPart(type='tool_call', id=part.tool_call_id, name=part.tool_name)
                    if isinstance(part, BuiltinToolCallPart):
                        call_part['builtin'] = True
                    if settings.include_content and part.args is not None:
                        from .models.instrumented import InstrumentedModel
    
                        if isinstance(part.args, str):
                            call_part['arguments'] = part.args
                        else:
                            call_part['arguments'] = {k: InstrumentedModel.serialize_any(v) for k, v in part.args.items()}
    
                    parts.append(call_part)
                elif isinstance(part, BuiltinToolReturnPart):
                    return_part = _otel_messages.ToolCallResponsePart(
                        type='tool_call_response',
                        id=part.tool_call_id,
                        name=part.tool_name,
                        builtin=True,
                    )
                    if settings.include_content and part.content is not None:  # pragma: no branch
                        from .models.instrumented import InstrumentedModel
    
                        return_part['result'] = InstrumentedModel.serialize_any(part.content)
    
                    parts.append(return_part)
            return parts
    
        @property
        @deprecated('`vendor_details` is deprecated, use `provider_details` instead')
        def vendor_details(self) -> dict[str, Any] | None:
            return self.provider_details
    
        @property
        @deprecated('`vendor_id` is deprecated, use `provider_response_id` instead')
        def vendor_id(self) -> str | None:
            return self.provider_response_id
    
        @property
        @deprecated('`provider_request_id` is deprecated, use `provider_response_id` instead')
        def provider_request_id(self) -> str | None:
            return self.provider_response_id
    
        __repr__ = _utils.dataclasses_no_defaults_repr
    
