---
url: https://ai.pydantic.dev/input/
date: 2026-01-03T23:40:08.601343
---

# Image, Audio, Video & Document Input

Some LLMs are now capable of understanding audio, video, image and document content.

## Image Input

Info

Some models do not support image input. Please check the model's documentation to confirm whether it supports image input.

If you have a direct URL for the image, you can use [`ImageUrl`](../api/messages/#pydantic_ai.messages.ImageUrl "ImageUrl

  
      dataclass
  "):

If you have the image locally, you can also use [`BinaryContent`](../api/messages/#pydantic_ai.messages.BinaryContent "BinaryContent

  
      dataclass
  "):

With Pydantic AI GatewayDirectly to Provider API

[Learn about Gateway](../gateway) local_image_input.py
    
    
    import httpx
    
    from pydantic_ai import Agent, BinaryContent
    
    image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo
    
    agent = Agent(model='gateway/openai:gpt-5')
    result = agent.run_sync(
        [
            'What company is this logo from?',
            BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
        ]
    )
    print(result.output)
    #> This is the logo for Pydantic, a data validation and settings management library in Python.
    

  1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.

local_image_input.py
    
    
    import httpx
    
    from pydantic_ai import Agent, BinaryContent
    
    image_response = httpx.get('https://iili.io/3Hs4FMg.png')  # Pydantic logo
    
    agent = Agent(model='openai:gpt-5')
    result = agent.run_sync(
        [
            'What company is this logo from?',
            BinaryContent(data=image_response.content, media_type='image/png'),  # (1)!
        ]
    )
    print(result.output)
    #> This is the logo for Pydantic, a data validation and settings management library in Python.
    

  1. To ensure the example is runnable we download this image from the web, but you can also use `Path().read_bytes()` to read a local file's contents.

## Audio Input

Info

Some models do not support audio input. Please check the model's documentation to confirm whether it supports audio input.

You can provide audio input using either [`AudioUrl`](../api/messages/#pydantic_ai.messages.AudioUrl "AudioUrl

  
      dataclass
  ") or [`BinaryContent`](../api/messages/#pydantic_ai.messages.BinaryContent "BinaryContent

  
      dataclass
  "). The process is analogous to the examples above.

## Video Input

Info

Some models do not support video input. Please check the model's documentation to confirm whether it supports video input.

You can provide video input using either [`VideoUrl`](../api/messages/#pydantic_ai.messages.VideoUrl "VideoUrl

  
      dataclass
  ") or [`BinaryContent`](../api/messages/#pydantic_ai.messages.BinaryContent "BinaryContent

  
      dataclass
  "). The process is analogous to the examples above.

## Document Input

Info

Some models do not support document input. Please check the model's documentation to confirm whether it supports document input.

You can provide document input using either [`DocumentUrl`](../api/messages/#pydantic_ai.messages.DocumentUrl "DocumentUrl

  
      dataclass
  ") or [`BinaryContent`](../api/messages/#pydantic_ai.messages.BinaryContent "BinaryContent

  
      dataclass
  "). The process is similar to the examples above.

If you have a direct URL for the document, you can use [`DocumentUrl`](../api/messages/#pydantic_ai.messages.DocumentUrl "DocumentUrl

  
      dataclass
  "):

The supported document formats vary by model.

You can also use [`BinaryContent`](../api/messages/#pydantic_ai.messages.BinaryContent "BinaryContent

  
      dataclass
  ") to pass document data directly:

## User-side download vs. direct file URL

When using one of `ImageUrl`, `AudioUrl`, `VideoUrl` or `DocumentUrl`, Pydantic AI will default to sending the URL to the model provider, so the file is downloaded on their side.

Support for file URLs varies depending on type and provider:

Model | Send URL directly | Download and send bytes | Unsupported  
---|---|---|---  
[`OpenAIChatModel`](../api/models/openai/#pydantic_ai.models.openai.OpenAIChatModel "OpenAIChatModel

  
      dataclass
  ") | `ImageUrl` | `AudioUrl`, `DocumentUrl` | `VideoUrl`  
[`OpenAIResponsesModel`](../api/models/openai/#pydantic_ai.models.openai.OpenAIResponsesModel "OpenAIResponsesModel

  
      dataclass
  ") | `ImageUrl`, `AudioUrl`, `DocumentUrl` | — | `VideoUrl`  
[`AnthropicModel`](../api/models/anthropic/#pydantic_ai.models.anthropic.AnthropicModel "AnthropicModel

  
      dataclass
  ") | `ImageUrl`, `DocumentUrl` (PDF) | `DocumentUrl` (`text/plain`) | `AudioUrl`, `VideoUrl`  
[`GoogleModel`](../api/models/google/#pydantic_ai.models.google.GoogleModel "GoogleModel

  
      dataclass
  ") (Vertex) | All URL types | — | —  
[`GoogleModel`](../api/models/google/#pydantic_ai.models.google.GoogleModel "GoogleModel

  
      dataclass
  ") (GLA) | [YouTube](../models/google/#document-image-audio-and-video-input), [Files API](../models/google/#document-image-audio-and-video-input) | All other URLs | —  
[`MistralModel`](../api/models/mistral/#pydantic_ai.models.mistral.MistralModel "MistralModel

  
      dataclass
  ") | `ImageUrl`, `DocumentUrl` (PDF) | — | `AudioUrl`, `VideoUrl`, `DocumentUrl` (non-PDF)  
[`BedrockConverseModel`](../api/models/bedrock/#pydantic_ai.models.bedrock.BedrockConverseModel "BedrockConverseModel

  
      dataclass
  ") | S3 URLs (`s3://`) | `ImageUrl`, `DocumentUrl`, `VideoUrl` | `AudioUrl`  
  
A model API may be unable to download a file (e.g., because of crawling or access restrictions) even if it supports file URLs. For example, [`GoogleModel`](../api/models/google/#pydantic_ai.models.google.GoogleModel "GoogleModel

  
      dataclass
  ") on Vertex AI limits YouTube video URLs to one URL per request. In such cases, you can instruct Pydantic AI to download the file content locally and send that instead of the URL by setting `force_download` on the URL object:

force_download.py
    
    
    from pydantic_ai import ImageUrl, AudioUrl, VideoUrl, DocumentUrl
    
    ImageUrl(url='https://example.com/image.png', force_download=True)
    AudioUrl(url='https://example.com/audio.mp3', force_download=True)
    VideoUrl(url='https://example.com/video.mp4', force_download=True)
    DocumentUrl(url='https://example.com/doc.pdf', force_download=True)
    

## Uploaded Files

Some model providers support passing URLs to files hosted on their platform:

  - [`GoogleModel`](../api/models/google/#pydantic_ai.models.google.GoogleModel "GoogleModel

  
      dataclass
  ") supports the [Files API](../models/google/#document-image-audio-and-video-input) for uploading and referencing files.
  - [`BedrockConverseModel`](../api/models/bedrock/#pydantic_ai.models.bedrock.BedrockConverseModel "BedrockConverseModel

  
      dataclass
  ") supports `s3://<bucket-name>/<object-key>` URIs, provided that the assumed role has the `s3:GetObject` permission. An optional `bucketOwner` query parameter must be specified if the bucket is not owned by the account making the request. For example: `s3://my-bucket/my-file.png?bucketOwner=123456789012`.

