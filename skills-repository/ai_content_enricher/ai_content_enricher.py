import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import re
import typer
from typing_extensions import Annotated
from pydantic import BaseModel, Field
try:
    from pydantic_ai import Agent
    HAS_PYDANTIC_AI = True
except ImportError:
    Agent = None
    HAS_PYDANTIC_AI = False
try:
    import tiktoken
except ImportError:
    tiktoken = None
import aiofiles


app = typer.Typer()

# --- Configuration & Constants ---


MODEL_MAP = {
    # OpenAI (2026)
    'gpt-5.2': 'openai:gpt-5.2', # Thinking Mode, High Reasoning
    'gpt-oss-120b': 'openai:gpt-oss-120b', # Thinking Mode, High Reasoning
    'gpt-oss-20b': 'openai:gpt-oss-20b', # Thinking Mode, High Reasoning
    
    # Anthropic (2026 - v4.5 Series)
    'claude-sonnet-4.5': 'anthropic:claude-sonnet-4-5-20250929',
    'claude-haiku-4.5': 'anthropic:claude-haiku-4-5-20251001',
    'claude-opus-4.5': 'anthropic:claude-opus-4-5-20251101',

    # Google Gemini (2026 - v3/v2.5)
    'gemini-3-pro-preview': 'google-gla:gemini-3-pro-preview', # Native Multimodal
    'gemini-3-flash-preview': 'google-gla:gemini-3-flash-preview',

    # DeepSeek
    'deepseek-v3.1': 'deepseek:deepseek-v3.1',
    'deepseek-reasoner': 'deepseek:deepseek-reasoner',

    # Z.ai (GLM / Zhipu)
    'glm-4.7': 'z-ai:glm-4.7',

    # Ollama (Cloud - via ollama.com)
    'ollama-gpt-oss-120b': 'ollama:gpt-oss:120b-cloud',
    'ollama-gpt-oss-20b': 'ollama:gpt-oss:20b-cloud',
    'ollama-qwen3-coder-480b': 'ollama:qwen3-coder:480b-cloud',
    'ollama-deepseek-671b': 'ollama:deepseek-v3.1:671b-cloud',
    'ollama-kimi-k2': 'ollama:kimi-k2:1t-cloud',
    'ollama-glm-4.6': 'ollama:glm-4.6:cloud',
    'ollama-qwen3-vl': 'ollama:qwen3-vl:235b-cloud',

    # HuggingFace (Inference Endpoints)
    'hf-llama-4-70b': 'huggingface:meta-llama/Llama-4-70b-Instruct',
}


def resolve_model(model_name: str) -> str:
    """Resolve user model name to Pydantic AI format."""
    if ':' in model_name:
        return model_name
    return MODEL_MAP.get(model_name, f'openai:{model_name}')

def truncate_for_model(text: str, max_tokens: int = 4000) -> str:
    """Truncate text to fit within token limit."""
    if not tiktoken:
        # Fallback approximation: 1 token ~= 4 chars
        return text[:max_tokens * 4]
    
    try:
        encoding = tiktoken.get_encoding('cl100k_base')
        tokens = encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return encoding.decode(tokens[:max_tokens]) + "\n\n[Content truncated...]"
    except Exception as e:
        # Fallback on error
        return text[:max_tokens * 4]

def count_tokens(text: str) -> int:
    """Count tokens in text."""
    if not tiktoken:
        return len(text) // 4
    try:
        encoding = tiktoken.get_encoding('cl100k_base')
        return len(encoding.encode(text))
    except Exception:
        return len(text) // 4


# --- Pydantic Models ---

class SummaryOutput(BaseModel):
    summary: str = Field(..., description="Concise 1-3 sentence summary of the content")
    key_topics: list[str] = Field(default_factory=list, description="Main topics covered")

class EntityOutput(BaseModel):
    people: list[str] = Field(default_factory=list, description="Person names mentioned")
    organizations: list[str] = Field(default_factory=list, description="Company/organization names")
    locations: list[str] = Field(default_factory=list, description="Place names, cities, countries")
    dates: list[str] = Field(default_factory=list, description="Date references")
    technologies: list[str] = Field(default_factory=list, description="Technologies, frameworks, languages")


# --- Agents ---

_summarization_agent = None
_entity_agent = None

def get_summarization_agent(model_name: str) -> Optional[Any]:
    global _summarization_agent
    if not HAS_PYDANTIC_AI:
        return None
    
    # We create agent lazily. PydanticAI agents are reusable.
    # Note: Model can be overridden at run time, so fixed model in init is fine or generic.
    if _summarization_agent is None:
        _summarization_agent = Agent(
            model=model_name,
            output_type=SummaryOutput,
            instructions='Summarize the provided content concisely in 1-3 sentences. Identify key topics.'
        )
    return _summarization_agent

def get_entity_agent(model_name: str) -> Optional[Any]:
    global _entity_agent
    if not HAS_PYDANTIC_AI:
        return None
    
    if _entity_agent is None:
        _entity_agent = Agent(
            model=model_name,
            output_type=EntityOutput,
            instructions='Extract named entities from the content. Include people, organizations, locations, dates, and technologies.'
        )
    return _entity_agent


# --- Logic Functions ---

async def generate_summary(content: str, model_name: str, api_key: str) -> Optional[SummaryOutput]:
    if not HAS_PYDANTIC_AI: 
        return None
    
    resolved_model = resolve_model(model_name)
    agent = get_summarization_agent(resolved_model)
    truncated_content = truncate_for_model(content, max_tokens=4000)
    
    # Setup Env Vars for Pydantic AI (it usually reads from env)
    # If using OpenAI, it expects OPENAI_API_KEY.
    # We might need to set it if passed via CLI.
    # Provide keys and endpoints based on provider
    if 'openai' in resolved_model:
        if api_key: os.environ['OPENAI_API_KEY'] = api_key
    elif 'anthropic' in resolved_model:
        if api_key: os.environ['ANTHROPIC_API_KEY'] = api_key
    elif 'google' in resolved_model:
        if api_key: os.environ['GOOGLE_API_KEY'] = api_key
    elif 'deepseek' in resolved_model:
        if api_key: os.environ['DEEPSEEK_API_KEY'] = api_key
    elif 'ollama' in resolved_model:
        # Ollama usually needs OLLAMA_HOST or just works with local, 
        # but for cloud we might need auth if it acts like a remote.
        # Assuming standard env var if library supports it, or custom handling.
        # Pydantic AI usually relies on the underlying client.
        if api_key: os.environ['OLLAMA_API_KEY'] = api_key # hypothetical
    elif 'z-ai' in resolved_model:
        if api_key: os.environ['ZAI_API_KEY'] = api_key
    elif 'huggingface' in resolved_model:
        if api_key: os.environ['HUGGINGFACE_API_KEY'] = api_key
            
    try:
        result = await agent.run(f"Summarize this:\n\n{truncated_content}")
        return result.data
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

async def extract_entities_ai(content: str, model_name: str, api_key: str) -> Optional[EntityOutput]:
    if not HAS_PYDANTIC_AI:
        return None
        
    resolved_model = resolve_model(model_name)
    agent = get_entity_agent(resolved_model)
    truncated_content = truncate_for_model(content, max_tokens=4000)
    
    # Provide keys and endpoints based on provider (duplicated logic, could be helper)
    if 'openai' in resolved_model:
        if api_key: os.environ['OPENAI_API_KEY'] = api_key
    elif 'anthropic' in resolved_model:
        if api_key: os.environ['ANTHROPIC_API_KEY'] = api_key
    elif 'google' in resolved_model:
        if api_key: os.environ['GOOGLE_API_KEY'] = api_key
    elif 'deepseek' in resolved_model:
        if api_key: os.environ['DEEPSEEK_API_KEY'] = api_key
    elif 'ollama' in resolved_model:
        if api_key: os.environ['OLLAMA_API_KEY'] = api_key
    elif 'z-ai' in resolved_model:
        if api_key: os.environ['ZAI_API_KEY'] = api_key
    elif 'huggingface' in resolved_model:
        if api_key: os.environ['HUGGINGFACE_API_KEY'] = api_key
            
    try:
        result = await agent.run(f"Extract entities from:\n\n{truncated_content}")
        return result.data
    except Exception as e:
        print(f"Error extracting entities: {e}")
        return None

def chunk_by_semantics(text: str, max_tokens: int = 512) -> List[str]:
    """Split text by semantic boundaries respecting token limits."""
    chunks = []
    # Match headings levels 1-6
    heading_pattern = re.compile(r'^(#{1,6})\s+.+$', re.MULTILINE)
    
    # Find all heading positions
    matches = list(heading_pattern.finditer(text))
    
    if not matches:
        # Fallback: Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        current_chunk = ""
        for para in paragraphs:
            if count_tokens(current_chunk + para) > max_tokens and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    # Semantic split by headings
    sections = []
    # Text before first heading
    if matches[0].start() > 0:
        sections.append(text[:matches[0].start()])
        
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(text[start:end])
        
    # Merge or split sections to fit max_tokens
    current_chunk = ""
    for section in sections:
        section_tokens = count_tokens(section)
        current_tokens = count_tokens(current_chunk)
        
        if section_tokens > max_tokens:
            # Current section is huge, push existing buffer first
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Sub-split huge section by paragraphs
            # For simplicity here, we just hard truncate or simple split
            # Ideally recursion, but let's do simple char/token cut for now or leave as is (oversized)
            # Strategy: Split huge section by paragraphs
            sub_paragraphs = section.split('\n\n')
            sub_chunk = ""
            for sub_p in sub_paragraphs:
                if count_tokens(sub_chunk + sub_p) > max_tokens and sub_chunk:
                    chunks.append(sub_chunk.strip())
                    sub_chunk = sub_p
                else:
                    sub_chunk += "\n\n" + sub_p if sub_chunk else sub_p
            if sub_chunk.strip():
                chunks.append(sub_chunk.strip())
                
        elif current_tokens + section_tokens > max_tokens:
            chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            current_chunk += section if not current_chunk else "\n" + section
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

@app.command()
def main(
    input_dir: Annotated[Path, typer.Option(help="Directory containing markdown files", exists=True, file_okay=False, dir_okay=True, resolve_path=True)],
    summarize: Annotated[bool, typer.Option(help="Enable ai summarization")] = False,
    extract_entities: Annotated[bool, typer.Option(help="Enable entity extraction")] = False,
    semantic_chunk: Annotated[bool, typer.Option(help="Enable semantic chunking")] = False,
    
    # Provider Configs
    openai_api_key: Annotated[Optional[str], typer.Option(help="OpenAI API Key")] = None,
    openai_base_url: Annotated[Optional[str], typer.Option(help="OpenAI Base URL")] = None,
    
    anthropic_api_key: Annotated[Optional[str], typer.Option(help="Anthropic API Key")] = None,
    anthropic_base_url: Annotated[Optional[str], typer.Option(help="Anthropic Base URL")] = None,
    
    google_api_key: Annotated[Optional[str], typer.Option(help="Google/Gemini API Key")] = None,
    
    deepseek_api_key: Annotated[Optional[str], typer.Option(help="DeepSeek API Key")] = None,
    deepseek_base_url: Annotated[Optional[str], typer.Option(help="DeepSeek Base URL")] = None,
    
    ollama_api_key: Annotated[Optional[str], typer.Option(help="Ollama Cloud API Key")] = None,
    ollama_base_url: Annotated[Optional[str], typer.Option(help="Ollama Base URL (e.g. https://api.ollama.com)")] = None,
    
    zai_api_key: Annotated[Optional[str], typer.Option(help="Z.ai API Key")] = None,
    hf_api_key: Annotated[Optional[str], typer.Option(help="HuggingFace API Key")] = None,

    # General Override (Legacy/Simple)
    ai_api_key: Annotated[Optional[str], typer.Option(help="Generic API Key (applied to selected provider if specific key not missing)")] = None,
    
    ai_model: Annotated[str, typer.Option(help="Model name")] = "gpt-4o",
    concurrency: Annotated[int, typer.Option(help="Number of concurrent files to process")] = 5,
):
    """
    Enrich markdown content with AI summaries, entities, and semantic chunking.
    """
    # Consolidate Keys/URLs into Env Vars
    if openai_api_key: os.environ['OPENAI_API_KEY'] = openai_api_key
    if openai_base_url: os.environ['OPENAI_BASE_URL'] = openai_base_url
    
    if anthropic_api_key: os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key
    if anthropic_base_url: os.environ['ANTHROPIC_BASE_URL'] = anthropic_base_url
    
    if google_api_key: os.environ['GOOGLE_API_KEY'] = google_api_key
    
    if deepseek_api_key: os.environ['DEEPSEEK_API_KEY'] = deepseek_api_key
    if deepseek_base_url: os.environ['DEEPSEEK_BASE_URL'] = deepseek_base_url
    
    if ollama_api_key: os.environ['OLLAMA_API_KEY'] = ollama_api_key # or whatever pydantic-ai uses for ollama auth
    if ollama_base_url: os.environ['OLLAMA_HOST'] = ollama_base_url # Standard Ollama env var
    
    if zai_api_key: os.environ['ZAI_API_KEY'] = zai_api_key
    if hf_api_key: os.environ['HUGGINGFACE_API_KEY'] = hf_api_key

    # Fallback to generic key if provided and specific one missing (logic handled in functions or here)
    # Actually, simpler to just pass ai_api_key as 'api_key' param to functions acting as override/fallback
    pass
    if not (summarize or extract_entities or semantic_chunk):
        print("No AI features enabled. Use --summarize, --extract-entities, or --semantic-chunk.")
        return

    # If using AI features, check if keys are likely present (either in env or passed)
    if (summarize or extract_entities):
        # We can't strict check all because we don't know which model needs what until resolved,
        # but we can warn if NO potential keys are found and args are missing.
        # For now, rely on processing/runtime error if key missing.
        pass

    print(f"Processing directory: {input_dir}")
    print(f"Features: Summarize={summarize}, Entities={extract_entities}, Chunk={semantic_chunk}")
    
    # Run async logic
    asyncio.run(process_files(
        input_dir=input_dir,
        summarize=summarize,
        extract_entities=extract_entities,
        semantic_chunk=semantic_chunk,
        ai_api_key=ai_api_key,
        ai_model=ai_model,
        concurrency=concurrency
    ))


async def process_single_file(
    file_path: Path, 
    summarize: bool, 
    extract_entities: bool, 
    semantic_chunk: bool, 
    ai_api_key: Optional[str], 
    ai_model: str, 
    semaphore: asyncio.Semaphore,
    manifest_lock: asyncio.Lock,
    manifest_data: Dict[str, Any]
):
    async with semaphore:
        try:
            print(f"Processing: {file_path.name}")
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Simple frontmatter parsing
            # Assumes --- at start and end of frontmatter
            frontmatter = ""
            body = content
            if content.startswith("---\n"):
                parts = content.split("---\n", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]
            
            # 1. Summarization
            summary_result = None
            if summarize:
                summary_result = await generate_summary(body, ai_model, ai_api_key)
            
            # 2. Entity Extraction
            entity_result = None
            if extract_entities:
                entity_result = await extract_entities_ai(body, ai_model, ai_api_key)
            
            # 3. Semantic Chunking
            chunks = []
            if semantic_chunk:
                chunks = chunk_by_semantics(body, max_tokens=512)
            
            # Update File Content (Frontmatter)
            new_frontmatter_lines = []
            if frontmatter:
                new_frontmatter_lines.append(frontmatter.strip())
            
            if summary_result:
                new_frontmatter_lines.append(f"summary: \"{summary_result.summary.replace('\"', '\\\"')}\"")
                # key_topics as list
                new_frontmatter_lines.append(f"key_topics: {summary_result.key_topics}")
                
            if entity_result:
                # Add entities to frontmatter? task 3.2 says update/append. 
                # Let's add them as simple structure
                new_frontmatter_lines.append("entities:")
                new_frontmatter_lines.append(f"  people: {entity_result.people}")
                new_frontmatter_lines.append(f"  organizations: {entity_result.organizations}")
                # etc... keeping it brief to avoid massive frontmatter headers if list is huge
            
            if new_frontmatter_lines:
                new_content = "---\n" + "\n".join(new_frontmatter_lines) + "\n---\n" + body
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(new_content)
            
            # Save Chunks
            if chunks:
                base_name = file_path.stem
                for i, chunk in enumerate(chunks, 1):
                    chunk_path = file_path.parent / f"{base_name}-chunk-{i:03d}.md"
                    chunk_header = f"---\nsource: {file_path.name}\nchunk: {i}/{len(chunks)}\n---\n\n"
                    async with aiofiles.open(chunk_path, 'w', encoding='utf-8') as f:
                        await f.write(chunk_header + chunk)

            # Update Manifest (Thread Safe)
            if extract_entities and entity_result:
                async with manifest_lock:
                    rel_path = str(file_path.name) # Using filename as key for now, could use full rel path
                    if "entities" not in manifest_data:
                        manifest_data["entities"] = {}
                    
                    manifest_data["entities"][rel_path] = entity_result.model_dump()
            
            print(f"Completed: {file_path.name}")
            
        except Exception as e:
            print(f"Failed to process {file_path.name}: {e}")

async def process_files(
    input_dir: Path,
    summarize: bool,
    extract_entities: bool,
    semantic_chunk: bool,
    ai_api_key: Optional[str],
    ai_model: str,
    concurrency: int
):
    print("Starting processing...")
    
    # Discovery
    files = list(input_dir.rglob("*.md"))
    # Exclude chunks we just generated to avoid loops if running multiple times? 
    # For now assume clean run or ignore files with -chunk- pattern
    files = [f for f in files if "-chunk-" not in f.name]
    
    print(f"Found {len(files)} markdown files.")
    
    # Manifest Loading
    manifest_path = input_dir / "_manifest.json"
    manifest_data = {}
    if manifest_path.exists():
        async with aiofiles.open(manifest_path, 'r') as f:
            try:
                import json
                content = await f.read()
                manifest_data = json.loads(content)
            except:
                pass
    
    semaphore = asyncio.Semaphore(concurrency)
    manifest_lock = asyncio.Lock()
    
    tasks = [
        process_single_file(
            f, summarize, extract_entities, semantic_chunk, 
            ai_api_key, ai_model, semaphore, manifest_lock, manifest_data
        )
        for f in files
    ]
    
    await asyncio.gather(*tasks)
    
    # Save Manifest
    if extract_entities:
        async with aiofiles.open(manifest_path, 'w') as f:
            import json
            await f.write(json.dumps(manifest_data, indent=2))
    
    print("All files processed.")


if __name__ == "__main__":
    app()
