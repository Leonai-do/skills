---
url: https://ai.pydantic.dev/api/models/bedrock/
date: 2026-01-03T23:41:01.911461
---


    @dataclass(init=False)
    class BedrockConverseModel(Model):
        """A model that uses the Bedrock Converse API."""
    
        client: BedrockRuntimeClient
    
        _model_name: BedrockModelName = field(repr=False)
        _provider: Provider[BaseClient] = field(repr=False)
    
        def __init__(
            self,
            model_name: BedrockModelName,
            *,
            provider: Literal['bedrock', 'gateway'] | Provider[BaseClient] = 'bedrock',
            profile: ModelProfileSpec | None = None,
            settings: ModelSettings | None = None,
        ):
            """Initialize a Bedrock model.
    
            Args:
                model_name: The name of the model to use.
                model_name: The name of the Bedrock model to use. List of model names available
                    [here](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html).
                provider: The provider to use for authentication and API access. Can be either the string
                    'bedrock' or an instance of `Provider[BaseClient]`. If not provided, a new provider will be
                    created using the other parameters.
                profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
                settings: Model-specific settings that will be used as defaults for this model.
            """
            self._model_name = model_name
    
            if isinstance(provider, str):
                provider = infer_provider('gateway/bedrock' if provider == 'gateway' else provider)
            self._provider = provider
            self.client = cast('BedrockRuntimeClient', provider.client)
    
            super().__init__(settings=settings, profile=profile or provider.model_profile)
    
        @property
        def base_url(self) -> str:
            return str(self.client.meta.endpoint_url)
    
        @property
        def model_name(self) -> str:
            """The model name."""
            return self._model_name
    
        @property
        def system(self) -> str:
            """The model provider."""
            return self._provider.name
    
        def _get_tools(self, model_request_parameters: ModelRequestParameters) -> list[ToolTypeDef]:
            return [self._map_tool_definition(r) for r in model_request_parameters.tool_defs.values()]
    
        @staticmethod
        def _map_tool_definition(f: ToolDefinition) -> ToolTypeDef:
            tool_spec: ToolSpecificationTypeDef = {'name': f.name, 'inputSchema': {'json': f.parameters_json_schema}}
    
            if f.description:  # pragma: no branch
                tool_spec['description'] = f.description
    
            return {'toolSpec': tool_spec}
    
        async def request(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> ModelResponse:
            model_settings, model_request_parameters = self.prepare_request(
                model_settings,
                model_request_parameters,
            )
            settings = cast(BedrockModelSettings, model_settings or {})
            response = await self._messages_create(messages, False, settings, model_request_parameters)
            model_response = await self._process_response(response)
            return model_response
    
        async def count_tokens(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> usage.RequestUsage:
            """Count the number of tokens, works with limited models.
    
            Check the actual supported models on <https://docs.aws.amazon.com/bedrock/latest/userguide/count-tokens.html>
            """
            model_settings, model_request_parameters = self.prepare_request(model_settings, model_request_parameters)
            settings = cast(BedrockModelSettings, model_settings or {})
            system_prompt, bedrock_messages = await self._map_messages(messages, model_request_parameters, settings)
            params: CountTokensRequestTypeDef = {
                'modelId': self._remove_inference_geo_prefix(self.model_name),
                'input': {
                    'converse': {
                        'messages': bedrock_messages,
                        'system': system_prompt,
                    },
                },
            }
            try:
                response = await anyio.to_thread.run_sync(functools.partial(self.client.count_tokens, **params))
            except ClientError as e:
                status_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
                if isinstance(status_code, int):
                    raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.response) from e
                raise ModelAPIError(model_name=self.model_name, message=str(e)) from e
            return usage.RequestUsage(input_tokens=response['inputTokens'])
    
        @asynccontextmanager
        async def request_stream(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
            run_context: RunContext[Any] | None = None,
        ) -> AsyncIterator[StreamedResponse]:
            model_settings, model_request_parameters = self.prepare_request(
                model_settings,
                model_request_parameters,
            )
            settings = cast(BedrockModelSettings, model_settings or {})
            response = await self._messages_create(messages, True, settings, model_request_parameters)
            yield BedrockStreamedResponse(
                model_request_parameters=model_request_parameters,
                _model_name=self.model_name,
                _event_stream=response['stream'],
                _provider_name=self._provider.name,
                _provider_url=self.base_url,
                _provider_response_id=response.get('ResponseMetadata', {}).get('RequestId', None),
            )
    
        async def _process_response(self, response: ConverseResponseTypeDef) -> ModelResponse:
            items: list[ModelResponsePart] = []
            if message := response['output'].get('message'):  # pragma: no branch
                for item in message['content']:
                    if reasoning_content := item.get('reasoningContent'):
                        if redacted_content := reasoning_content.get('redactedContent'):
                            items.append(
                                ThinkingPart(
                                    id='redacted_content',
                                    content='',
                                    signature=redacted_content.decode('utf-8'),
                                    provider_name=self.system,
                                )
                            )
                        elif reasoning_text := reasoning_content.get('reasoningText'):  # pragma: no branch
                            signature = reasoning_text.get('signature')
                            items.append(
                                ThinkingPart(
                                    content=reasoning_text['text'],
                                    signature=signature,
                                    provider_name=self.system if signature else None,
                                )
                            )
                    if text := item.get('text'):
                        items.append(TextPart(content=text))
                    elif tool_use := item.get('toolUse'):
                        items.append(
                            ToolCallPart(
                                tool_name=tool_use['name'],
                                args=tool_use['input'],
                                tool_call_id=tool_use['toolUseId'],
                            ),
                        )
            u = usage.RequestUsage(
                input_tokens=response['usage']['inputTokens'],
                output_tokens=response['usage']['outputTokens'],
                cache_read_tokens=response['usage'].get('cacheReadInputTokens', 0),
                cache_write_tokens=response['usage'].get('cacheWriteInputTokens', 0),
            )
            response_id = response.get('ResponseMetadata', {}).get('RequestId', None)
            raw_finish_reason = response['stopReason']
            provider_details = {'finish_reason': raw_finish_reason}
            finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)
    
            return ModelResponse(
                parts=items,
                usage=u,
                model_name=self.model_name,
                provider_response_id=response_id,
                provider_name=self._provider.name,
                provider_url=self.base_url,
                finish_reason=finish_reason,
                provider_details=provider_details,
            )
    
        @overload
        async def _messages_create(
            self,
            messages: list[ModelMessage],
            stream: Literal[True],
            model_settings: BedrockModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> ConverseStreamResponseTypeDef:
            pass
    
        @overload
        async def _messages_create(
            self,
            messages: list[ModelMessage],
            stream: Literal[False],
            model_settings: BedrockModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> ConverseResponseTypeDef:
            pass
    
        async def _messages_create(
            self,
            messages: list[ModelMessage],
            stream: bool,
            model_settings: BedrockModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> ConverseResponseTypeDef | ConverseStreamResponseTypeDef:
            settings = model_settings or BedrockModelSettings()
            system_prompt, bedrock_messages = await self._map_messages(messages, model_request_parameters, settings)
            inference_config = self._map_inference_config(settings)
    
            params: ConverseRequestTypeDef = {
                'modelId': self.model_name,
                'messages': bedrock_messages,
                'system': system_prompt,
                'inferenceConfig': inference_config,
            }
    
            tool_config = self._map_tool_config(model_request_parameters, settings)
            if tool_config:
                params['toolConfig'] = tool_config
    
            tools: list[ToolTypeDef] = list(tool_config['tools']) if tool_config else []
            self._limit_cache_points(system_prompt, bedrock_messages, tools)
    
            # Bedrock supports a set of specific extra parameters
            if model_settings:
                if guardrail_config := model_settings.get('bedrock_guardrail_config', None):
                    params['guardrailConfig'] = guardrail_config
                if performance_configuration := model_settings.get('bedrock_performance_configuration', None):
                    params['performanceConfig'] = performance_configuration
                if request_metadata := model_settings.get('bedrock_request_metadata', None):
                    params['requestMetadata'] = request_metadata
                if additional_model_response_fields_paths := model_settings.get(
                    'bedrock_additional_model_response_fields_paths', None
                ):
                    params['additionalModelResponseFieldPaths'] = additional_model_response_fields_paths
                if additional_model_requests_fields := model_settings.get('bedrock_additional_model_requests_fields', None):
                    params['additionalModelRequestFields'] = additional_model_requests_fields
                if prompt_variables := model_settings.get('bedrock_prompt_variables', None):
                    params['promptVariables'] = prompt_variables
                if service_tier := model_settings.get('bedrock_service_tier', None):
                    params['serviceTier'] = service_tier
    
            try:
                if stream:
                    model_response = await anyio.to_thread.run_sync(
                        functools.partial(self.client.converse_stream, **params)
                    )
                else:
                    model_response = await anyio.to_thread.run_sync(functools.partial(self.client.converse, **params))
            except ClientError as e:
                status_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode')
                if isinstance(status_code, int):
                    raise ModelHTTPError(status_code=status_code, model_name=self.model_name, body=e.response) from e
                raise ModelAPIError(model_name=self.model_name, message=str(e)) from e
            return model_response
    
        @staticmethod
        def _map_inference_config(
            model_settings: ModelSettings | None,
        ) -> InferenceConfigurationTypeDef:
            model_settings = model_settings or {}
            inference_config: InferenceConfigurationTypeDef = {}
    
            if max_tokens := model_settings.get('max_tokens'):
                inference_config['maxTokens'] = max_tokens
            if (temperature := model_settings.get('temperature')) is not None:
                inference_config['temperature'] = temperature
            if top_p := model_settings.get('top_p'):
                inference_config['topP'] = top_p
            if stop_sequences := model_settings.get('stop_sequences'):
                inference_config['stopSequences'] = stop_sequences
    
            return inference_config
    
        def _map_tool_config(
            self,
            model_request_parameters: ModelRequestParameters,
            model_settings: BedrockModelSettings | None,
        ) -> ToolConfigurationTypeDef | None:
            tools = self._get_tools(model_request_parameters)
            if not tools:
                return None
    
            profile = BedrockModelProfile.from_profile(self.profile)
            if (
                model_settings
                and model_settings.get('bedrock_cache_tool_definitions')
                and profile.bedrock_supports_tool_caching
            ):
                tools.append({'cachePoint': {'type': 'default'}})
    
            tool_choice: ToolChoiceTypeDef
            if not model_request_parameters.allow_text_output:
                tool_choice = {'any': {}}
            else:
                tool_choice = {'auto': {}}
    
            tool_config: ToolConfigurationTypeDef = {'tools': tools}
            if tool_choice and BedrockModelProfile.from_profile(self.profile).bedrock_supports_tool_choice:
                tool_config['toolChoice'] = tool_choice
    
            return tool_config
    
        async def _map_messages(  # noqa: C901
            self,
            messages: Sequence[ModelMessage],
            model_request_parameters: ModelRequestParameters,
            model_settings: BedrockModelSettings | None,
        ) -> tuple[list[SystemContentBlockTypeDef], list[MessageUnionTypeDef]]:
            """Maps a `pydantic_ai.Message` to the Bedrock `MessageUnionTypeDef`.
    
            Groups consecutive ToolReturnPart objects into a single user message as required by Bedrock Claude/Nova models.
            """
            settings = model_settings or BedrockModelSettings()
            profile = BedrockModelProfile.from_profile(self.profile)
            system_prompt: list[SystemContentBlockTypeDef] = []
            bedrock_messages: list[MessageUnionTypeDef] = []
            document_count: Iterator[int] = count(1)
            for message in messages:
                if isinstance(message, ModelRequest):
                    for part in message.parts:
                        if isinstance(part, SystemPromptPart) and part.content:
                            system_prompt.append({'text': part.content})
                        elif isinstance(part, UserPromptPart):
                            bedrock_messages.extend(
                                await self._map_user_prompt(part, document_count, profile.bedrock_supports_prompt_caching)
                            )
                        elif isinstance(part, ToolReturnPart):
                            assert part.tool_call_id is not None
                            bedrock_messages.append(
                                {
                                    'role': 'user',
                                    'content': [
                                        {
                                            'toolResult': {
                                                'toolUseId': part.tool_call_id,
                                                'content': [
                                                    {'text': part.model_response_str()}
                                                    if profile.bedrock_tool_result_format == 'text'
                                                    else {'json': part.model_response_object()}
                                                ],
                                                'status': 'success',
                                            }
                                        }
                                    ],
                                }
                            )
                        elif isinstance(part, RetryPromptPart):
                            # TODO(Marcelo): We need to add a test here.
                            if part.tool_name is None:  # pragma: no cover
                                bedrock_messages.append({'role': 'user', 'content': [{'text': part.model_response()}]})
                            else:
                                assert part.tool_call_id is not None
                                bedrock_messages.append(
                                    {
                                        'role': 'user',
                                        'content': [
                                            {
                                                'toolResult': {
                                                    'toolUseId': part.tool_call_id,
                                                    'content': [{'text': part.model_response()}],
                                                    'status': 'error',
                                                }
                                            }
                                        ],
                                    }
                                )
                elif isinstance(message, ModelResponse):
                    content: list[ContentBlockOutputTypeDef] = []
                    for item in message.parts:
                        if isinstance(item, TextPart):
                            content.append({'text': item.content})
                        elif isinstance(item, ThinkingPart):
                            if (
                                item.provider_name == self.system
                                and item.signature
                                and BedrockModelProfile.from_profile(self.profile).bedrock_send_back_thinking_parts
                            ):
                                if item.id == 'redacted_content':
                                    reasoning_content: ReasoningContentBlockOutputTypeDef = {
                                        'redactedContent': item.signature.encode('utf-8'),
                                    }
                                else:
                                    reasoning_content: ReasoningContentBlockOutputTypeDef = {
                                        'reasoningText': {
                                            'text': item.content,
                                            'signature': item.signature,
                                        }
                                    }
                                content.append({'reasoningContent': reasoning_content})
                            else:
                                start_tag, end_tag = self.profile.thinking_tags
                                content.append({'text': '\n'.join([start_tag, item.content, end_tag])})
                        elif isinstance(item, BuiltinToolCallPart | BuiltinToolReturnPart):
                            pass
                        else:
                            assert isinstance(item, ToolCallPart)
                            content.append(self._map_tool_call(item))
                    if content:
                        bedrock_messages.append({'role': 'assistant', 'content': content})
                else:
                    assert_never(message)
    
            # Merge together sequential user messages.
            processed_messages: list[MessageUnionTypeDef] = []
            last_message: dict[str, Any] | None = None
            for current_message in bedrock_messages:
                if (
                    last_message is not None
                    and current_message['role'] == last_message['role']
                    and current_message['role'] == 'user'
                ):
                    # Add the new user content onto the existing user message.
                    last_content = list(last_message['content'])
                    last_content.extend(current_message['content'])
                    last_message['content'] = last_content
                    continue
    
                # Add the entire message to the list of messages.
                processed_messages.append(current_message)
                last_message = cast(dict[str, Any], current_message)
    
            if instructions := self._get_instructions(messages, model_request_parameters):
                system_prompt.append({'text': instructions})
    
            if system_prompt and settings.get('bedrock_cache_instructions') and profile.bedrock_supports_prompt_caching:
                system_prompt.append({'cachePoint': {'type': 'default'}})
    
            if processed_messages and settings.get('bedrock_cache_messages') and profile.bedrock_supports_prompt_caching:
                last_user_content = self._get_last_user_message_content(processed_messages)
                if last_user_content is not None:
                    # AWS currently rejects cache points that directly follow non-text content.
                    # Insert a newline text block as a workaround.
                    if 'text' not in last_user_content[-1]:
                        last_user_content.append({'text': '\n'})
                    last_user_content.append({'cachePoint': {'type': 'default'}})
    
            return system_prompt, processed_messages
    
        @staticmethod
        def _get_last_user_message_content(messages: list[MessageUnionTypeDef]) -> list[Any] | None:
            """Get the content list from the last user message that can receive a cache point.
    
            Returns the content list if:
            - A user message exists
            - It has a non-empty content list
            - The last content block doesn't already have a cache point
    
            Returns None otherwise.
            """
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return None
    
            content = user_messages[-1].get('content')  # Last user message
            if not content or not isinstance(content, list) or len(content) == 0:
                return None
    
            last_block = content[-1]
            if not isinstance(last_block, dict):
                return None
            if 'cachePoint' in last_block:  # Skip if already has a cache point
                return None
            return content
    
        @staticmethod
        async def _map_user_prompt(  # noqa: C901
            part: UserPromptPart,
            document_count: Iterator[int],
            supports_prompt_caching: bool,
        ) -> list[MessageUnionTypeDef]:
            content: list[ContentBlockUnionTypeDef] = []
            if isinstance(part.content, str):
                content.append({'text': part.content})
            else:
                for item in part.content:
                    if isinstance(item, str):
                        content.append({'text': item})
                    elif isinstance(item, BinaryContent):
                        format = item.format
                        if item.is_document:
                            name = f'Document {next(document_count)}'
                            assert format in ('pdf', 'txt', 'csv', 'doc', 'docx', 'xls', 'xlsx', 'html', 'md')
                            content.append({'document': {'name': name, 'format': format, 'source': {'bytes': item.data}}})
                        elif item.is_image:
                            assert format in ('jpeg', 'png', 'gif', 'webp')
                            content.append({'image': {'format': format, 'source': {'bytes': item.data}}})
                        elif item.is_video:
                            assert format in ('mkv', 'mov', 'mp4', 'webm', 'flv', 'mpeg', 'mpg', 'wmv', 'three_gp')
                            content.append({'video': {'format': format, 'source': {'bytes': item.data}}})
                        else:
                            raise NotImplementedError('Binary content is not supported yet.')
                    elif isinstance(item, ImageUrl | DocumentUrl | VideoUrl):
                        source: DocumentSourceTypeDef
                        if item.url.startswith('s3://'):
                            parsed = urlparse(item.url)
                            s3_location: S3LocationTypeDef = {'uri': f'{parsed.scheme}://{parsed.netloc}{parsed.path}'}
                            if bucket_owner := parse_qs(parsed.query).get('bucketOwner', [None])[0]:
                                s3_location['bucketOwner'] = bucket_owner
                            source = {'s3Location': s3_location}
                        else:
                            downloaded_item = await download_item(item, data_format='bytes', type_format='extension')
                            source = {'bytes': downloaded_item['data']}
    
                        if item.kind == 'image-url':
                            format = item.media_type.split('/')[1]
                            assert format in ('jpeg', 'png', 'gif', 'webp'), f'Unsupported image format: {format}'
                            image: ImageBlockTypeDef = {'format': format, 'source': source}
                            content.append({'image': image})
    
                        elif item.kind == 'document-url':
                            name = f'Document {next(document_count)}'
                            document: DocumentBlockTypeDef = {
                                'name': name,
                                'format': item.format,
                                'source': source,
                            }
                            content.append({'document': document})
    
                        elif item.kind == 'video-url':  # pragma: no branch
                            format = item.media_type.split('/')[1]
                            assert format in (
                                'mkv',
                                'mov',
                                'mp4',
                                'webm',
                                'flv',
                                'mpeg',
                                'mpg',
                                'wmv',
                                'three_gp',
                            ), f'Unsupported video format: {format}'
                            video: VideoBlockTypeDef = {'format': format, 'source': source}
                            content.append({'video': video})
                    elif isinstance(item, AudioUrl):  # pragma: no cover
                        raise NotImplementedError('Audio is not supported yet.')
                    elif isinstance(item, CachePoint):
                        if not supports_prompt_caching:
                            # Silently skip CachePoint for models that don't support prompt caching
                            continue
                        if not content or 'cachePoint' in content[-1]:
                            raise UserError(
                                'CachePoint cannot be the first content in a user message - there must be previous content to cache when using Bedrock. '
                                'To cache system instructions or tool definitions, use the `bedrock_cache_instructions` or `bedrock_cache_tool_definitions` settings instead.'
                            )
                        if 'text' not in content[-1]:
                            # AWS currently rejects cache points that directly follow non-text content.
                            # Insert an empty text block as a workaround (see https://github.com/pydantic/pydantic-ai/issues/3418
                            # and https://github.com/pydantic/pydantic-ai/pull/2560#discussion_r2349209916).
                            content.append({'text': '\n'})
                        content.append({'cachePoint': {'type': 'default'}})
                    else:
                        assert_never(item)
            return [{'role': 'user', 'content': content}]
    
        @staticmethod
        def _map_tool_call(t: ToolCallPart) -> ContentBlockOutputTypeDef:
            return {
                'toolUse': {'toolUseId': _utils.guard_tool_call_id(t=t), 'name': t.tool_name, 'input': t.args_as_dict()}
            }
    
        @staticmethod
        def _limit_cache_points(
            system_prompt: list[SystemContentBlockTypeDef],
            bedrock_messages: list[MessageUnionTypeDef],
            tools: list[ToolTypeDef],
        ) -> None:
            """Limit the number of cache points in the request to Bedrock's maximum.
    
            Bedrock enforces a maximum of 4 cache points per request. This method ensures
            compliance by counting existing cache points and removing excess ones from messages.
    
            Strategy:
            1. Count cache points in system_prompt
            2. Count cache points in tools
            3. Raise UserError if system + tools already exceed MAX_CACHE_POINTS
            4. Calculate remaining budget for message cache points
            5. Traverse messages from newest to oldest, keeping the most recent cache points
               within the remaining budget
            6. Remove excess cache points from older messages to stay within limit
    
            Cache point priority (always preserved):
            - System prompt cache points
            - Tool definition cache points
            - Message cache points (newest first, oldest removed if needed)
    
            Raises:
                UserError: If system_prompt and tools combined already exceed MAX_CACHE_POINTS (4).
                          This indicates a configuration error that cannot be auto-fixed.
            """
            MAX_CACHE_POINTS = 4
    
            # Count existing cache points in system prompt
            used_cache_points = sum(1 for block in system_prompt if 'cachePoint' in block)
    
            # Count existing cache points in tools
            for tool in tools:
                if 'cachePoint' in tool:
                    used_cache_points += 1
    
            # Calculate remaining cache points budget for messages
            remaining_budget = MAX_CACHE_POINTS - used_cache_points
            if remaining_budget < 0:  # pragma: no cover
                raise UserError(
                    f'Too many cache points for Bedrock request. '
                    f'System prompt and tool definitions already use {used_cache_points} cache points, '
                    f'which exceeds the maximum of {MAX_CACHE_POINTS}.'
                )
    
            # Remove excess cache points from messages (newest to oldest)
            for message in reversed(bedrock_messages):
                content = message.get('content')
                if not content or not isinstance(content, list):  # pragma: no cover
                    continue
    
                # Build a new content list, keeping only cache points within budget
                new_content: list[Any] = []
                for block in reversed(content):  # Process newest first
                    is_cache_point = isinstance(block, dict) and 'cachePoint' in block
                    if is_cache_point:
                        if remaining_budget > 0:
                            remaining_budget -= 1
                            new_content.append(block)
                    else:
                        new_content.append(block)
                message['content'] = list(reversed(new_content))  # Restore original order
    
        @staticmethod
        def _remove_inference_geo_prefix(model_name: BedrockModelName) -> BedrockModelName:
            """Remove inference geographic prefix from model ID if present."""
            for prefix in BEDROCK_GEO_PREFIXES:
                if model_name.startswith(f'{prefix}.'):
                    return model_name.removeprefix(f'{prefix}.')
            return model_name
    
