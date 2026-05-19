# 🔧 Setup Guide

Complete setup instructions for the LLM Knowledge Base system.

---

## Prerequisites

- **Python 3.7+**
- **Confluence Access**: API token with read permissions
- **Obsidian** (optional but recommended)
- **Claude Code or similar AI assistant** (for multi-agent features)

---

## Step 1: Clone Repository

```bash
git clone https://github.com/ggthename/llm-knowledge-base.git
cd llm-knowledge-base
```

---

## Step 2: Configure Confluence

### 2.1 Get Confluence API Token

1. Log in to your Confluence instance
2. Go to **Settings** → **Personal Access Tokens**
3. Click **Create token**
4. Give it a name (e.g., "LLM Knowledge Base")
5. Set appropriate permissions (read access to your spaces)
6. Copy the token (you won't see it again!)

### 2.2 Find Space Root Page ID

1. Navigate to the root page of your Confluence Space
2. Look at the URL:
   ```
   https://your-company.atlassian.net/wiki/spaces/ABC/pages/123456789/Page+Title
                                                                ^^^^^^^^^ 
                                                                Page ID
   ```
3. Copy the Page ID number

### 2.3 Create Configuration File

```bash
cp .confluence-config.template .confluence-config
vi .confluence-config
```

**Fill in:**
```bash
CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
CONFLUENCE_TOKEN="your_token_here"

# Your main space
ENGINEERING_ROOT_PAGE="123456789"

# Add more spaces as needed
PRODUCT_ROOT_PAGE="987654321"
```

**Security Note**: `.confluence-config` is gitignored. Never commit tokens!

---

## Step 3: Install Python Dependencies

### Option A: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install packages
pip install html2text beautifulsoup4 lxml requests
```

### Option B: System-wide (Not Recommended)

```bash
pip3 install html2text beautifulsoup4 lxml requests
```

### Verify Installation

```bash
python3 -c "import html2text, bs4, lxml, requests; print('✅ All dependencies installed')"
```

---

## Step 4: Configure Obsidian (Optional)

### 4.1 Install Obsidian

Download from: https://obsidian.md

### 4.2 Set Vault Location

The sync scripts expect your vault at:
```
~/Documents/Obsidian Vault
```

To use a different location, edit `.confluence-config`:
```bash
OBSIDIAN_VAULT="/path/to/your/vault"
```

### 4.3 Create Directory Structure

```bash
mkdir -p "$HOME/Documents/Obsidian Vault/02_Work/Projects"
```

---

## Step 5: First Sync

### 5.1 Full Sync (Required First Time)

```bash
./tools/confluence/sync-space.sh ENGINEERING
```

Replace `ENGINEERING` with your space name (from `ENGINEERING_ROOT_PAGE` in config).

**What happens**:
1. Downloads all pages under the root page
2. Converts HTML to Markdown
3. Downloads images and diagrams
4. Converts Confluence links to `[[Obsidian links]]`
5. Saves to `Obsidian Vault/02_Work/Projects/ENGINEERING/`

**Expected output**:
```
🔄 Syncing Confluence Space: ENGINEERING
   Root Page ID: 123456789

📄 Found 150 pages to process

✨ New: Architecture/System-Overview.md
✨ New: Meetings/Weekly-2025-05-19.md
...
📊 Summary:
  - New: 150
  - Updated: 0
  - Skipped: 0
  - Total: 150

✅ Sync completed: ENGINEERING
```

### 5.2 Sync Additional Spaces

```bash
./tools/confluence/sync-space.sh PRODUCT
./tools/confluence/sync-space.sh OPERATIONS
```

---

## Step 6: Configure Projects (Optional)

For wiki context injection, map your source code projects:

```bash
cp .projects-config.template .projects-config
vi .projects-config
```

**Example**:
```bash
PROJECT_BACKEND="$HOME/dev/backend-service"
PROJECT_FRONTEND="$HOME/dev/web-app"
PROJECT_DATA="$HOME/dev/data-pipeline"
```

---

## Step 7: Configure Multi-Agent Routing (Optional)

For AI-assisted coding with multi-agent orchestration:

```bash
# In your project directory
cp ~/path/to/llm-knowledge-base/.moe-config.template .moe-config
vi .moe-config
```

Customize routing rules based on your tech stack.

---

## Step 8: Setup Automated Sync (Optional)

### Option A: Cron (macOS/Linux)

```bash
crontab -e
```

Add:
```cron
# Daily sync at 10 AM
0 10 * * * /path/to/llm-knowledge-base/tools/confluence/sync-incremental.sh >> /path/to/llm-knowledge-base/logs/sync.log 2>&1
```

### Option B: Launchd (macOS)

Create `~/Library/LaunchAgents/com.llm-knowledge-base.sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.llm-knowledge-base.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/llm-knowledge-base/tools/confluence/sync-incremental.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>10</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.llm-knowledge-base.sync.plist
```

---

## Step 9: Verify Setup

### Check Synced Files

```bash
ls -la ~/Documents/Obsidian\ Vault/02_Work/Projects/ENGINEERING/
```

### Open in Obsidian

1. Launch Obsidian
2. Open vault: `~/Documents/Obsidian Vault`
3. Navigate to `02_Work/Projects/ENGINEERING/`
4. Verify:
   - Markdown files exist
   - Images display correctly
   - `[[Links]]` work (Cmd+Click)
   - Graph view shows connections (Cmd+G)

### Test Search

In Obsidian:
- Press `Cmd+O` (Quick Switcher)
- Type a document name
- Should find your synced pages

---

## Common Issues

### Issue: "Permission denied" when running scripts

**Solution**:
```bash
chmod +x tools/confluence/*.sh
```

### Issue: "Module not found: html2text"

**Solution**:
```bash
source .venv/bin/activate
pip install html2text beautifulsoup4 lxml requests
```

### Issue: "Config file not found"

**Solution**:
Check that `.confluence-config` exists and has correct path:
```bash
ls -la .confluence-config
```

### Issue: "API Token invalid"

**Solution**:
1. Verify token hasn't expired
2. Check token has read permissions for your spaces
3. Regenerate token if needed

### Issue: No pages synced

**Solution**:
1. Verify root page ID is correct
2. Check token has access to that space
3. Try navigating to the page in browser first
4. Check logs: `tail -50 logs/sync.log`

---

## Next Steps

- **Daily Usage**: Run `sync-incremental.sh` each morning
- **Monthly**: Full sync with `sync-space.sh` to cleanup deleted pages
- **Multi-Agent**: See [MULTI-AGENT.md](MULTI-AGENT.md) for AI coding setup
- **Customization**: See [CUSTOMIZATION.md](CUSTOMIZATION.md) for advanced config

---

**Need Help?**  
- Check [examples/EXAMPLE-SETUP.md](../examples/EXAMPLE-SETUP.md) for a real-world example
- Open an issue on GitHub
- Review logs in `logs/` directory
