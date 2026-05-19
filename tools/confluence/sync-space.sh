#!/bin/bash

# Generic Confluence Space Sync Script
# Usage: ./sync-space.sh SPACE_NAME
# Example: ./sync-space.sh ENGINEERING

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load configuration
if [ -f "$PROJECT_ROOT/.confluence-config" ]; then
    source "$PROJECT_ROOT/.confluence-config"
else
    echo "❌ Error: .confluence-config not found"
    echo "Please copy .confluence-config.template to .confluence-config and configure it"
    exit 1
fi

# Check argument
if [ -z "$1" ]; then
    echo "Usage: $0 SPACE_NAME"
    echo "Example: $0 ENGINEERING"
    exit 1
fi

SPACE_NAME=$1
ROOT_PAGE_VAR="${SPACE_NAME}_ROOT_PAGE"
ROOT_PAGE_ID="${!ROOT_PAGE_VAR}"

if [ -z "$ROOT_PAGE_ID" ]; then
    echo "❌ Error: ${ROOT_PAGE_VAR} not defined in .confluence-config"
    exit 1
fi

echo "========================================="
echo "  🔄 Confluence Full Sync: $SPACE_NAME"
echo "========================================="
echo ""
echo "📂 Root Page ID: $ROOT_PAGE_ID"
echo ""

# Temp directory for JSON files
TEMP_DIR="$PROJECT_ROOT/.temp/$SPACE_NAME"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Step 1: Fetch all pages from Confluence API
echo "Step 1: Fetching pages from Confluence..."
echo ""
"$SCRIPT_DIR/fetch-pages.sh" "$SPACE_NAME" "$ROOT_PAGE_ID" "$TEMP_DIR"

echo ""
echo "Step 2: Converting to Markdown..."
echo ""

# Activate Python venv
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo "❌ Error: Python virtual environment not found"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install html2text beautifulsoup4 lxml requests"
    exit 1
fi

# Step 2: Convert JSON to Markdown
python3 "$SCRIPT_DIR/export-generic.py" \
    --space-name "$SPACE_NAME" \
    --root-page-id "$ROOT_PAGE_ID" \
    --output-dir "$OBSIDIAN_VAULT/02_Work/Projects/$SPACE_NAME"

echo ""
echo "========================================="
echo "  ✅ Sync Completed: $SPACE_NAME"
echo "========================================="
echo "   Output: $OBSIDIAN_VAULT/02_Work/Projects/$SPACE_NAME"
