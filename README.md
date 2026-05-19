# 📚 LLM Knowledge Base + Multi-Agent Development Environment

> AI Second Brain: Confluence Sync + Multi-Agent Orchestration + Project Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

**Customizable AI Development Environment**
- Works with any Confluence Space or organization wiki
- Supports multiple projects with custom agent routing
- Configuration-driven customization (no code changes required)

**What This Solves**:
1. **Wiki Context**: Auto-sync Confluence docs to local Obsidian for unified context across projects
2. **Multi-Agent Orchestration**: Codex + Claude collaboration with feedback loop for better code quality
3. **Project Integration**: Wiki context injection when working across multiple codebases

**Key Features**:
- ✅ Auto-sync Confluence → Markdown (Obsidian format)
- ✅ Confluence links → `[[Obsidian links]]` conversion
- ✅ Image & diagram download (PNG, Draw.io, Gliffy)
- ✅ Multi-Agent orchestration (Codex + Claude)
- ✅ Wiki context injection when coding
- ✅ Project-specific agent routing (`.moe-config`)
- ✅ Auto-convergence (stops when no more improvements)
- ✅ Incremental & full sync support

---

## 🚀 Quick Start (30 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/ggthename/llm-knowledge-base.git
cd llm-knowledge-base
```

### 2. Configure Confluence

**Step 2.1**: Get your Confluence API token
- Go to: https://id.atlassian.com/manage-profile/security/api-tokens
- Click "Create API token"
- Copy the token

**Step 2.2**: Find your Space Root Page ID
- Open your Confluence Space homepage
- URL will look like: `https://company.atlassian.net/wiki/spaces/MYSPACE/pages/123456789/Home`
- The number `123456789` is your Root Page ID

**Step 2.3**: Create config file
```bash
cp .confluence-config.template .confluence-config
vi .confluence-config
```

**Fill in these values**:
```bash
# Confluence connection
CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
CONFLUENCE_TOKEN="paste_your_token_here"

# Your Space settings (example: ENGINEERING space)
ENGINEERING_ROOT_PAGE="123456789"  # Replace with your Root Page ID

# Local paths
KNOWLEDGE_ROOT="$HOME/Develop/llm-knowledge-base"
OBSIDIAN_VAULT="$HOME/Documents/Obsidian Vault"
```

### 3. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install html2text beautifulsoup4 lxml requests
```

### 4. Make Scripts Executable
```bash
chmod +x tools/confluence/*.sh
```

### 5. Sync Documents
```bash
# Full sync (first time) - replace ENGINEERING with your space name
./tools/confluence/sync-space.sh ENGINEERING 123456789

# This will:
# 1. Fetch all pages from Confluence API (fetch-pages.sh)
# 2. Convert to Markdown (export-generic.py)
# 3. Download images and diagrams
# 4. Save to Obsidian vault
```

### 6. Configure Obsidian
1. Open Obsidian
2. Open vault at: `~/Documents/Obsidian Vault` (or your configured path)
3. Your synced docs are in: `02_Work/Projects/ENGINEERING/`
4. Enable graph view to see document connections

---

## 📂 Project Structure

```
llm-knowledge-base/
├── README.md                          # This file
├── .confluence-config.template        # Config template
├── .projects-config.template          # Source project paths
├── .moe-config.template               # Multi-agent routing
├── .gitignore
│
├── tools/
│   ├── confluence/
│   │   ├── sync-space.sh              # Generic space sync (orchestrator)
│   │   ├── fetch-pages.sh             # Confluence API caller
│   │   ├── sync-incremental.sh        # Incremental sync
│   │   ├── export-generic.py          # Markdown converter
│   │   ├── confluence_converter.py    # Conversion engine
│   │   ├── attachment_downloader.py   # Image/diagram downloader
│   │   └── load_config.py             # Config loader
│   │
│   ├── agent_orchestrate_moe.py       # Multi-agent orchestrator
│   ├── wiki_context.py                # Wiki context injector
│   └── agent-moe.zsh                  # CLI wrapper (moe, moe-with-wiki)
│
├── docs/
│   ├── SETUP-GUIDE.md                 # Detailed setup
│   ├── MULTI-AGENT.md                 # Multi-agent guide
│   └── CUSTOMIZATION.md               # Customization guide
│
└── examples/
    ├── EXAMPLE-SETUP.md               # Real-world example
    ├── .confluence-config.example     # Example config
    └── .moe-config.example            # Example routing
```

---

## 🎨 How It Works

### Confluence Sync Pipeline
```
┌─────────────────────────────────────┐
│  Confluence (Your Wiki)             │
│  Architecture, Meetings, Designs    │
└───────────┬─────────────────────────┘
            │ REST API
            ↓
┌─────────────────────────────────────┐
│  Python Converter                   │
│  HTML → Markdown                    │
│  Links → [[Obsidian]]               │
│  Images → Local files               │
└───────────┬─────────────────────────┘
            │
            ↓
┌─────────────────────────────────────┐
│  Obsidian Vault                     │
│  Local searchable knowledge base    │
└─────────────────────────────────────┘
```

### Multi-Agent Collaboration
```
┌─────────────────────────────────────┐
│  Wiki Context                       │
│  Keyword search → Related docs      │
└───────────┬─────────────────────────┘
            │ Inject context
            ↓
┌─────────────────────────────────────┐
│  Codex ↔ Claude                     │
│  Feedback loop → Better code        │
│  Auto-convergence                   │
└─────────────────────────────────────┘
```

---

## 🛠️ Customization

### Multi-Agent Routing (`.moe-config`)

Configure which AI handles which tasks:

```yaml
simple_code:
  primary: codex       # Fast execution
  validator: claude
  keywords:
    - crud
    - rest
    - sql

complex_code:
  primary: claude      # Robust design
  validator: codex
  keywords:
    - authentication
    - security
    - distributed
    - stream-processing
```

### Project-Specific Paths (`.projects-config`)

```bash
# Your source code projects
PROJECT_A="$HOME/dev/backend-service"
PROJECT_B="$HOME/dev/data-pipeline"
PROJECT_C="$HOME/dev/web-frontend"
```

---

## 📖 Real-World Example

See [`examples/EXAMPLE-SETUP.md`](examples/EXAMPLE-SETUP.md) for a complete setup example:

- **Organization**: Large tech company
- **Wiki**: 4 Confluence Spaces (400+ documents)
- **Projects**: 5 codebases (Flink/Kafka, Spring Boot, Airflow, ETL, Deployment)
- **Use Case**: Multi-project development with unified wiki context

---

## 🔧 Configuration Files

### `.confluence-config`

**Purpose**: Connect to your Confluence instance

**Example**:
```bash
# Confluence API
CONFLUENCE_URL="https://mycompany.atlassian.net/wiki"
CONFLUENCE_TOKEN="ATA...xyz123"  # From Atlassian account settings

# Space: ENGINEERING team wiki
ENGINEERING_ROOT_PAGE="909930969"

# Space: PRODUCT team wiki  
PRODUCT_ROOT_PAGE="891487540"

# Local paths
KNOWLEDGE_ROOT="$HOME/Develop/llm-knowledge-base"
OBSIDIAN_VAULT="$HOME/Documents/Obsidian Vault"
```

**How to get values**:
- `CONFLUENCE_URL`: Your company's Confluence domain
- `CONFLUENCE_TOKEN`: Atlassian → Settings → Security → API tokens
- `*_ROOT_PAGE`: Space homepage URL contains the page ID

### `.projects-config`

**Purpose**: Link your source code projects for wiki context injection

**Example**:
```bash
# Backend microservices
AUTH_SERVICE="$HOME/dev/auth-service"
API_GATEWAY="$HOME/dev/api-gateway"

# Data pipelines
ETL_PIPELINE="$HOME/dev/etl-jobs"
STREAM_PROCESSOR="$HOME/dev/kafka-streams"

# Frontend
WEB_APP="$HOME/dev/react-web"
```

**Usage**: When you run `moe-with-wiki "Fix auth bug"`, the system:
1. Searches Obsidian for "auth" keywords
2. Finds related wiki docs
3. Injects context when calling AI
4. Navigates to `$AUTH_SERVICE` to apply changes

### `.moe-config`

**Purpose**: Route tasks to best AI agent (Codex vs Claude)

**Example**:
```yaml
simple_code:
  primary: codex       # Fast for CRUD/REST
  validator: claude
  keywords:
    - crud
    - rest api
    - sql query

complex_code:
  primary: claude      # Better for architecture
  validator: codex
  keywords:
    - authentication
    - distributed system
    - stream processing
    - state management
```

**How it works**:
- Task contains "rest api" → Routes to Codex (fast)
- Task contains "authentication" → Routes to Claude (robust)
- Both agents review each other's output (quality check)

---

## 💡 Usage

### Daily Workflow

**Method 1: Through Claude Code** (Recommended)
```
"Morning sync please"
"Sync all docs"
```

**Method 2: Direct Execution**
```bash
# Incremental sync (daily)
./tools/confluence/sync-incremental.sh

# Full sync (monthly - cleans up deleted pages)
./tools/confluence/sync-space.sh YOUR_SPACE YOUR_ROOT_PAGE_ID
```

**Method 3: Automatic** (cron)
```bash
# Setup once
./setup-auto-sync.sh

# Runs daily at 10 AM automatically
```

### Multi-Agent Orchestration

**Shell Commands** (after loading `agent-moe.zsh`):
```bash
# With wiki context (project-specific)
moe-with-wiki "PROJECT_NAME" "Improve authentication"

# Simple task (no wiki)
moe "Add CRUD endpoints"

# Debate mode (equal collaboration)
debate "Design distributed cache"

# Force specific agent
code-help "REST API implementation"  # Codex primary
doc-help "Write technical doc"       # Claude primary
```

**Through Claude Code** (automatic routing):
```
"Improve Fatigue Rule logic"
→ Claude automatically detects project and uses wiki context

"Add simple utility function"
→ Claude routes to appropriate agent based on complexity
```

### Verify Results

**Obsidian Graph View** (Cmd/Ctrl + G):
- Visualize document connections
- `[[Links]]` show as lines between documents

**Backlinks Panel** (right side):
- Lists documents referencing current page
- Confluence internal links auto-converted to Obsidian links

---

## 🆘 Troubleshooting

### Permission Denied
```bash
chmod +x tools/confluence/*.sh
```

### Python Module Not Found
```bash
source .venv/bin/activate
pip install html2text beautifulsoup4 lxml requests
```

### Confluence API Error
- Check token validity (Settings → Personal Access Tokens)
- Verify Space ID and root page ID
- Check network/VPN access

### AttributeError: 'str' object has no attribute 'keys'
```
Error in export-generic.py: ConfluenceConverter initialization
```
**Fix**: Already fixed in latest version. Make sure you're using:
```python
converter = ConfluenceConverter(mapping)  # Pass dict, not string
```

### FileNotFoundError: Config file not found
```
Error: .confluence-config not found
```
**Fix**: Create config file from template:
```bash
cp .confluence-config.template .confluence-config
vi .confluence-config  # Add your token and settings
```

### Method Not Found: 'convert'
```
AttributeError: 'ConfluenceConverter' object has no attribute 'convert'
```
**Fix**: Already fixed in latest version. Correct method name:
```python
markdown_content = converter.convert_to_markdown(body)
```

### Sync Downloaded 0 Pages
**Possible causes**:
1. Wrong ROOT_PAGE_ID → Check Confluence URL for page ID
2. Invalid API token → Regenerate token
3. Space permissions → Verify you have read access
4. Network issues → Check VPN/firewall

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🌟 Acknowledgments

Inspired by:
- Andrej Karpathy's LLM Knowledge Base architecture
- Obsidian community's note-taking practices
- Multi-agent AI research

---

---

## 📋 Checklist

### Initial Setup (First Time)
- [ ] Clone repository
- [ ] Create `.confluence-config` from template
- [ ] Add Confluence API token
- [ ] Set up Python venv and install dependencies
- [ ] Make scripts executable (`chmod +x`)
- [ ] Run initial sync
- [ ] Load `agent-moe.zsh` in shell
- [ ] Test sync and agent commands

### Regular Maintenance
- [ ] Daily: Incremental sync (automatic or manual)
- [ ] Monthly: Full sync (cleans up deleted pages)
- [ ] Backup: Git push regularly
- [ ] Security: Keep API token secure (never commit)

### Migration to New Machine
- [ ] Clone repository
- [ ] ⚠️ Recreate `.confluence-config` (not in Git)
- [ ] Rebuild Python venv
- [ ] Load shell functions
- [ ] Run full sync
- [ ] Test functionality

---

## 🔗 Related Documentation

- **[SETUP-GUIDE.md](docs/SETUP-GUIDE.md)** - Detailed setup instructions
- **[MULTI-AGENT.md](docs/MULTI-AGENT.md)** - Agent orchestration guide
- **[CUSTOMIZATION.md](docs/CUSTOMIZATION.md)** - How to customize for your team
- **[EXAMPLE-SETUP.md](examples/EXAMPLE-SETUP.md)** - Real-world implementation example

---

**Last Updated**: 2026-05-19  
**Version**: v1.0  
**Maintained by**: [@ggthename](https://github.com/ggthename)

**Features**:
- ✅ Confluence Storage Format → Markdown conversion
- ✅ Confluence links → `[[Obsidian links]]` transformation
- ✅ Image & diagram auto-download (PNG, Draw.io, Gliffy)
- ✅ Code blocks, lists, tables preservation
- ✅ Graph view document relationship visualization
- ✅ Multi-Agent Orchestration (MoE) - Codex + Claude
- ✅ Wiki Context injection - Auto-reference team docs
- ✅ Auto-convergence - Stops when no improvements
- ✅ Configuration-driven - Customize without code changes
- ✅ Incremental & full sync support
- ✅ Deleted page cleanup (full sync)

**Security**:
- ⚠️ `.confluence-config` excluded from Git (contains API token)
- ⚠️ `.temp/`, `logs/` excluded from Git (temporary files)
- ⚠️ `.venv/` excluded from Git (Python environment)
