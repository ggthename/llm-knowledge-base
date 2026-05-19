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

    # Load existing mapping
    mapping = load_mapping(MAPPING_FILE)

    # Initialize converters
    confluence_config = load_confluence_config()
    converter = ConfluenceConverter(mapping)
    downloader = AttachmentDownloader(confluence_config['CONFLUENCE_URL'],
                                      confluence_config['CONFLUENCE_TOKEN'])

    # Get all JSON files
    json_files = list(TEMP_DIR.glob("*.json"))

    if not json_files:
        print(f"⚠️  No JSON files found in {TEMP_DIR}")
        return

    print(f"📄 Found {len(json_files)} pages to process")
    print("")

    # Process pages
    new_count = 0
    updated_count = 0
    skipped_count = 0

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
        is_new = page_id not in mapping

        if is_new:
            status = "✨ New"
            new_count += 1
        else:
            old_path = mapping[page_id].get('file_path', '')
            if str(file_path.relative_to(OUTPUT_DIR)) != old_path:
                status = "📝 Moved"
                updated_count += 1
            else:
                status = "✓ Exists"
                skipped_count += 1

        print(f"{status}: {file_path.relative_to(OUTPUT_DIR)}")

        # Convert to Markdown
        try:
            # Create directory
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert content
            body = page.get('body', {}).get('storage', {}).get('value', '')
            markdown_content = converter.convert_to_markdown(body)

            # Download attachments
            attachments = page.get('_expandable', {}).get('attachments', '')
            if attachments:
                markdown_content = downloader.download_attachments(
                    page_id,
                    markdown_content,
                    file_path.parent
                )

            # Add frontmatter
            frontmatter = f"""---
title: {title}
confluence_id: "{page_id}"
confluence_url: {confluence_config['CONFLUENCE_URL']}/pages/viewpage.action?pageId={page_id}
created: {page.get('history', {}).get('createdDate', '')}
updated: {page.get('version', {}).get('when', '')}
---

"""

            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter + markdown_content)

            # Update mapping
            mapping[page_id] = {
                'file_path': str(file_path.relative_to(OUTPUT_DIR)),
                'title': title,
                'updated': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Save mapping
    save_mapping(mapping, MAPPING_FILE)

    # Summary
    print("")
    print("📊 Summary:")
    print(f"  - New: {new_count}")
    print(f"  - Updated: {updated_count}")
    print(f"  - Skipped: {skipped_count}")
    print(f"  - Total: {len(json_files)}")


if __name__ == '__main__':
    main()
