# storage Specification

## Purpose
TBD - created by archiving change extend-sitemap-advanced-features. Update Purpose after archive.
## Requirements
### Requirement: Multiple output formats
The skill SHALL support multiple output formats for flexible integration.

**Why**: Different use cases need different formats (JSON for APIs, HTML for browsers).

#### Scenario: Export as JSON for search indexing

**Given**: Documentation crawl complete  
**When**: `--output-format json`  
**Then**: Each page saved as structured JSON with metadata

### Requirement: Archive generation
The skill SHALL support archive generation for flexible integration.

**Why**: Distribute complete offline copy as single file.

#### Scenario: Create downloadable documentation archive

**Given**: Crawl complete  
**When**: `--create-archive tar.gz`  
**Then**: `documentation.tar.gz` created with all files

### Requirement: SQLite storage for querying
The skill SHALL support sqlite storage for querying for flexible integration.

**Why**: Enable full-text search, SQL queries on content.

#### Scenario: Build searchable knowledge base

**Given**: Crawl of 10,000 docs  
**When**: `--sqlite-db docs.db`  
**Then**: Query `SELECT * FROM pages WHERE content LIKE '%auth%'`

### Requirement: S3/GCS cloud upload
The skill SHALL s3/gcs cloud upload.

**Why**: Automated backup and distribution.

#### Scenario: Backup to S3

**Given**: AWS credentials configured  
**When**: `--s3-bucket my-docs --s3-prefix v2/`  
**Then**: All files uploaded to `s3://my-docs/v2/`

### Requirement: Single-file concatenated output
The skill SHALL support single-file concatenated output for flexible integration.

**Why**: Simplify distribution, easier for AI ingestion.

#### Scenario: Create one massive markdown file

**Given**: 1000 page documentation  
**When**: `--single-file`  
**Then**: `complete_docs.md` with TOC and all pages

