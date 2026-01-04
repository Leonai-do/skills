# Spec: Enhanced Content Processing

## ADDED Requirements

### Requirement: Extract main content only (remove ads/nav/footer)
The skill MUST extract main content only (remove ads/nav/footer) to enhance content quality.

**Why**: Web pages contain navigation, ads, cookie banners that pollute markdown output.

#### Scenario: Clean documentation extraction

**Given**: HTML page with header, sidebar, main content, footer, ads  
**When**: `--extract-main` flag enabled  
**Then**: Only main article content extracted, noise removed

### Requirement: Download images locally and rewrite paths
The skill MUST download images locally and rewrite paths to enhance content quality.

**Why**: External images may break or disappear; local copies ensure archival.

#### Scenario: Create self-contained archive

**Given**: Page with 10 images from CDN  
**When**: `--download-images` enabled  
**Then**: Images saved to `_images/`, markdown paths rewritten to local

### Requirement: Convert PDF documents to markdown
The skill MUST convert pdf documents to markdown to enhance content quality.

**Why**: Documentation sites often include PDF guides.

#### Scenario: Process PDF technical guide

**Given**: URL pointing to `.pdf` file  
**When**: `--pdf-support` enabled  
**Then**: PDF text extracted and saved as markdown with metadata

### Requirement: Custom CSS selector-based extraction
The skill MUST custom css selector-based extraction to enhance content quality.

**Why**: Sites have non-standard layouts; generic extraction fails.

#### Scenario: Extract specific content div

**Given**: Content in non-standard `<div id="docs-content">`  
**When**: `--content-selector "#docs-content"` set  
**Then**: Only that div's contents extracted

### Requirement: Download all assets for offline viewing
The skill MUST download all assets for offline viewing to enhance content quality.

**Why**: Complete offline archive requires CSS, JS, fonts.

#### Scenario: Create offline-viewable mirror

**Given**: Documentation site with external stylesheets  
**When**: `--download-assets` enabled  
**Then**: CSS/JS/fonts downloaded, HTML rendered correctly offline

## Technical Specifications

```python
# Main content extraction
from readability import Document
doc = Document(html)
clean_html = doc.summary()

# Image downloading
import hashlib
def download_image(url: str, output_dir: Path) -> str:
    response = requests.get(url)
    ext = mimetypes.guess_extension(response.headers.get('Content-Type', ''))
    hash = hashlib.md5(url.encode()).hexdigest()[:8]
    path = output_dir / f"_images/{hash}{ext}"
    path.write_bytes(response.content)
    return str(path.relative_to(output_dir))

# PDF conversion
from pypdf import PdfReader
from io import BytesIO
reader = PdfReader(BytesIO(response.content))
text = "\n\n".join(page.extract_text() for page in reader.pages)
```

## Cross-References

- **Depends on**: `sitemap-content-mirroring` (base functionality)
- **Enables**: `storage` (quality inputs for archives)
