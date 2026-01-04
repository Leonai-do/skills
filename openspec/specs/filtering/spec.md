# filtering Specification

## Purpose
TBD - created by archiving change extend-sitemap-advanced-features. Update Purpose after archive.
## Requirements
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

