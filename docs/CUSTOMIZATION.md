# ⚙️ Customization Guide

Advanced configuration and customization options.

---

## Configuration Files

### `.confluence-config`
**Purpose**: Confluence connection and paths

**Required variables**:
- `CONFLUENCE_URL`: Your Confluence base URL
- `CONFLUENCE_TOKEN`: API access token
- `*_ROOT_PAGE`: Root page ID for each space
- `KNOWLEDGE_ROOT`: This repo path
- `OBSIDIAN_VAULT`: Obsidian vault path

**Adding new spaces**:
```bash
YOUR_NEW_SPACE_ROOT_PAGE="999888777"
```

Then sync with:
```bash
./tools/confluence/sync-space.sh YOUR_NEW_SPACE
```

---

### `.projects-config`
**Purpose**: Map source code project paths

**Usage**:
- Used for wiki context injection
- Agent detects current project directory
- Injects relevant wiki docs automatically

**Example**:
```bash
PROJECT_MOBILE="$HOME/dev/mobile-app"
PROJECT_API="$HOME/dev/api-service"
```

**Naming convention**: `PROJECT_*` (any name after prefix)

---

### `.moe-config`
**Purpose**: Multi-agent routing rules

**Per-project configuration**: Place in each project root

**Task types**:
- `simple_code`: CRUD, REST APIs, simple logic
- `complex_code`: Security, distributed systems, algorithms
- `doc`: Documentation generation
- `analysis`: Code review and refactoring

**Customizing keywords**:
```yaml
complex_code:
  primary: claude
  keywords:
    - your-framework
    - custom-keyword
    - domain-specific-term
```

---

## Directory Structure Customization

### Change Obsidian Output Location

Default: `~/Documents/Obsidian Vault/02_Work/Projects/SPACE_NAME/`

To customize, edit `export-generic.py`:
```python
OUTPUT_DIR = Path(args.output_dir)
```

Or change `.confluence-config`:
```bash
OBSIDIAN_VAULT="/custom/path/to/vault"
```

### Change Temp Directory

Default: `.temp/`

Edit scripts to change `TEMP_DIR` variable.

---

## Sync Behavior Customization

### Incremental Sync Frequency

Edit cron schedule or run manually:
```bash
# Every 2 hours
0 */2 * * * /path/to/sync-incremental.sh

# Only weekdays at 9 AM
0 9 * * 1-5 /path/to/sync-incremental.sh
```

### Full Sync Schedule

Recommended: Monthly for cleanup

```bash
# First day of month at 2 AM
0 2 1 * * /path/to/sync-space.sh YOUR_SPACE
```

---

## Markdown Conversion Customization

### Code Block Languages

Edit `confluence_converter.py`:
```python
LANGUAGE_MAP = {
    'java': 'java',
    'python': 'python',
    'javascript': 'javascript',
    # Add your custom mappings
}
```

### Link Conversion

To change link format, edit `confluence_link_to_obsidian()` in `confluence_converter.py`.

---

## Adding New Confluence Spaces

1. **Get root page ID** from Confluence URL
2. **Add to `.confluence-config`**:
   ```bash
   NEW_SPACE_ROOT_PAGE="123456789"
   ```
3. **Run full sync**:
   ```bash
   ./tools/confluence/sync-space.sh NEW_SPACE
   ```
4. **Verify in Obsidian**: Check `02_Work/Projects/NEW_SPACE/`

---

## Multi-Space Mapping

To reference pages across spaces:

The system automatically builds cross-space title mappings during sync. 

Confluence links like `[[Other Space Page]]` will resolve if:
1. Both spaces are synced
2. Page title is unique across spaces

---

## Advanced: Custom Python Scripts

### Extending `export-generic.py`

Add custom processing:
```python
def custom_transform(markdown_content):
    # Your custom transformations
    return markdown_content

# In main():
markdown_content = converter.convert(body)
markdown_content = custom_transform(markdown_content)
```

### Adding Metadata

Edit frontmatter in `export-generic.py`:
```python
frontmatter = f"""---
title: {title}
confluence_id: "{page_id}"
custom_field: "your_value"
---
"""
```

---

## Performance Optimization

### Large Spaces (1000+ pages)

1. **Parallel sync**: Modify scripts to sync multiple pages concurrently
2. **Selective sync**: Only sync specific page trees
3. **Incremental only**: Skip full sync, use incremental exclusively

### Image Download

To skip large images, edit `attachment_downloader.py`:
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
```

---

## Troubleshooting Customizations

### Test Configuration

```bash
python3 tools/confluence/load_config.py
```

Should show all your configuration variables.

### Test Sync (Dry Run)

Comment out write operations in `export-generic.py`:
```python
# with open(file_path, 'w', encoding='utf-8') as f:
#     f.write(frontmatter + markdown_content)
print(f"Would write: {file_path}")
```

---

## Community Configurations

Share your customizations! Submit a PR with:
- `examples/your-company-setup.md`
- Custom `.moe-config` for specific tech stacks
- Integration scripts (Notion, Slack, etc.)

---

**Questions?**  
Open an issue on GitHub or check existing configurations in `examples/`
