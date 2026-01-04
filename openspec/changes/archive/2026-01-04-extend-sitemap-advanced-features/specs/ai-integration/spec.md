# Spec: AI & LLM Integration

## ADDED Requirements

### Requirement: AI-powered page summarization

The skill SHALL provide AI-powered page summarization when explicitly enabled with the `--summarize` flag.

**Why**: Generate TL;DR for each page automatically.

#### Scenario: Create executive summaries

**Given**: Technical documentation page  
**When**: `--summarize --ai-api-key sk-...`  
**Then**: Frontmatter includes AI summary

### Requirement: Named entity extraction

The skill MUST named entity extraction to enhance content quality.

**Why**: Identify people, organizations, locations in content.

#### Scenario: Extract entities for knowledge graph

**Given**: Documentation mentioning "John Doe at ACME Corp"  
**When**: `--extract-entities`  
**Then**: Frontmatter includes `entities: ["Person: John Doe", "Org: ACME Corp"]`

### Requirement: Semantic chunking for RAG

The skill SHALL split content into semantic chunks for RAG embeddings when the `--semantic-chunk` flag is enabled.

**Why**: Split content into embeddings-friendly chunks.

#### Scenario: Prepare for vector database

**Given**: Long documentation page (5000 tokens)  
**When**: `--semantic-chunk --chunk-size 512`  
**Then**: Page split into 10 chunks, each < 512 tokens

### Requirement: Auto-generated table of contents

The skill SHALL auto-generated table of contents.

**Why**: Improve navigation in long documents.

#### Scenario: Add TOC to engineering docs

**Given**: Page with H1-H6 headings  
**When**: `--generate-toc`  
**Then**: TOC prepended with anchor links

### Requirement: Content translation

The skill SHALL content translation.

**Why**: Multilingual documentation support.

#### Scenario: Translate docs to Spanish

**Given**: English documentation  
**When**: `--translate es --ai-api-key sk-...`  
**Then**: Spanish markdown generated alongside English

## Technical Specifications

```python
# Summarization
from openai import OpenAI
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": f"Summarize: {content[:4000]}"}]
)
summary = response.choices[0].message.content

# Entity extraction
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
entities = [(ent.text, ent.label_) for ent in doc.ents]

# Semantic chunking
def chunk_text(text: str, max_tokens: int) -> List[str]:
    # Split by headings, then by paragraphs
    # Ensure each chunk < max_tokens
    pass
```

## Security Considerations

- Never send content to AI APIs without explicit `--summarize` flag
- API keys via env var, never logged
- User must acknowledge terms: "AI features send content to third-party APIs"

## Cross-References

- **Depends on**: `content-processing` (clean content)
- **Optional**: Requires external API keys
- **High-value for**: RAG systems, knowledge bases
