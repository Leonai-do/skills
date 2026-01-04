# network-crawling Specification

## Purpose
TBD - created by archiving change extend-sitemap-advanced-features. Update Purpose after archive.
## Requirements
### Requirement: Concurrent request processing
The skill SHALL support concurrent request processing for improved performance.

**Why**: Sequential fetching is 10× slower than parallel.

#### Scenario: Fast crawl with concurrency

**Given**: 1000 URLs to fetch  
**When**: `--concurrency 5`  
**Then**: 5 simultaneous requests, ~5× speedup

### Requirement: Proxy support
The skill SHALL proxy support.

**Why**: Corporate networks, geo-restrictions require proxies.

#### Scenario: Crawl through corporate proxy

**Given**: Proxy at `http://proxy.corp.com:8080`  
**When**: `--proxy http://proxy.corp.com:8080`  
**Then**: All requests routed through proxy

### Requirement: Custom headers and authentication
The skill SHALL custom headers and authentication.

**Why**: Some sites require auth tokens, API keys.

#### Scenario: Access authenticated documentation

**Given**: Site requires `Authorization: Bearer <token>`  
**When**: `--headers '{"Authorization": "Bearer xyz"}'`  
**Then**: Header added to all requests

### Requirement: Respect robots.txt
The skill SHALL respect robots.txt.

**Why**: Ethical crawling, avoid getting blocked.

#### Scenario: Obey crawl restrictions

**Given**: robots.txt disallows `/private/`  
**When**: `--respect-robots` enabled  
**Then**: `/private/*` URLs skipped automatically

### Requirement: Configurable timeouts
The skill SHALL configurable timeouts.

**Why**: Slow servers need longer timeouts.

#### Scenario: Handle slow API docs

**Given**: Server responds in 45 seconds  
**When**: `--timeout 60`  
**Then**: Request completes without timeout

