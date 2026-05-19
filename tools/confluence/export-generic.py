#!/usr/bin/env python3
"""
Generic Confluence to Obsidian Converter
- Converts any Confluence Space to Markdown
- Preserves hierarchy structure
- Downloads images and diagrams
- Converts Confluence links to [[Obsidian links]]
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


def build_hierarchy_path(ancestors: List[Dict], skip_root_id: str) -> Path:
    """Build folder path from ancestors

    Example: Category / Subcategory / Page
    """
    path_parts = []

    for ancestor in ancestors:
        ancestor_id = ancestor.get('id', '')
        ancestor_title = ancestor.get('title', '')

        # Skip root page
        if ancestor_id == skip_root_id:
            continue

        # Clean folder name
        folder_name = clean_filename(ancestor_title)
        if folder_name:
            path_parts.append(folder_name)

    return Path(*path_parts) if path_parts else Path('.')


def load_mapping(mapping_file: Path) -> Dict:
    """Load Page ID → Obsidian file mapping"""
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_mapping(mapping: Dict, mapping_file: Path):
    """Save mapping"""
    mapping_file.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def load_page_json(json_file: Path) -> Optional[Dict]:
    """Load page JSON"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {json_file}: {e}")
        return None


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


def main():
    parser = argparse.ArgumentParser(description='Convert Confluence Space to Obsidian Markdown')
    parser.add_argument('--space-name', required=True, help='Space name (e.g., ENGINEERING)')
    parser.add_argument('--root-page-id', required=True, help='Root page ID')
    parser.add_argument('--output-dir', required=True, help='Output directory path')
    args = parser.parse_args()

    # Setup paths
    KNOWLEDGE_ROOT, OBSIDIAN_VAULT, WORK_DIR = get_paths()
    TEMP_DIR = KNOWLEDGE_ROOT / ".temp" / args.space_name
    OUTPUT_DIR = Path(args.output_dir)
    MAPPING_FILE = OUTPUT_DIR.parent / f".confluence-mapping-{args.space_name.lower()}.json"

    # Ensure directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing mapping (space-separated structure)
    all_mapping = load_mapping(MAPPING_FILE)

    # Get or create this space's mapping
    if args.space_name not in all_mapping:
        all_mapping[args.space_name] = {}

    space_mapping = all_mapping[args.space_name]

    # Initialize converters
    confluence_config = load_confluence_config()
    converter = ConfluenceConverter(all_mapping)  # Pass full mapping for cross-space links
    downloader = AttachmentDownloader(confluence_config['CONFLUENCE_URL'],
                                      confluence_config['CONFLUENCE_TOKEN'])

    # Get all JSON files
    json_files = list(TEMP_DIR.glob("*.json"))

    if not json_files:
        print(f"⚠️  No JSON files found in {TEMP_DIR}")
        return

    print(f"📄 Found {len(json_files)} pages to process")

    # Build full title mapping for Confluence link → [[Obsidian link]] conversion
    print("🔗 Building page title mapping for link conversion...")
    converter.build_full_title_mapping(TEMP_DIR)
    print(f"   ✅ {len(converter.title_to_path)} pages mapped (cross-linking enabled)")
    print("")

    # Statistics
    stats = {
        'new': 0,
        'updated': 0,
        'skipped': 0,
        'deleted': 0,
        'links_converted': 0,
        'attachments_downloaded': 0
    }

    # Track synced page IDs for deletion detection
    synced_page_ids = {json_file.stem for json_file in json_files}

    # Process pages
    for json_file in sorted(json_files):
        page = load_page_json(json_file)
        if not page:
            continue

        page_id = page.get('id', '')
        title = page.get('title', 'Untitled')
        ancestors = page.get('ancestors', [])

        # Build path
        hierarchy_path = build_hierarchy_path(ancestors, args.root_page_id)
        filename = f"{clean_filename(title)}.md"
        file_path = OUTPUT_DIR / hierarchy_path / filename

        # Check if needs update
        is_new = page_id not in space_mapping
        relative_file_path = str(file_path.relative_to(OUTPUT_DIR))

        if is_new:
            status = "✨ New"
            stats['new'] += 1
        else:
            old_path = space_mapping[page_id]
            if relative_file_path != old_path:
                status = "📝 Moved"
                stats['updated'] += 1
            else:
                status = "✓ Exists"
                stats['skipped'] += 1

        print(f"{status}: {relative_file_path}")

        # Convert to Markdown
        try:
            # Create directory
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert content
            body = page.get('body', {}).get('storage', {}).get('value', '')
            markdown_content = converter.convert_to_markdown(body)

            # Count links converted
            links_count = markdown_content.count('[[')
            if links_count > 0:
                stats['links_converted'] += links_count

            # Download attachments
            attachments = page.get('_expandable', {}).get('attachments', '')
            if attachments:
                markdown_content = downloader.download_attachments(
                    page_id,
                    markdown_content,
                    file_path.parent
                )
                # Count attachments (rough estimate)
                stats['attachments_downloaded'] += 1

            # Build parent link
            parent_link = build_parent_link(ancestors, space_mapping, args.root_page_id)
            parent_section = ""
            if parent_link:
                parent_section = f"\n> 📁 **Parent**: {parent_link}\n"

            # Add frontmatter
            frontmatter = f"""---
title: {title}
confluence_id: "{page_id}"
confluence_url: {confluence_config['CONFLUENCE_URL']}/pages/viewpage.action?pageId={page_id}
created: {page.get('history', {}).get('createdDate', '')}
updated: {page.get('version', {}).get('when', '')}
---

"""

            # Write file (frontmatter + parent link + content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter + parent_section + markdown_content)

            # Update mapping (simple: page_id → relative_path)
            space_mapping[page_id] = relative_file_path

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Detect deleted pages (Confluence → Obsidian)
    print("")
    print("🔍 Checking for deleted pages...")
    orphaned_ids = []
    for page_id, relative_path in space_mapping.items():
        if page_id not in synced_page_ids:
            # Page was deleted from Confluence
            orphaned_file = OUTPUT_DIR / relative_path
            if orphaned_file.exists():
                orphaned_file.unlink()
                print(f"  🗑️  Deleted: {relative_path} (Page ID {page_id} removed from Confluence)")
                stats['deleted'] += 1
            orphaned_ids.append(page_id)

    # Remove from mapping
    for page_id in orphaned_ids:
        del space_mapping[page_id]

    # Update all_mapping and save
    all_mapping[args.space_name] = space_mapping
    save_mapping(all_mapping, MAPPING_FILE)

    # Summary
    print("")
    print("=" * 60)
    print("  ✅ Conversion Complete")
    print("=" * 60)
    print("")
    print("📊 Statistics:")
    print(f"  - New: {stats['new']}")
    print(f"  - Updated: {stats['updated']}")
    print(f"  - Skipped: {stats['skipped']}")
    print(f"  - Deleted: {stats['deleted']}")
    print(f"  - 🔗 Links converted: {stats['links_converted']}")
    if stats['attachments_downloaded'] > 0:
        print(f"  - 📎 Attachments downloaded: {stats['attachments_downloaded']}")
    print(f"  - Total: {len(json_files)}")
    print("")
    print(f"📂 Location: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
