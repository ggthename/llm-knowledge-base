#!/bin/bash

# Incremental Confluence Sync Script
# Syncs only changed pages since last sync

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

# Last sync timestamp file
LAST_SYNC_FILE="$PROJECT_ROOT/.last-sync"

# Get last sync time
if [ -f "$LAST_SYNC_FILE" ]; then
    LAST_SYNC=$(cat "$LAST_SYNC_FILE")
    echo "🔄 Incremental sync since: $LAST_SYNC"
else
    echo "⚠️  No previous sync found. Use sync-space.sh for full sync first."
    exit 1
fi

echo ""
echo "Checking for changes in all configured spaces..."
echo ""

# Get all *_ROOT_PAGE variables
SPACE_VARS=$(set | grep "_ROOT_PAGE=" | cut -d= -f1)

TOTAL_CHANGED=0

for SPACE_VAR in $SPACE_VARS; do
    if [ "$SPACE_VAR" = "PERSONAL_ROOT_PAGE" ]; then
        continue  # Skip personal space for now
    fi

    SPACE_NAME=$(echo "$SPACE_VAR" | sed 's/_ROOT_PAGE//')
    ROOT_PAGE_ID="${!SPACE_VAR}"

    if [ -z "$ROOT_PAGE_ID" ]; then
        continue
    fi

    echo "📂 Checking $SPACE_NAME..."

    # Query Confluence for changed pages using CQL
    # This would typically call the Confluence API
    # For now, we'll trigger a full sync for each space with changes

    # TODO: Implement actual CQL query for changed pages
    # For MVP, just re-run sync-space.sh for each space

    "$SCRIPT_DIR/sync-space.sh" "$SPACE_NAME" 2>&1 | grep -E "(New|Updated|✅)" || true

done

# Update last sync time
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$LAST_SYNC_FILE"

echo ""
echo "✅ Incremental sync completed"
echo "   Last sync: $(cat $LAST_SYNC_FILE)"
