#!/usr/bin/env python3
"""
Upload Markdown file to Confluence Space

Usage:
    python3 upload-to-confluence.py <markdown_file> <space_key> [parent_page_id]

Examples:
    # Upload to space root (requires PERSONAL_ROOT_PAGE in config)
    python3 upload-to-confluence.py ~/Documents/Obsidian/MyDoc.md MYSPACE

    # Upload under specific page
    python3 upload-to-confluence.py ~/Documents/Obsidian/MyDoc.md MYSPACE 123456789

Features:
    - Auto-converts Markdown to Confluence Storage Format
    - Supports: headings, lists, code blocks, links, bold/italic
    - Warns before overwriting existing pages
    - Extracts title from first # heading
"""

import json
import os
import re
import sys
from pathlib import Path

import requests


def load_config():
    """Load configuration from .confluence-config"""
    config_path = Path(__file__).parent.parent.parent / '.confluence-config'

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print(f"   Create from template: cp .confluence-config.template .confluence-config")
        sys.exit(1)

    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove inline comments
                    if '#' in value:
                        value = value.split('#')[0]
                    # Remove quotes and expand environment variables
                    value = value.strip().strip('"').strip("'")
                    value = os.path.expandvars(value)
                    config[key] = value

    required = ['CONFLUENCE_URL', 'CONFLUENCE_TOKEN']
    for key in required:
        if key not in config or not config[key]:
            print(f"❌ {key} not configured")
            print(f"   Check .confluence-config file")
            sys.exit(1)

    return config


def markdown_to_confluence_storage(md_content):
    """
    Convert Markdown to Confluence Storage Format

    Supports:
    - Headings (h1-h6)
    - Lists (unordered)
    - Code blocks
    - Links
    - Bold/Italic
    """
    lines = md_content.split('\n')
    html_lines = []
    in_code_block = False
    code_language = ''
    code_lines = []

    for line in lines:
        # Code block start/end
        if line.startswith('```'):
            if not in_code_block:
                # Start code block
                in_code_block = True
                code_language = line[3:].strip() or 'plain'
                code_lines = []
            else:
                # End code block
                in_code_block = False
                code_content = '\n'.join(code_lines)
                html_lines.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{code_language}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Empty line
        if not line.strip():
            html_lines.append('<p><br/></p>')
            continue

        # Headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            html_lines.append(f'<h{level}>{escape_html(text)}</h{level}>')
            continue

        # Lists
        list_match = re.match(r'^(\s*)([-*])\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            text = list_match.group(3)
            html_lines.append(f'<ul><li>{escape_html(text)}</li></ul>')
            continue

        # Normal text with inline formatting
        formatted = format_inline(line)
        html_lines.append(f'<p>{formatted}</p>')

    return '\n'.join(html_lines)


def escape_html(text):
    """Escape HTML special characters"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_inline(text):
    """Process inline formatting"""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    return escape_html(text)


def extract_title_from_markdown(md_content):
    """Extract title from Markdown (first # heading)"""
    for line in md_content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"


def check_page_exists(confluence_url, token, space_key, parent_id, title):
    """Check if page with same title already exists"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Search pages in space
    url = f"{confluence_url}/rest/api/content"
    params = {
        'spaceKey': space_key,
        'title': title,
        'expand': 'version'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None

    results = response.json().get('results', [])

    # Check parent page
    for page in results:
        page_id = page['id']
        # Check ancestors
        page_detail_url = f"{confluence_url}/rest/api/content/{page_id}?expand=ancestors"
        detail_response = requests.get(page_detail_url, headers=headers)

        if detail_response.status_code == 200:
            ancestors = detail_response.json().get('ancestors', [])
            # Check if parent matches
            if any(ancestor['id'] == parent_id for ancestor in ancestors):
                return page

    return None


def create_or_update_page(confluence_url, token, space_key, parent_id, title, content):
    """Create or update Confluence page"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Check existing page
    existing_page = check_page_exists(confluence_url, token, space_key, parent_id, title)

    if existing_page:
        # Update - requires user confirmation
        page_id = existing_page['id']
        version = existing_page['version']['number']
        page_url = f"{confluence_url}/pages/viewpage.action?pageId={page_id}"

        print()
        print("⚠️  This page already exists in Confluence")
        print(f"   Title: {title}")
        print(f"   URL: {page_url}")
        print(f"   Version: {version}")
        print()
        print("   Upload will overwrite Confluence content")
        print("   Recommendation: Edit only in Confluence web, use sync for read-only")
        print()

        try:
            response = input("   Continue? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled")
                return None
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled")
            return None

        print()
        print("📤 Updating...")

        data = {
            'version': {
                'number': version + 1
            },
            'title': title,
            'type': 'page',
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }

        url = f"{confluence_url}/rest/api/content/{page_id}"
        response = requests.put(url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            print(f"✅ Page updated: {title}")
            print(f"   URL: {confluence_url}/pages/viewpage.action?pageId={page_id}")
            return page_id
        else:
            print(f"❌ Update failed: {response.status_code}")
            print(response.text)
            return None

    else:
        # Create new page
        data = {
            'type': 'page',
            'title': title,
            'space': {
                'key': space_key
            },
            'ancestors': [
                {'id': int(parent_id)}
            ],
            'body': {
                'storage': {
                    'value': content,
                    'representation': 'storage'
                }
            }
        }

        url = f"{confluence_url}/rest/api/content"
        response = requests.post(url, headers=headers, json=data)

        if response.status_code in [200, 201]:
            page_id = response.json()['id']
            print(f"✅ Page created: {title}")
            print(f"   URL: {confluence_url}/pages/viewpage.action?pageId={page_id}")
            return page_id
        else:
            print(f"❌ Creation failed: {response.status_code}")
            print(response.text)
            return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 upload-to-confluence.py <markdown_file> <space_key> [parent_page_id]")
        print()
        print("Examples:")
        print("  python3 upload-to-confluence.py ~/Docs/MyDoc.md MYSPACE")
        print("  python3 upload-to-confluence.py ~/Docs/MyDoc.md MYSPACE 123456789")
        print()
        print("Note: If parent_page_id is omitted, PERSONAL_ROOT_PAGE from .confluence-config is used")
        sys.exit(1)

    md_file = Path(sys.argv[1])
    space_key = sys.argv[2]

    if not md_file.exists():
        print(f"❌ File not found: {md_file}")
        sys.exit(1)

    print(f"📄 Markdown file: {md_file}")
    print(f"📂 Space: {space_key}")

    # Load config
    config = load_config()
    confluence_url = config['CONFLUENCE_URL']
    token = config['CONFLUENCE_TOKEN']

    # Parent ID: command arg or config default
    if len(sys.argv) >= 4:
        parent_id = sys.argv[3]
        print(f"📂 Parent page ID: {parent_id}")
    else:
        if 'PERSONAL_ROOT_PAGE' not in config:
            print("❌ parent_page_id required (PERSONAL_ROOT_PAGE not configured)")
            sys.exit(1)
        parent_id = config['PERSONAL_ROOT_PAGE']
        print(f"📂 Using PERSONAL_ROOT_PAGE from config")

    # Read Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Extract title
    title = extract_title_from_markdown(md_content)
    print(f"📝 Title: {title}")

    # Convert to Confluence Storage Format
    print("🔄 Converting Markdown → Confluence...")
    confluence_content = markdown_to_confluence_storage(md_content)

    # Upload
    print(f"📤 Uploading to Confluence...")
    page_id = create_or_update_page(confluence_url, token, space_key, parent_id, title, confluence_content)

    if page_id:
        print(f"✅ Done!")
    else:
        print(f"❌ Failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
