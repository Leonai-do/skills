# Change: Add Sitemap-to-Markdown Skill

## Why

The LeonAI_DO Agent Skills repository currently lacks a specialized skill for extracting and documenting website sitemaps. Users frequently need to:

1. Audit website structures for SEO analysis
2. Generate documentation of site architecture
3. Create markdown inventories of large websites for content management

The existing `url_to_markdown` skill converts single pages but cannot handle XML sitemap parsing, rate limiting for large sites, or hierarchical URL organization. This gap leaves users without an automated solution for sitemap documentation.

## What Changes

### New Agent Skill: `sitemap_to_markdown`

A production-grade skill that converts XML sitemaps to structured Markdown documentation.

**Core Capabilities:**

- Automatic sitemap discovery (`/sitemap.xml`, `/sitemap_index.xml`, `robots.txt`)
- XML streaming parser (`iterparse`) for 50K+ URL sitemaps
- Rate limiting with exponential backoff + jitter (default: 1 req/sec)
- Batch processing and checkpoint/resume for interrupted operations
- Hierarchical URL grouping by path segments
- Structured JSON output for agent consumption

**Files Created:**

- `skills-repository/sitemap_to_markdown/SKILL.md` — Cognitive interface (YAML frontmatter + instructions)
- `skills-repository/sitemap_to_markdown/README.md` — Human documentation
- `skills-repository/sitemap_to_markdown/sitemap_to_markdown.py` — Executable CLI tool
- `skills-repository/sitemap_to_markdown/tests/test_sitemap_to_markdown.py` — pytest unit tests
- `skills-repository/sitemap_to_markdown/tests/fixtures/` — Test XML files
- `skills-repository/sitemap_to_markdown/output/.gitignore` — Ignore generated files

**Compliance with Standards:**
All designs validated against `docs/Agent Skills Creation and Management.pdf`:

- ✅ Directory structure matches Section 5.1
- ✅ SKILL.md follows Section 5.2 cognitive interface pattern
- ✅ Deterministic chain pattern (Section 4.1)
- ✅ Output compaction (Section 4.2)
- ✅ Sandbox security (Section 4.3)
- ✅ Testing strategy (Section 5.4)

## Impact

- **New Spec**: `sitemap-to-markdown` capability added to `openspec/specs/`
- **Skill Repository**: 1 new skill directory with 6+ files
- **Dependencies**: Python packages: `typer`, `pydantic`, `requests` (existing patterns)
- **No Breaking Changes**: Standalone skill, does not modify existing skills

## Test Strategy

### Automated Testing

1. **Unit Tests** (`pytest`):
   - `test_discover_sitemap()` — Sitemap URL discovery logic
   - `test_parse_sitemap_xml()` — XML parsing with namespace handling
   - `test_rate_limiting()` — Exponential backoff timing
   - `test_checkpoint_resume()` — Checkpoint save/load cycle
   - `test_path_validation()` — Path traversal protection

2. **Integration Tests**:
   - Schema discovery: `python sitemap_to_markdown.py --schema`
   - Small sitemap processing (fixture file)
   - Sitemap index processing (fixture file)
   - JSON output structure validation

### Manual Verification

1. Test with live sitemap: `https://www.sitemaps.org/sitemap.xml`
2. Verify output file created in `output/<domain>/`
3. Verify checkpoint file on Ctrl+C interruption
4. Verify resume from checkpoint on re-run

### Validation Tools

```bash
# OpenSpec validation
openspec validate add-sitemap-to-markdown-skill --strict

# Skills validation (post-implementation)
skills-ref validate ./skills-repository/sitemap_to_markdown
python skills-repository/sitemap_to_markdown/sitemap_to_markdown.py --schema
```

## References

- **Critique Report**: [critique_report.md](file:///home/leonai-do/.gemini/antigravity/brain/eb6627e8-4988-4bb0-9ca5-465abd9a928d/critique_report.md)
- **Compliance Report**: [compliance_validation_report.md](file:///home/leonai-do/.gemini/antigravity/brain/eb6627e8-4988-4bb0-9ca5-465abd9a928d/compliance_validation_report.md)
- **Original RAPO Prompt**: [optimized-create-sitemap-to-markdown-skill-20260103-190152.md](file:///home/leonai-do/Host-D-Drive/LeonAI_DO/dev/Agent-Skills/docs/docs-local/2026-01-03/prompts/optimized-create-sitemap-to-markdown-skill-20260103-190152.md)
- **Reference Skill**: [url_to_markdown](file:///home/leonai-do/Host-D-Drive/LeonAI_DO/dev/Agent-Skills/skills-repository/url_to_markdown/)
- **Standards Document**: [Agent Skills Creation and Management.pdf](file:///home/leonai-do/Host-D-Drive/LeonAI_DO/dev/Agent-Skills/docs/Agent%20Skills%20Creation%20and%20Management.pdf)
