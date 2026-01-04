# Spec: URL Filtering & Selection

## ADDED Requirements

### Requirement: Content authors can filter URLs by regex pattern

The skill SHALL filter URLs based on content authors can filter urls by regex pattern to reduce crawl scope.

**Why**: Processing entire sitemaps wastes bandwidth and time when only specific sections are needed (e.g., `/docs/*` for documentation sites).

**Impact**: Reduces crawl time by 50-90% for targeted use cases.

#### Scenario: Include only documentation URLs

**Given**: A sitemap containing 10,000 URLs with `/docs/`, `/blog/`, and `/products/` sections

**When**: User runs `--include-pattern "^.*/docs/.*$"`

**Then**:

- Only URLs matching `/docs/*` are processed
- Other URLs are logged as filtered
- Manifest includes `filtered_count` statistic
- Total processing time is 10× faster

#### Scenario: Exclude blog and archive sections

**Given**: A sitemap with `/blog/` and `/archive/` sections to exclude

**When**: User runs `--exclude-pattern "^.*/(blog|archive)/.*$"`

**Then**:

- URLs matching the pattern are skipped
- Processed URLs do not include blog or archive pages
- Filtered URLs are tracked separately in manifest

#### Scenario: Complex filter combination

**Given**: User wants only `/docs/api/*` but not `/docs/api/legacy/*`

**When**: User runs `--include-pattern "^.*/docs/api/.*$" --exclude-pattern ".*/legacy/.*"`

**Then**:

- Filter logic is applied in order (include first, then exclude)
- Only current API docs are processed
- Legacy docs are filtered out

### Requirement: Content authors can filter URLs by path prefix

The skill SHALL filter URLs based on content authors can filter urls by path prefix to reduce crawl scope.

**Why**: Path prefixes are simpler than regex for common use cases.

**Impact**: Easier syntax for non-technical users.

#### Scenario: Include multiple top-level sections

**Given**: A sitemap with `/docs/`, `/api/`, `/tutorials/` sections

**When**: User runs `--include-paths "/docs,/api"`

**Then**:

- Only URLs starting with `/docs/` or `/api/` are processed
- Other sections are filtered out
- No regex knowledge required

#### Scenario: Exclude specific paths

**Given**: A need to exclude `/tag/` and `/category/` routes

**When**: User runs `--exclude-paths "/tag,/category"`

**Then**:

- Tag and category pages are skipped
- Main content pages are processed normally

### Requirement: Content authors can filter by sitemap priority

The skill SHALL filter URLs based on content authors can filter by sitemap priority to reduce crawl scope.

**Why**: Sitemap priority indicates page importance (0.0-1.0).

**Impact**: Focus on high-value pages first.

#### Scenario: Only process high-priority pages

**Given**: Sitemap with priority values ranging from 0.3 to 1.0

**When**: User runs `--priority-min 0.8`

**Then**:

- Only URLs with `<priority>` ≥ 0.8 are processed
- Lower priority pages are filtered
- Manifest shows priority-based filtering stats

### Requirement: Content authors can filter by change frequency

The skill SHALL filter URLs based on content authors can filter by change frequency to reduce crawl scope.

**Why**: Target pages that update frequently (e.g., `daily`) vs static content.

**Impact**: Useful for incremental update strategies.

#### Scenario: Only process frequently updated content

**Given**: Sitemap with `<changefreq>` values: `always`, `daily`, `monthly`

**When**: User runs `--changefreq daily`

**Then**:

- Only pages marked as `daily` are processed
- Other frequencies are filtered
- Useful for news/blog sites

---

## ADDED Requirements

### Requirement: Checkpoint tracks filtered URLs

The skill SHALL track filtered URLs in checkpoint to enable efficient resume after filter changes.

**Previous**: Checkpoint only tracked `processed`, `failed`, `skipped`

**Now**: Checkpoint also tracks `filtered_urls: List[str]`

**Why**: Enable resume after filtering changes (don't re-filter already filtered URLs).

#### Scenario: Resume after filter adjustment

**Given**: User started crawl with `--include-pattern "docs"`, stopped halfway

**When**: User resumes with same pattern

**Then**:

- Previously filtered URLs are not re-evaluated
- Only unprocessed URLs are filtered and processed
- Resume is efficient

---

## Technical Specifications

### CLI Flags

```python
class InputModel(BaseModel):
    # Regex filtering
    include_pattern: Optional[str] = Field(None, description="Regex pattern to include URLs")
    exclude_pattern: Optional[str] = Field(None, description="Regex pattern to exclude URLs")

    # Path filtering
    include_paths: Optional[str] = Field(None, description="Comma-separated path prefixes to include")
    exclude_paths: Optional[str] = Field(None, description="Comma-separated path prefixes to exclude")

    # Attribute filtering
    priority_min: Optional[float] = Field(None, description="Minimum sitemap priority (0.0-1.0)")
    changefreq: Optional[str] = Field(None, description="Filter by changefreq value")
```

### Filter Logic

```python
def should_process_url(
    url: str,
    meta: dict,
    include_pattern: Optional[str],
    exclude_pattern: Optional[str],
    include_paths: Optional[List[str]],
    exclude_paths: Optional[List[str]],
    priority_min: Optional[float],
    changefreq: Optional[str]
) -> bool:
    # All filters must pass (AND logic)

    # 1. Regex include
    if include_pattern and not re.match(include_pattern, url):
        return False

    # 2. Regex exclude
    if exclude_pattern and re.match(exclude_pattern, url):
        return False

    # 3. Path include
    if include_paths:
        path = urlparse(url).path
        if not any(path.startswith(p) for p in include_paths):
            return False

    # 4. Path exclude
    if exclude_paths:
        path = urlparse(url).path
        if any(path.startswith(p) for p in exclude_paths):
            return False

    # 5. Priority filter
    if priority_min is not None:
        priority = float(meta.get('priority', 1.0))
        if priority < priority_min:
            return False

    # 6. Changefreq filter
    if changefreq and meta.get('changefreq') != changefreq:
        return False

    return True
```

### Manifest Updates

```json
{
  "version": "1.0",
  "statistics": {
    "total_urls_in_sitemap": 10000,
    "filtered_count": 9500,
    "processed_count": 450,
    "failed_count": 20,
    "skipped_count": 30
  },
  "filters_applied": {
    "include_pattern": "^.*/docs/.*$",
    "priority_min": 0.5
  },
  "filtered_urls": ["https://example.com/blog/post1", "..."]
}
```

## Cross-References

- **Depends on**: None (standalone feature)
- **Related to**: `sitemap-content-mirroring` (spec/sitemap-content-mirroring/spec.md)
- **Enables**: Faster targeted crawls for `reporting`, `storage` phases
