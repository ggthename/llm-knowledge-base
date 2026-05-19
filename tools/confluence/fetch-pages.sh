#!/bin/bash
# Fetch all pages under a Confluence root page using API
# Usage: ./fetch-pages.sh SPACE_NAME ROOT_PAGE_ID OUTPUT_DIR

set -e

SPACE_NAME=$1
ROOT_PAGE_ID=$2
OUTPUT_DIR=$3

if [ -z "$SPACE_NAME" ] || [ -z "$ROOT_PAGE_ID" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 SPACE_NAME ROOT_PAGE_ID OUTPUT_DIR"
    exit 1
fi

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/.confluence-config"

echo "🔍 Fetching all pages under: $ROOT_PAGE_ID"
echo "   Space: $SPACE_NAME"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Fetch all pages (pagination)
START=0
LIMIT=50
TOTAL_DOWNLOADED=0
TOTAL_SIZE=0

while true; do
    echo "📥 Fetching pages $START ~ $((START + LIMIT))..."

    # CQL query for all descendants
    CQL_QUERY="ancestor=${ROOT_PAGE_ID}"
    CQL_ENCODED=$(echo "$CQL_QUERY" | jq -sRr @uri)

    # Call Confluence API
    RESPONSE=$(curl -s \
        -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
        "${CONFLUENCE_URL}/rest/api/content/search?cql=${CQL_ENCODED}&expand=body.storage,version,ancestors&limit=${LIMIT}&start=${START}")

    # Parse results
    PAGE_COUNT=$(echo "$RESPONSE" | jq '.results | length')

    # Get total size on first request
    if [ "$START" -eq 0 ]; then
        TOTAL_SIZE=$(echo "$RESPONSE" | jq '.totalSize // 0')
        echo "📊 Total pages: ${TOTAL_SIZE}"
        echo ""
    fi

    if [ "$PAGE_COUNT" -eq 0 ]; then
        break
    fi

    # Save each page as JSON
    echo "$RESPONSE" | jq -c '.results[]' | while read -r page; do
        PAGE_ID=$(echo "$page" | jq -r '.id')
        TITLE=$(echo "$page" | jq -r '.title')

        # Save as JSON file (for Python processing)
        echo "$page" > "$OUTPUT_DIR/${PAGE_ID}.json"

        echo "  ✅ $TITLE (ID: $PAGE_ID)"
    done

    TOTAL_DOWNLOADED=$((TOTAL_DOWNLOADED + PAGE_COUNT))

    # Next page
    START=$((START + LIMIT))

    # Stop if we've fetched all pages
    if [ "$START" -ge "$TOTAL_SIZE" ]; then
        break
    fi

    # Rate limit protection
    sleep 1
done

echo ""
echo "✅ Downloaded: ${TOTAL_DOWNLOADED} pages"
echo "   Output: $OUTPUT_DIR"
