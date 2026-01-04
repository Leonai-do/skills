---
url: https://ai.pydantic.dev/api/ui/base/
date: 2026-01-03T23:41:47.551294
---


    @dataclass
    class UIAdapter(ABC, Generic[RunInputT, MessageT, EventT, AgentDepsT, OutputDataT]):
        """Base class for UI adapters.
    
        This class is responsible for transforming agent run input received from the frontend into arguments for [`Agent.run_stream_events()`][pydantic_ai.agent.Agent.run_stream_events], running the agent, and then transforming Pydantic AI events into protocol-specific events.
    
        The event stream transformation is handled by a protocol-specific [`UIEventStream`][pydantic_ai.ui.UIEventStream] subclass.
        """
    
        agent: AbstractAgent[AgentDepsT, OutputDataT]
        """The Pydantic AI agent to run."""
    
        run_input: RunInputT
        """The protocol-specific run input object."""
    
        _: KW_ONLY
    
        accept: str | None = None
        """The `Accept` header value of the request, used to determine how to encode the protocol-specific events for the streaming response."""
    
        @classmethod
        async def from_request(
            cls, request: Request, *, agent: AbstractAgent[AgentDepsT, OutputDataT]
        ) -> UIAdapter[RunInputT, MessageT, EventT, AgentDepsT, OutputDataT]:
            """Create an adapter from a request."""
            return cls(
                agent=agent,
                run_input=cls.build_run_input(await request.body()),
                accept=request.headers.get('accept'),
            )
    
        @classmethod
        @abstractmethod
        def build_run_input(cls, body: bytes) -> RunInputT:
            """Build a protocol-specific run input object from the request body."""
            raise NotImplementedError
    
        @classmethod
        @abstractmethod
        def load_messages(cls, messages: Sequence[MessageT]) -> list[ModelMessage]:
            """Transform protocol-specific messages into Pydantic AI messages."""
            raise NotImplementedError
    
        @classmethod
        def dump_messages(cls, messages: Sequence[ModelMessage]) -> list[MessageT]:
            """Transform Pydantic AI messages into protocol-specific messages."""
            raise NotImplementedError
    
        @abstractmethod
        def build_event_stream(self) -> UIEventStream[RunInputT, EventT, AgentDepsT, OutputDataT]:
            """Build a protocol-specific event stream transformer."""
            raise NotImplementedError
    
        @cached_property
        @abstractmethod
        def messages(self) -> list[ModelMessage]:
            """Pydantic AI messages from the protocol-specific run input."""
            raise NotImplementedError
    
        @cached_property
        def toolset(self) -> AbstractToolset[AgentDepsT] | None:
            """Toolset representing frontend tools from the protocol-specific run input."""
            return None
    
        @cached_property
        def state(self) -> dict[str, Any] | None:
            """Frontend state from the protocol-specific run input."""
            return None
    
        def transform_stream(
            self,
            stream: AsyncIterator[NativeEvent],
            on_complete: OnCompleteFunc[EventT] | None = None,
        ) -> AsyncIterator[EventT]:
            """Transform a stream of Pydantic AI events into protocol-specific events.
    
            Args:
                stream: The stream of Pydantic AI events to transform.
                on_complete: Optional callback function called when the agent run completes successfully.
                    The callback receives the completed [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] and can optionally yield additional protocol-specific events.
            """
            return self.build_event_stream().transform_stream(stream, on_complete=on_complete)
    
        def encode_stream(self, stream: AsyncIterator[EventT]) -> AsyncIterator[str]:
            """Encode a stream of protocol-specific events as strings according to the `Accept` header value.
    
            Args:
                stream: The stream of protocol-specific events to encode.
            """
            return self.build_event_stream().encode_stream(stream)
    
        def streaming_response(self, stream: AsyncIterator[EventT]) -> StreamingResponse:
            """Generate a streaming response from a stream of protocol-specific events.
    
            Args:
                stream: The stream of protocol-specific events to encode.
            """
            return self.build_event_stream().streaming_response(stream)
    
        def run_stream_native(
            self,
            *,
            output_type: OutputSpec[Any] | None = None,
            message_history: Sequence[ModelMessage] | None = None,
            deferred_tool_results: DeferredToolResults | None = None,
            model: Model | KnownModelName | str | None = None,
            instructions: Instructions[AgentDepsT] = None,
            deps: AgentDepsT = None,
            model_settings: ModelSettings | None = None,
            usage_limits: UsageLimits | None = None,
            usage: RunUsage | None = None,
            metadata: AgentMetadata[AgentDepsT] | None = None,
            infer_name: bool = True,
            toolsets: Sequence[AbstractToolset[AgentDepsT]] | None = None,
            builtin_tools: Sequence[AbstractBuiltinTool] | None = None,
        ) -> AsyncIterator[NativeEvent]:
            """Run the agent with the protocol-specific run input and stream Pydantic AI events.
    
            Args:
                output_type: Custom output type to use for this run, `output_type` may only be used if the agent has no
                    output validators since output validators would expect an argument that matches the agent's output type.
                message_history: History of the conversation so far.
                deferred_tool_results: Optional results for deferred tool calls in the message history.
                model: Optional model to use for this run, required if `model` was not set when creating the agent.
                instructions: Optional additional instructions to use for this run.
                deps: Optional dependencies to use for this run.
                model_settings: Optional settings to use for this model's request.
                usage_limits: Optional limits on model request count or token usage.
                usage: Optional usage to start with, useful for resuming a conversation or agents used in tools.
                metadata: Optional metadata to attach to this run. Accepts a dictionary or a callable taking
                    [`RunContext`][pydantic_ai.tools.RunContext]; merged with the agent's configured metadata.
                infer_name: Whether to try to infer the agent name from the call frame if it's not set.
                toolsets: Optional additional toolsets for this run.
                builtin_tools: Optional additional builtin tools to use for this run.
            """
            message_history = [*(message_history or []), *self.messages]
    
            toolset = self.toolset
            if toolset:
                output_type = [output_type or self.agent.output_type, DeferredToolRequests]
                toolsets = [*(toolsets or []), toolset]
    
            if isinstance(deps, StateHandler):
                raw_state = self.state or {}
                if isinstance(deps.state, BaseModel):
                    state = type(deps.state).model_validate(raw_state)
                else:
                    state = raw_state
    
                deps.state = state
            elif self.state:
                warnings.warn(
                    f'State was provided but `deps` of type `{type(deps).__name__}` does not implement the `StateHandler` protocol, so the state was ignored. Use `StateDeps[...]` or implement `StateHandler` to receive AG-UI state.',
                    UserWarning,
                    stacklevel=2,
                )
    
            return self.agent.run_stream_events(
                output_type=output_type,
                message_history=message_history,
                deferred_tool_results=deferred_tool_results,
                model=model,
                deps=deps,
                model_settings=model_settings,
                instructions=instructions,
                usage_limits=usage_limits,
                usage=usage,
                metadata=metadata,
                infer_name=infer_name,
                toolsets=toolsets,
                builtin_tools=builtin_tools,
            )
    
        def run_stream(
            self,
            *,
            output_type: OutputSpec[Any] | None = None,
            message_history: Sequence[ModelMessage] | None = None,
            deferred_tool_results: DeferredToolResults | None = None,
            model: Model | KnownModelName | str | None = None,
            instructions: Instructions[AgentDepsT] = None,
            deps: AgentDepsT = None,
            model_settings: ModelSettings | None = None,
            usage_limits: UsageLimits | None = None,
            usage: RunUsage | None = None,
            metadata: AgentMetadata[AgentDepsT] | None = None,
            infer_name: bool = True,
            toolsets: Sequence[AbstractToolset[AgentDepsT]] | None = None,
            builtin_tools: Sequence[AbstractBuiltinTool] | None = None,
            on_complete: OnCompleteFunc[EventT] | None = None,
        ) -> AsyncIterator[EventT]:
            """Run the agent with the protocol-specific run input and stream protocol-specific events.
    
            Args:
                output_type: Custom output type to use for this run, `output_type` may only be used if the agent has no
                    output validators since output validators would expect an argument that matches the agent's output type.
                message_history: History of the conversation so far.
                deferred_tool_results: Optional results for deferred tool calls in the message history.
                model: Optional model to use for this run, required if `model` was not set when creating the agent.
                instructions: Optional additional instructions to use for this run.
                deps: Optional dependencies to use for this run.
                model_settings: Optional settings to use for this model's request.
                usage_limits: Optional limits on model request count or token usage.
                usage: Optional usage to start with, useful for resuming a conversation or agents used in tools.
                metadata: Optional metadata to attach to this run. Accepts a dictionary or a callable taking
                    [`RunContext`][pydantic_ai.tools.RunContext]; merged with the agent's configured metadata.
                infer_name: Whether to try to infer the agent name from the call frame if it's not set.
                toolsets: Optional additional toolsets for this run.
                builtin_tools: Optional additional builtin tools to use for this run.
                on_complete: Optional callback function called when the agent run completes successfully.
                    The callback receives the completed [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] and can optionally yield additional protocol-specific events.
            """
            return self.transform_stream(
                self.run_stream_native(
                    output_type=output_type,
                    message_history=message_history,
                    deferred_tool_results=deferred_tool_results,
                    model=model,
                    instructions=instructions,
                    deps=deps,
                    model_settings=model_settings,
                    usage_limits=usage_limits,
                    usage=usage,
                    metadata=metadata,
                    infer_name=infer_name,
                    toolsets=toolsets,
                    builtin_tools=builtin_tools,
                ),
                on_complete=on_complete,
            )
    
        @classmethod
        async def dispatch_request(
            cls,
            request: Request,
            *,
            agent: AbstractAgent[DispatchDepsT, DispatchOutputDataT],
            message_history: Sequence[ModelMessage] | None = None,
            deferred_tool_results: DeferredToolResults | None = None,
            model: Model | KnownModelName | str | None = None,
            instructions: Instructions[DispatchDepsT] = None,
            deps: DispatchDepsT = None,
            output_type: OutputSpec[Any] | None = None,
            model_settings: ModelSettings | None = None,
            usage_limits: UsageLimits | None = None,
            usage: RunUsage | None = None,
            metadata: AgentMetadata[DispatchDepsT] | None = None,
            infer_name: bool = True,
            toolsets: Sequence[AbstractToolset[DispatchDepsT]] | None = None,
            builtin_tools: Sequence[AbstractBuiltinTool] | None = None,
            on_complete: OnCompleteFunc[EventT] | None = None,
        ) -> Response:
            """Handle a protocol-specific HTTP request by running the agent and returning a streaming response of protocol-specific events.
    
            Args:
                request: The incoming Starlette/FastAPI request.
                agent: The agent to run.
                output_type: Custom output type to use for this run, `output_type` may only be used if the agent has no
                    output validators since output validators would expect an argument that matches the agent's output type.
                message_history: History of the conversation so far.
                deferred_tool_results: Optional results for deferred tool calls in the message history.
                model: Optional model to use for this run, required if `model` was not set when creating the agent.
                instructions: Optional additional instructions to use for this run.
                deps: Optional dependencies to use for this run.
                model_settings: Optional settings to use for this model's request.
                usage_limits: Optional limits on model request count or token usage.
                usage: Optional usage to start with, useful for resuming a conversation or agents used in tools.
                metadata: Optional metadata to attach to this run. Accepts a dictionary or a callable taking
                    [`RunContext`][pydantic_ai.tools.RunContext]; merged with the agent's configured metadata.
                infer_name: Whether to try to infer the agent name from the call frame if it's not set.
                toolsets: Optional additional toolsets for this run.
                builtin_tools: Optional additional builtin tools to use for this run.
                on_complete: Optional callback function called when the agent run completes successfully.
                    The callback receives the completed [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] and can optionally yield additional protocol-specific events.
    
            Returns:
                A streaming Starlette response with protocol-specific events encoded per the request's `Accept` header value.
            """
            try:
                from starlette.responses import Response
            except ImportError as e:  # pragma: no cover
                raise ImportError(
                    'Please install the `starlette` package to use `dispatch_request()` method, '
                    'you can use the `ui` optional group — `pip install "pydantic-ai-slim[ui]"`'
                ) from e
    
            try:
                # The DepsT and OutputDataT come from `agent`, not from `cls`; the cast is necessary to explain this to pyright
                adapter = cast(
                    UIAdapter[RunInputT, MessageT, EventT, DispatchDepsT, DispatchOutputDataT],
                    await cls.from_request(request, agent=cast(AbstractAgent[AgentDepsT, OutputDataT], agent)),
                )
            except ValidationError as e:  # pragma: no cover
                return Response(
                    content=e.json(),
                    media_type='application/json',
                    status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
    
            return adapter.streaming_response(
                adapter.run_stream(
                    message_history=message_history,
                    deferred_tool_results=deferred_tool_results,
                    deps=deps,
                    output_type=output_type,
                    model=model,
                    instructions=instructions,
                    model_settings=model_settings,
                    usage_limits=usage_limits,
                    usage=usage,
                    metadata=metadata,
                    infer_name=infer_name,
                    toolsets=toolsets,
                    builtin_tools=builtin_tools,
                    on_complete=on_complete,
                ),
            )
    
