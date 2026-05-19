#!/usr/bin/env python3
"""
Generic Confluence to Obsidian Converter v7
- Supports any Confluence Space
- Preserves all features from original export-catch.py
- Command-line arguments for flexibility
"""

import os
import re
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from confluence_converter import ConfluenceConverter
from load_config import get_paths, load_confluence_config
from attachment_downloader import AttachmentDownloader


def clean_filename(title: str) -> str:
    """Clean filename for filesystem compatibility"""
    # Remove number prefixes like "1. Title"
    title = re.sub(r'^\d+\.\s*', '', title)

    # Replace special characters
    replacements = {
        '/': '-', '\\': '-', ':': '-', '*': '',
        '?': '', '"': '', '<': '', '>': '', '|': '-',
        '├': '', '└': '', '─': '', '│': ''  # Tree symbols
    }
    for old, new in replacements.items():
        title = title.replace(old, new)

    # Replace spaces with hyphens
    title = re.sub(r'\s+', '-', title)
    # Remove consecutive hyphens
    title = re.sub(r'-+', '-', title)
    # Strip leading/trailing hyphens
    title = title.strip('-')

    return title


def build_hierarchy_path(ancestors: List[Dict], output_dir: Path, root_page_id: str) -> Path:
    """Build folder path from ancestors

    Args:
        ancestors: List of ancestor pages
        output_dir: Base output directory
        root_page_id: Root page ID to skip

    Returns:
        Full path for this page
    """
    path_parts = []

    for ancestor in ancestors:
        ancestor_id = ancestor.get('id', '')
        ancestor_title = ancestor.get('title', '')

        # Skip root page
        if ancestor_id == root_page_id:
            continue

        # Clean folder name
        folder_name = clean_filename(ancestor_title)
        if folder_name:
            path_parts.append(folder_name)

    # Build path from output_dir
    result_path = output_dir
    for part in path_parts:
        result_path = result_path / part

    return result_path


def detect_doc_type(title: str, body: str) -> str:
    """Auto-detect document type from title and content"""
    title_lower = title.lower()
    body_lower = body.lower()[:1000]

    if any(kw in title_lower for kw in ['architecture', '아키텍처', '구조']):
        return 'architecture'
    elif any(kw in title_lower for kw in ['integration', '통합', '연동']):
        return 'integration'
    elif any(kw in title_lower for kw in ['api', 'interface', '인터페이스']):
        return 'api'
    elif any(kw in title_lower for kw in ['tutorial', '튜토리얼', '가이드']):
        return 'tutorial'
    elif any(kw in title_lower for kw in ['weekly', 'biweekly', '회의']):
        return 'meeting'
    else:
        return 'tech-article'


def create_properties_frontmatter(page_data: Dict, space_name: str) -> str:
    """Create properties frontmatter"""
    page_id = page_data.get('id', '')
    title = page_data.get('title', 'Untitled')
    body = page_data.get('body', {}).get('storage', {}).get('value', '')

    doc_type = detect_doc_type(title, body)
    date_str = datetime.now().strftime('%Y-%m-%d')

    props = f"""---
title: "{title}"
project: {space_name}
doc_type: {doc_type}
status: active
priority: medium
confluence_id: "{page_id}"
updated: {date_str}
tags:
  - {space_name.lower()}
  - {doc_type}
  - work
---

"""
    return props


def build_parent_link(ancestors: List[Dict], space_mapping: Dict, root_page_id: str) -> Optional[str]:
    """Build parent page Obsidian link from ancestors

    Args:
        ancestors: List of ancestor pages (root → current)
        space_mapping: Page ID → file path mapping for this space
        root_page_id: Root page ID to skip

    Returns:
        [[parent-path]] or None
    """
    # Ancestors are ordered root → current, so reverse to find immediate parent
    for ancestor in reversed(ancestors):
        ancestor_id = ancestor.get('id', '')

        # Skip root page
        if ancestor_id == root_page_id:
            continue

        # Find parent in mapping
        if ancestor_id in space_mapping:
            parent_path = space_mapping[ancestor_id]
            # Remove .md extension for Obsidian link
            parent_path_no_ext = str(parent_path).replace('.md', '')
            return f"[[{parent_path_no_ext}]]"

    return None


def process_page(
    json_file: Path,
    mapping: Dict,
    stats: Dict,
    space_name: str,
    output_dir: Path,
    work_dir: Path,
    root_page_id: str,
    confluence_url: str,
    converter: ConfluenceConverter = None,
    attachment_downloader: AttachmentDownloader = None
) -> Optional[Dict]:
    """Process a single page (create or update)

    Args:
        json_file: JSON file path
        mapping: Full mapping data (all spaces)
        stats: Statistics dict
        space_name: Space name (e.g., CATCH, ENGINEERING)
        output_dir: Output directory for this space
        work_dir: Base Obsidian work directory
        root_page_id: Root page ID to skip in hierarchy
        confluence_url: Base Confluence URL
        converter: Confluence → Markdown converter
        attachment_downloader: Attachment downloader

    Returns:
        Dict with page info or None
    """
    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        page_data = json.load(f)

    page_id = page_data.get('id', '')
    title = page_data.get('title', 'Untitled')
    ancestors = page_data.get('ancestors', [])
    version_data = page_data.get('version', {})
    last_updated = version_data.get('when', '')
    body_storage = page_data.get('body', {}).get('storage', {}).get('value', '')

    if not page_id:
        print(f"  ⚠️  Skip: No page ID in {json_file.name}")
        return None

    # Get space mapping
    space_mapping = mapping.get(space_name, {})

    # Build hierarchy path
    parent_dir = build_hierarchy_path(ancestors, output_dir, root_page_id)
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    clean_title = clean_filename(title)
    filename = f"{clean_title}.md"
    file_path = parent_dir / filename

    # Relative path (from work_dir)
    relative_path = file_path.relative_to(work_dir)

    # Check existing mapping
    existing_path = space_mapping.get(page_id)

    # Create frontmatter
    frontmatter = create_properties_frontmatter(page_data, space_name)

    page_url = f"{confluence_url}/pages/viewpage.action?pageId={page_id}"

    # Build parent link
    parent_link = build_parent_link(ancestors, space_mapping, root_page_id)
    parent_section = ""
    if parent_link:
        parent_section = f"\n> 📁 **Parent**: {parent_link}\n"

    # Download attachments (images + diagrams)
    attachment_dir = parent_dir / f"attachments_{clean_title}"
    attachments_downloaded = 0
    if attachment_downloader:
        try:
            downloaded = attachment_downloader.download_page_attachments(page_id, attachment_dir)
            attachments_downloaded = len(downloaded)
            if attachments_downloaded > 0:
                stats['attachments_downloaded'] = stats.get('attachments_downloaded', 0) + attachments_downloaded

                # Convert images to Obsidian links (before Markdown conversion)
                body_storage = attachment_downloader.replace_images_with_obsidian_links(
                    body_storage, page_id, attachment_dir, work_dir
                )
        except Exception as e:
            print(f"  ⚠️  Attachment download failed for {title}: {e}")

    # Convert Confluence Storage Format → Markdown + Obsidian link conversion
    if converter:
        body_markdown = converter.convert_to_markdown(body_storage)
        links_count = body_markdown.count('[[')

        # Convert Markdown image links to Obsidian format
        # ![alt](path) → ![[path]]
        if attachments_downloaded > 0:
            # Remove \( \) escapes
            body_markdown = body_markdown.replace(r'\(', '(').replace(r'\)', ')')

            # Convert only image links (paths starting with attachments_)
            body_markdown = re.sub(
                r'!\[([^\]]*)\]\((attachments_.+?\.(?:png|jpg|jpeg|gif|svg|bmp))\)',
                r'![[\2]]',
                body_markdown,
                flags=re.IGNORECASE
            )
    else:
        body_markdown = body_storage
        links_count = 0

    # Diagram files section (Draw.io, Gliffy, etc.)
    diagram_files_section = ""
    if attachments_downloaded > 0 and attachment_dir.exists():
        diagram_files = []
        for f in attachment_dir.iterdir():
            if f.is_file() and not f.name.startswith('.') and f.suffix.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp']:
                diagram_files.append(f.name)

        if diagram_files:
            diagram_files_section = "\n## 📊 Diagrams\n"
            for df in sorted(diagram_files):
                diagram_files_section += f"- [[{attachment_dir.name}/{df}]]\n"

    # Related Notes section (hub-and-spoke structure for graph view)
    related_notes_section = f"""
---

## Related Notes
- [[02_Work/Projects/{space_name}/README|{space_name} Overview]]
"""

    content = f"""{frontmatter}
---
id: {page_id}
title: {title}
last_updated: {last_updated}
source: {page_url}
---
{parent_section}
# {title}

{body_markdown}

---
*Source: Confluence Page ID {page_id}*
*Last Updated: {last_updated}*

{diagram_files_section}{related_notes_section}
"""

    # Check existing file
    if existing_path:
        existing_full_path = work_dir / existing_path

        # Check if path changed
        if existing_full_path != file_path:
            # Path changed: delete old file and create at new location
            if existing_full_path.exists():
                existing_full_path.unlink()
                print(f"  🔄 Move: {existing_path} → {relative_path}")

        # Check if file exists
        if file_path.exists():
            # Compare timestamps
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            existing_ts_match = re.search(r'last_updated:\s*([^\n]+)', existing_content)
            new_ts = last_updated

            if existing_ts_match and existing_ts_match.group(1).strip() == new_ts.strip():
                # No changes
                stats['skipped'] += 1
                return None

        # Update
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  🔄 Update: {relative_path}")
        stats['updated'] += 1
    else:
        # Create new
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✨ New: {relative_path}")
        stats['created'] += 1

    # Update mapping
    if space_name not in mapping:
        mapping[space_name] = {}
    mapping[space_name][page_id] = str(relative_path)

    return {
        'page_id': page_id,
        'title': title,
        'path': str(relative_path),
        'links_count': links_count
    }


def main():
    parser = argparse.ArgumentParser(description='Convert Confluence Space to Obsidian Markdown (Full Features)')
    parser.add_argument('--space-name', required=True, help='Space name (e.g., ENGINEERING, CATCH)')
    parser.add_argument('--root-page-id', required=True, help='Root page ID to skip in hierarchy')
    parser.add_argument('--output-dir', required=True, help='Output directory path')
    parser.add_argument('--no-delete', action='store_true', help='Disable delete detection (for incremental sync)')
    args = parser.parse_args()

    print("=" * 60)
    print(f"  📝 Obsidian Converter v7: {args.space_name}")
    print("=" * 60)
    print()

    # Setup paths
    KNOWLEDGE_ROOT, OBSIDIAN_VAULT, WORK_DIR = get_paths()
    TEMP_DIR = KNOWLEDGE_ROOT / ".temp" / args.space_name
    OUTPUT_DIR = Path(args.output_dir)
    MAPPING_FILE = WORK_DIR / ".confluence-mapping.json"

    # Check source directory
    if not TEMP_DIR.exists():
        print(f"❌ Source directory not found: {TEMP_DIR}")
        print(f"   Run sync script first.")
        return

    # Get JSON files
    json_files = list(TEMP_DIR.glob('*.json'))

    if not json_files:
        print(f"❌ No JSON files found: {TEMP_DIR}")
        return

    print(f"📂 Source: {TEMP_DIR}")
    print(f"📄 Files: {len(json_files)}")
    print()

    # Load mapping
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    else:
        mapping = {}

    # Initialize converters
    config = load_confluence_config()
    converter = ConfluenceConverter(mapping)
    attachment_downloader = AttachmentDownloader(
        config['CONFLUENCE_URL'],
        config['CONFLUENCE_TOKEN']
    )

    # Build full title mapping (for cross-space links)
    print("🔗 Building page title mapping...")
    converter.build_full_title_mapping(TEMP_DIR.parent)  # Scan all spaces in .temp/
    print(f"   ✅ {len(converter.title_to_path)} pages mapped (cross-linking enabled)")
    print()

    # Statistics
    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'deleted': 0,
        'links_converted': 0
    }

    # Track synced page IDs for deletion detection
    synced_page_ids = {json_file.stem for json_file in json_files}

    # Process pages
    for json_file in json_files:
        result = process_page(
            json_file, mapping, stats,
            args.space_name, OUTPUT_DIR, WORK_DIR, args.root_page_id,
            config['CONFLUENCE_URL'],
            converter, attachment_downloader
        )
        if result and result.get('links_count', 0) > 0:
            stats['links_converted'] += result['links_count']

    # Detect deleted pages (full sync only)
    if not args.no_delete and args.space_name in mapping:
        orphaned_ids = []
        for page_id, relative_path in mapping[args.space_name].items():
            if page_id not in synced_page_ids:
                # Page deleted from Confluence
                orphaned_file = WORK_DIR / relative_path
                if orphaned_file.exists():
                    orphaned_file.unlink()
                    print(f"  🗑️  Delete: {relative_path} (Page ID {page_id} removed from Confluence)")
                    stats['deleted'] += 1
                orphaned_ids.append(page_id)

        # Remove from mapping
        for page_id in orphaned_ids:
            del mapping[args.space_name][page_id]
    elif args.no_delete:
        print("  ℹ️  Delete detection disabled (incremental sync mode)")
        print()

    # Save mapping
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    # Create README file (hub for graph view)
    readme_path = OUTPUT_DIR / "README.md"
    if not readme_path.exists():
        readme_content = f"""---
title: {args.space_name} Overview
tags:
  - {args.space_name.lower()}
  - overview
  - index
---

# {args.space_name} Overview

This is the central hub for all {args.space_name} documentation synced from Confluence.

## Statistics
- Total Documents: {len(json_files)}
- Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Navigation
All documents in this space link back to this overview page, creating a hub-and-spoke structure in the graph view.
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"  📝 Created: README.md (graph hub)")

    print()
    print("=" * 60)
    print("  ✅ Conversion Complete")
    print("=" * 60)
    print()
    print(f"📊 Statistics:")
    print(f"  - New: {stats['created']}")
    print(f"  - Updated: {stats['updated']}")
    print(f"  - Skipped: {stats['skipped']}")
    print(f"  - Deleted: {stats['deleted']}")
    print(f"  - 🔗 Links converted: {stats['links_converted']}")
    if stats.get('attachments_downloaded', 0) > 0:
        print(f"  - 📎 Attachments downloaded: {stats['attachments_downloaded']} (images + diagrams)")
    print()
    print(f"📂 Location: {OUTPUT_DIR}")
    print()


if __name__ == '__main__':
    main()
