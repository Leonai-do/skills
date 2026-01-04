# Spec: Reporting & Monitoring

## ADDED Requirements

### Requirement: Real-time progress tracking
The skill MUST provide real-time progress tracking for visibility.

**Why**: Long crawls need visibility into current status and ETA.

#### Scenario: Monitor 10-hour crawl

**Given**: Crawling 50,000 pages  
**When**: Progress file enabled  
**Then**: `_progress.json` updates every 10 URLs with ETA, current speed

### Requirement: HTML report generation
The skill MUST provide html report generation for visibility.

**Why**: Human-readable summary of crawl results.

#### Scenario: Share results with team

**Given**: Completed crawl  
**When**: `--html-report` enabled  
**Then**: Interactive HTML report with stats, charts, failed URL table

### Requirement: Diff reporting (compare crawls)
The skill SHALL support diff reporting (compare crawls) for improved performance.

**Why**: Detect content changes over time.

#### Scenario: Weekly documentation audit

**Given**: Previous crawl manifest from last week  
**When**: `--diff-with previous_manifest.json`  
**Then**: Report shows added/removed/changed pages

### Requirement: Webhook notifications
The skill SHALL webhook notifications.

**Why**: Integrate with Slack, Discord, monitoring systems.

#### Scenario: Notify on completion

**Given**: CI/CD pipeline runs daily crawl  
**When**: `--notify-webhook https://hooks.slack.com/...`  
**Then**: POST sent with stats when crawl finishes

### Requirement: Prometheus metrics export
The skill SHALL prometheus metrics export.

**Why**: Production monitoring and alerting.

#### Scenario: Monitor crawl health

**Given**: Metrics file enabled  
**When**: Prometheus scrapes `_metrics.prom`  
**Then**: Gauges show URLs processed, failed, duration

## Technical Specifications

```python
# Progress tracking
progress = {
    "processed": 1234,
    "total": 10000,
    "failed": 5,
    "skipped": 10,
    "elapsed_sec": 300,
    "eta_sec": 2100,
    "current_url": "https://example.com/page"
}

# HTML report template (Jinja2)
from jinja2 import Template
template = Template(open("templates/report.html.j2").read())
html = template.render(manifest=manifest, stats=stats)
```

## Cross-References

- **Depends on**: Core crawling
- **Uses data from**: All phases (filtering stats, performance metrics)
