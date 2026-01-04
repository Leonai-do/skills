---
url: https://ai.pydantic.dev/api/models/google/
date: 2026-01-03T23:41:08.438076
---


    @dataclass(init=False)
    class GoogleModel(Model):
        """A model that uses Gemini via `generativelanguage.googleapis.com` API.
    
        This is implemented from scratch rather than using a dedicated SDK, good API documentation is
        available [here](https://ai.google.dev/api).
    
        Apart from `__init__`, all methods are private or match those of the base class.
        """
    
        client: Client = field(repr=False)
    
        _model_name: GoogleModelName = field(repr=False)
        _provider: Provider[Client] = field(repr=False)
    
        def __init__(
            self,
            model_name: GoogleModelName,
            *,
            provider: Literal['google-gla', 'google-vertex', 'gateway'] | Provider[Client] = 'google-gla',
            profile: ModelProfileSpec | None = None,
            settings: ModelSettings | None = None,
        ):
            """Initialize a Gemini model.
    
            Args:
                model_name: The name of the model to use.
                provider: The provider to use for authentication and API access. Can be either the string
                    'google-gla' or 'google-vertex' or an instance of `Provider[google.genai.AsyncClient]`.
                    Defaults to 'google-gla'.
                profile: The model profile to use. Defaults to a profile picked by the provider based on the model name.
                settings: The model settings to use. Defaults to None.
            """
            self._model_name = model_name
    
            if isinstance(provider, str):
                provider = infer_provider('gateway/google-vertex' if provider == 'gateway' else provider)
            self._provider = provider
            self.client = provider.client
    
            super().__init__(settings=settings, profile=profile or provider.model_profile)
    
        @property
        def base_url(self) -> str:
            return self._provider.base_url
    
        @property
        def model_name(self) -> GoogleModelName:
            """The model name."""
            return self._model_name
    
        @property
        def system(self) -> str:
            """The model provider."""
            return self._provider.name
    
        @classmethod
        def supported_builtin_tools(cls) -> frozenset[type[AbstractBuiltinTool]]:
            """Return the set of builtin tool types this model can handle."""
            return frozenset({WebSearchTool, CodeExecutionTool, FileSearchTool, WebFetchTool, ImageGenerationTool})
    
        def prepare_request(
            self, model_settings: ModelSettings | None, model_request_parameters: ModelRequestParameters
        ) -> tuple[ModelSettings | None, ModelRequestParameters]:
            supports_native_output_with_builtin_tools = GoogleModelProfile.from_profile(
                self.profile
            ).google_supports_native_output_with_builtin_tools
            if model_request_parameters.builtin_tools and model_request_parameters.output_tools:
                if model_request_parameters.output_mode == 'auto':
                    output_mode = 'native' if supports_native_output_with_builtin_tools else 'prompted'
                    model_request_parameters = replace(model_request_parameters, output_mode=output_mode)
                else:
                    output_mode = 'NativeOutput' if supports_native_output_with_builtin_tools else 'PromptedOutput'
                    raise UserError(
                        f'Google does not support output tools and built-in tools at the same time. Use `output_type={output_mode}(...)` instead.'
                    )
            return super().prepare_request(model_settings, model_request_parameters)
    
        async def request(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> ModelResponse:
            check_allow_model_requests()
            model_settings, model_request_parameters = self.prepare_request(
                model_settings,
                model_request_parameters,
            )
            model_settings = cast(GoogleModelSettings, model_settings or {})
            response = await self._generate_content(messages, False, model_settings, model_request_parameters)
            return self._process_response(response)
    
        async def count_tokens(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
        ) -> usage.RequestUsage:
            check_allow_model_requests()
            model_settings, model_request_parameters = self.prepare_request(
                model_settings,
                model_request_parameters,
            )
            model_settings = cast(GoogleModelSettings, model_settings or {})
            contents, generation_config = await self._build_content_and_config(
                messages, model_settings, model_request_parameters
            )
    
            # Annoyingly, the type of `GenerateContentConfigDict.get` is "partially `Unknown`" because `response_schema` includes `typing._UnionGenericAlias`,
            # so without this we'd need `pyright: ignore[reportUnknownMemberType]` on every line and wouldn't get type checking anyway.
            generation_config = cast(dict[str, Any], generation_config)
    
            config = CountTokensConfigDict(
                http_options=generation_config.get('http_options'),
            )
            if self._provider.name != 'google-gla':
                # The fields are not supported by the Gemini API per https://github.com/googleapis/python-genai/blob/7e4ec284dc6e521949626f3ed54028163ef9121d/google/genai/models.py#L1195-L1214
                config.update(  # pragma: lax no cover
                    system_instruction=generation_config.get('system_instruction'),
                    tools=cast(list[ToolDict], generation_config.get('tools')),
                    # Annoyingly, GenerationConfigDict has fewer fields than GenerateContentConfigDict, and no extra fields are allowed.
                    generation_config=GenerationConfigDict(
                        temperature=generation_config.get('temperature'),
                        top_p=generation_config.get('top_p'),
                        max_output_tokens=generation_config.get('max_output_tokens'),
                        stop_sequences=generation_config.get('stop_sequences'),
                        presence_penalty=generation_config.get('presence_penalty'),
                        frequency_penalty=generation_config.get('frequency_penalty'),
                        seed=generation_config.get('seed'),
                        thinking_config=generation_config.get('thinking_config'),
                        media_resolution=generation_config.get('media_resolution'),
                        response_mime_type=generation_config.get('response_mime_type'),
                        response_json_schema=generation_config.get('response_json_schema'),
                    ),
                )
    
            response = await self.client.aio.models.count_tokens(
                model=self._model_name,
                contents=contents,
                config=config,
            )
            if response.total_tokens is None:
                raise UnexpectedModelBehavior(  # pragma: no cover
                    'Total tokens missing from Gemini response', str(response)
                )
            return usage.RequestUsage(
                input_tokens=response.total_tokens,
            )
    
        @asynccontextmanager
        async def request_stream(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings | None,
            model_request_parameters: ModelRequestParameters,
            run_context: RunContext[Any] | None = None,
        ) -> AsyncIterator[StreamedResponse]:
            check_allow_model_requests()
            model_settings, model_request_parameters = self.prepare_request(
                model_settings,
                model_request_parameters,
            )
            model_settings = cast(GoogleModelSettings, model_settings or {})
            response = await self._generate_content(messages, True, model_settings, model_request_parameters)
            yield await self._process_streamed_response(response, model_request_parameters)  # type: ignore
    
        def _build_image_config(self, tool: ImageGenerationTool) -> ImageConfigDict:
            """Build ImageConfigDict from ImageGenerationTool with validation."""
            image_config = ImageConfigDict()
    
            if tool.aspect_ratio is not None:
                image_config['aspect_ratio'] = tool.aspect_ratio
    
            if tool.size is not None:
                if tool.size not in _GOOGLE_IMAGE_SIZES:
                    raise UserError(
                        f'Google image generation only supports `size` values: {_GOOGLE_IMAGE_SIZES}. '
                        f'Got: {tool.size!r}. Omit `size` to use the default (1K).'
                    )
                image_config['image_size'] = tool.size
    
            if self.system == 'google-vertex':
                if tool.output_format is not None:
                    if tool.output_format not in _GOOGLE_IMAGE_OUTPUT_FORMATS:
                        raise UserError(
                            f'Google image generation only supports `output_format` values: {_GOOGLE_IMAGE_OUTPUT_FORMATS}. '
                            f'Got: {tool.output_format!r}.'
                        )
                    image_config['output_mime_type'] = f'image/{tool.output_format}'
    
                output_compression = tool.output_compression
                if output_compression is not None:
                    if not (0 <= output_compression <= 100):
                        raise UserError(
                            f'Google image generation `output_compression` must be between 0 and 100. '
                            f'Got: {output_compression}.'
                        )
                    if tool.output_format not in (None, 'jpeg'):
                        raise UserError(
                            f'Google image generation `output_compression` is only supported for JPEG format. '
                            f'Got format: {tool.output_format!r}. Either set `output_format="jpeg"` or remove `output_compression`.'
                        )
                    image_config['output_compression_quality'] = output_compression
                    if tool.output_format is None:
                        image_config['output_mime_type'] = 'image/jpeg'
    
            return image_config
    
        def _get_tools(
            self, model_request_parameters: ModelRequestParameters
        ) -> tuple[list[ToolDict] | None, ImageConfigDict | None]:
            tools: list[ToolDict] = [
                ToolDict(function_declarations=[_function_declaration_from_tool(t)])
                for t in model_request_parameters.tool_defs.values()
            ]
    
            image_config: ImageConfigDict | None = None
    
            if model_request_parameters.builtin_tools:
                if model_request_parameters.function_tools:
                    raise UserError('Google does not support function tools and built-in tools at the same time.')
    
                for tool in model_request_parameters.builtin_tools:
                    if isinstance(tool, WebSearchTool):
                        tools.append(ToolDict(google_search=GoogleSearchDict()))
                    elif isinstance(tool, WebFetchTool):
                        tools.append(ToolDict(url_context=UrlContextDict()))
                    elif isinstance(tool, CodeExecutionTool):
                        tools.append(ToolDict(code_execution=ToolCodeExecutionDict()))
                    elif isinstance(tool, FileSearchTool):
                        file_search_config = FileSearchDict(file_search_store_names=list(tool.file_store_ids))
                        tools.append(ToolDict(file_search=file_search_config))
                    elif isinstance(tool, ImageGenerationTool):  # pragma: no branch
                        if not self.profile.supports_image_output:
                            raise UserError(
                                "`ImageGenerationTool` is not supported by this model. Use a model with 'image' in the name instead."
                            )
                        image_config = self._build_image_config(tool)
                    else:  # pragma: no cover
                        raise UserError(
                            f'`{tool.__class__.__name__}` is not supported by `GoogleModel`. If it should be, please file an issue.'
                        )
            return tools or None, image_config
    
        def _get_tool_config(
            self, model_request_parameters: ModelRequestParameters, tools: list[ToolDict] | None
        ) -> ToolConfigDict | None:
            if not model_request_parameters.allow_text_output and tools:
                names: list[str] = []
                for tool in tools:
                    for function_declaration in tool.get('function_declarations') or []:
                        if name := function_declaration.get('name'):  # pragma: no branch
                            names.append(name)
                return _tool_config(names)
            else:
                return None
    
        @overload
        async def _generate_content(
            self,
            messages: list[ModelMessage],
            stream: Literal[False],
            model_settings: GoogleModelSettings,
            model_request_parameters: ModelRequestParameters,
        ) -> GenerateContentResponse: ...
    
        @overload
        async def _generate_content(
            self,
            messages: list[ModelMessage],
            stream: Literal[True],
            model_settings: GoogleModelSettings,
            model_request_parameters: ModelRequestParameters,
        ) -> Awaitable[AsyncIterator[GenerateContentResponse]]: ...
    
        async def _generate_content(
            self,
            messages: list[ModelMessage],
            stream: bool,
            model_settings: GoogleModelSettings,
            model_request_parameters: ModelRequestParameters,
        ) -> GenerateContentResponse | Awaitable[AsyncIterator[GenerateContentResponse]]:
            contents, config = await self._build_content_and_config(messages, model_settings, model_request_parameters)
            func = self.client.aio.models.generate_content_stream if stream else self.client.aio.models.generate_content
            try:
                return await func(model=self._model_name, contents=contents, config=config)  # type: ignore
            except errors.APIError as e:
                if (status_code := e.code) >= 400:
                    raise ModelHTTPError(
                        status_code=status_code,
                        model_name=self._model_name,
                        body=cast(Any, e.details),  # pyright: ignore[reportUnknownMemberType]
                    ) from e
                raise ModelAPIError(model_name=self._model_name, message=str(e)) from e
    
        async def _build_content_and_config(
            self,
            messages: list[ModelMessage],
            model_settings: GoogleModelSettings,
            model_request_parameters: ModelRequestParameters,
        ) -> tuple[list[ContentUnionDict], GenerateContentConfigDict]:
            tools, image_config = self._get_tools(model_request_parameters)
            if model_request_parameters.function_tools and not self.profile.supports_tools:
                raise UserError('Tools are not supported by this model.')
    
            response_mime_type = None
            response_schema = None
            if model_request_parameters.output_mode == 'native':
                if model_request_parameters.function_tools:
                    raise UserError(
                        'Google does not support `NativeOutput` and function tools at the same time. Use `output_type=ToolOutput(...)` instead.'
                    )
                response_mime_type = 'application/json'
                output_object = model_request_parameters.output_object
                assert output_object is not None
                response_schema = self._map_response_schema(output_object)
            elif model_request_parameters.output_mode == 'prompted' and not tools:
                if not self.profile.supports_json_object_output:
                    raise UserError('JSON output is not supported by this model.')
                response_mime_type = 'application/json'
    
            tool_config = self._get_tool_config(model_request_parameters, tools)
            system_instruction, contents = await self._map_messages(messages, model_request_parameters)
    
            modalities = [Modality.TEXT.value]
            if self.profile.supports_image_output:
                modalities.append(Modality.IMAGE.value)
    
            http_options: HttpOptionsDict = {
                'headers': {'Content-Type': 'application/json', 'User-Agent': get_user_agent()}
            }
            if timeout := model_settings.get('timeout'):
                if isinstance(timeout, int | float):
                    http_options['timeout'] = int(1000 * timeout)
                else:
                    raise UserError('Google does not support setting ModelSettings.timeout to a httpx.Timeout')
    
            config = GenerateContentConfigDict(
                http_options=http_options,
                system_instruction=system_instruction,
                temperature=model_settings.get('temperature'),
                top_p=model_settings.get('top_p'),
                max_output_tokens=model_settings.get('max_tokens'),
                stop_sequences=model_settings.get('stop_sequences'),
                presence_penalty=model_settings.get('presence_penalty'),
                frequency_penalty=model_settings.get('frequency_penalty'),
                seed=model_settings.get('seed'),
                safety_settings=model_settings.get('google_safety_settings'),
                thinking_config=model_settings.get('google_thinking_config'),
                labels=model_settings.get('google_labels'),
                media_resolution=model_settings.get('google_video_resolution'),
                cached_content=model_settings.get('google_cached_content'),
                tools=cast(ToolListUnionDict, tools),
                tool_config=tool_config,
                response_mime_type=response_mime_type,
                response_json_schema=response_schema,
                response_modalities=modalities,
                image_config=image_config,
            )
    
            return contents, config
    
        def _process_response(self, response: GenerateContentResponse) -> ModelResponse:
            if not response.candidates:
                raise UnexpectedModelBehavior('Expected at least one candidate in Gemini response')  # pragma: no cover
    
            candidate = response.candidates[0]
    
            vendor_id = response.response_id
            finish_reason: FinishReason | None = None
            vendor_details: dict[str, Any] = {}
    
            raw_finish_reason = candidate.finish_reason
            if raw_finish_reason:  # pragma: no branch
                vendor_details['finish_reason'] = raw_finish_reason.value
                finish_reason = _FINISH_REASON_MAP.get(raw_finish_reason)
    
            if response.create_time is not None:  # pragma: no branch
                vendor_details['timestamp'] = response.create_time
    
            if candidate.content is None or candidate.content.parts is None:
                if finish_reason == 'content_filter' and raw_finish_reason:
                    raise UnexpectedModelBehavior(
                        f'Content filter {raw_finish_reason.value!r} triggered', response.model_dump_json()
                    )
                parts = []  # pragma: no cover
            else:
                parts = candidate.content.parts or []
    
            usage = _metadata_as_usage(response, provider=self._provider.name, provider_url=self._provider.base_url)
            return _process_response_from_parts(
                parts,
                candidate.grounding_metadata,
                response.model_version or self._model_name,
                self._provider.name,
                self._provider.base_url,
                usage,
                vendor_id=vendor_id,
                vendor_details=vendor_details or None,
                finish_reason=finish_reason,
                url_context_metadata=candidate.url_context_metadata,
            )
    
        async def _process_streamed_response(
            self, response: AsyncIterator[GenerateContentResponse], model_request_parameters: ModelRequestParameters
        ) -> StreamedResponse:
            """Process a streamed response, and prepare a streaming response to return."""
            peekable_response = _utils.PeekableAsyncStream(response)
            first_chunk = await peekable_response.peek()
            if isinstance(first_chunk, _utils.Unset):
                raise UnexpectedModelBehavior('Streamed response ended without content or tool calls')  # pragma: no cover
    
            return GeminiStreamedResponse(
                model_request_parameters=model_request_parameters,
                _model_name=first_chunk.model_version or self._model_name,
                _response=peekable_response,
                _provider_name=self._provider.name,
                _provider_url=self._provider.base_url,
                _provider_timestamp=first_chunk.create_time,
            )
    
        async def _map_messages(
            self, messages: list[ModelMessage], model_request_parameters: ModelRequestParameters
        ) -> tuple[ContentDict | None, list[ContentUnionDict]]:
            contents: list[ContentUnionDict] = []
            system_parts: list[PartDict] = []
    
            for m in messages:
                if isinstance(m, ModelRequest):
                    message_parts: list[PartDict] = []
    
                    for part in m.parts:
                        if isinstance(part, SystemPromptPart):
                            system_parts.append({'text': part.content})
                        elif isinstance(part, UserPromptPart):
                            message_parts.extend(await self._map_user_prompt(part))
                        elif isinstance(part, ToolReturnPart):
                            message_parts.append(
                                {
                                    'function_response': {
                                        'name': part.tool_name,
                                        'response': part.model_response_object(),
                                        'id': part.tool_call_id,
                                    }
                                }
                            )
                        elif isinstance(part, RetryPromptPart):
                            if part.tool_name is None:
                                message_parts.append({'text': part.model_response()})
                            else:
                                message_parts.append(
                                    {
                                        'function_response': {
                                            'name': part.tool_name,
                                            'response': {'error': part.model_response()},
                                            'id': part.tool_call_id,
                                        }
                                    }
                                )
                        else:
                            assert_never(part)
    
                    if message_parts:
                        contents.append({'role': 'user', 'parts': message_parts})
                elif isinstance(m, ModelResponse):
                    maybe_content = _content_model_response(m, self.system)
                    if maybe_content:
                        contents.append(maybe_content)
                else:
                    assert_never(m)
    
            # Google GenAI requires at least one part in the message.
            if not contents:
                contents = [{'role': 'user', 'parts': [{'text': ''}]}]
    
            if instructions := self._get_instructions(messages, model_request_parameters):
                system_parts.append({'text': instructions})
            system_instruction = ContentDict(role='user', parts=system_parts) if system_parts else None
    
            return system_instruction, contents
    
        async def _map_user_prompt(self, part: UserPromptPart) -> list[PartDict]:
            if isinstance(part.content, str):
                return [{'text': part.content}]
            else:
                content: list[PartDict] = []
                for item in part.content:
                    if isinstance(item, str):
                        content.append({'text': item})
                    elif isinstance(item, BinaryContent):
                        inline_data_dict: BlobDict = {'data': item.data, 'mime_type': item.media_type}
                        part_dict: PartDict = {'inline_data': inline_data_dict}
                        if item.vendor_metadata:
                            part_dict['video_metadata'] = cast(VideoMetadataDict, item.vendor_metadata)
                        content.append(part_dict)
                    elif isinstance(item, VideoUrl) and (
                        item.is_youtube or (item.url.startswith('gs://') and self.system == 'google-vertex')
                    ):
                        # YouTube URLs work on both google-gla and google-vertex
                        # GCS URIs (gs://...) only work on google-vertex (Vertex AI can access GCS buckets)
                        # GCS on google-gla falls through to FileUrl which raises clear error on download attempt
                        # Other URLs fall through to FileUrl handling (download for google-gla)
                        # Note: force_download is not checked here, mirroring the original YouTube behavior.
                        # GCS URIs cannot be downloaded anyway ("gs://" protocol not supported for download).
                        file_data_dict: FileDataDict = {'file_uri': item.url, 'mime_type': item.media_type}
                        part_dict: PartDict = {'file_data': file_data_dict}
                        if item.vendor_metadata:
                            part_dict['video_metadata'] = cast(VideoMetadataDict, item.vendor_metadata)
                        content.append(part_dict)
                    elif isinstance(item, FileUrl):
                        if item.force_download or (
                            # google-gla does not support passing file urls directly, except for youtube videos
                            # (see above) and files uploaded to the file API (which cannot be downloaded anyway)
                            self.system == 'google-gla'
                            and not item.url.startswith(r'https://generativelanguage.googleapis.com/v1beta/files')
                        ):
                            downloaded_item = await download_item(item, data_format='bytes')
                            inline_data: BlobDict = {
                                'data': downloaded_item['data'],
                                'mime_type': downloaded_item['data_type'],
                            }
                            part_dict: PartDict = {'inline_data': inline_data}
                            # VideoUrl is a subclass of FileUrl - include video_metadata if present
                            if isinstance(item, VideoUrl) and item.vendor_metadata:
                                part_dict['video_metadata'] = cast(VideoMetadataDict, item.vendor_metadata)
                            content.append(part_dict)
                        else:
                            file_data_dict: FileDataDict = {'file_uri': item.url, 'mime_type': item.media_type}
                            part_dict: PartDict = {'file_data': file_data_dict}
                            # VideoUrl is a subclass of FileUrl - include video_metadata if present
                            if isinstance(item, VideoUrl) and item.vendor_metadata:
                                part_dict['video_metadata'] = cast(VideoMetadataDict, item.vendor_metadata)
                            content.append(part_dict)  # pragma: lax no cover
                    elif isinstance(item, CachePoint):
                        # Google Gemini doesn't support prompt caching via CachePoint
                        pass
                    else:
                        assert_never(item)
            return content
    
        def _map_response_schema(self, o: OutputObjectDefinition) -> dict[str, Any]:
            response_schema = o.json_schema.copy()
            if o.name:
                response_schema['title'] = o.name
            if o.description:
                response_schema['description'] = o.description
    
            return response_schema
    
