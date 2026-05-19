# 📚 LLM Knowledge Base + Multi-Agent Development Environment

> AI Second Brain: Sync any Confluence Space to local Obsidian vault for AI-powered development

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Transform your team's Confluence documentation into an **AI-accessible knowledge base** that provides unified context across multiple projects.

**What This Solves**:
1. **Wiki Context**: Auto-sync Confluence docs to local Obsidian for unified context across projects
2. **Multi-Agent Orchestration**: Codex + Claude collaboration with feedback loop for better code quality
3. **Reusable System**: Configuration-driven setup (works with any Confluence Space)

**Key Features**:
- ✅ Auto-sync Confluence → Markdown (Obsidian format)
- ✅ Confluence links → `[[Obsidian links]]` conversion
- ✅ Image & diagram download (PNG, Draw.io, Gliffy)
- ✅ Multi-Agent orchestration (Codex + Claude)
- ✅ Wiki context injection when coding
- ✅ Project-specific agent routing (`.moe-config`)

---

## 🚀 Quick Start (30 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/ggthename/llm-knowledge-base.git
cd llm-knowledge-base
```

### 2. Configure Confluence
```bash
cp .confluence-config.template .confluence-config
vi .confluence-config
```

**Required settings**:
```bash
CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
CONFLUENCE_TOKEN="your_api_token"
YOUR_SPACE_ROOT_PAGE="123456789"  # Root page ID of your Space
```

### 3. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install html2text beautifulsoup4 lxml requests
```

### 4. Sync Documents
```bash
# Full sync (first time)
./tools/confluence/sync-space.sh YOUR_SPACE

# Incremental sync (daily)
./tools/confluence/sync-incremental.sh
```

### 5. Configure Obsidian
1. Open Obsidian
2. Open vault: `~/Documents/Obsidian Vault`
3. Your synced docs are in: `02_Work/Projects/YOUR_SPACE/`

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
│   │   ├── sync-space.sh              # Generic space sync
│   │   ├── sync-incremental.sh        # Incremental sync
│   │   ├── export-generic.py          # Markdown converter
│   │   ├── confluence_converter.py    # Conversion engine
│   │   ├── attachment_downloader.py   # Image/diagram downloader
│   │   └── load_config.py             # Config loader
│   │
│   ├── agent_orchestrate_moe.py       # Multi-agent orchestrator
│   ├── wiki_context.py                # Wiki context injector
│   └── agent-moe.zsh                  # CLI wrapper
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
- Confluence URL, API token
- Space IDs and root page IDs
- Obsidian vault path

### `.projects-config`
- Source code project paths
- Used for wiki context injection

### `.moe-config`
- Multi-agent routing rules
- Task type classification
- Keyword-based routing

---

## 💡 Usage

### Daily Sync
```bash
./tools/confluence/sync-incremental.sh
```

### Full Sync (Monthly)
```bash
./tools/confluence/sync-space.sh YOUR_SPACE
```

### Multi-Agent Code Generation
```bash
# With wiki context
moe-with-wiki "Improve authentication flow"

# Simple task
moe "Add CRUD endpoints"
```

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

**Last Updated**: 2025-05-19  
**Version**: v1.0  
**Maintained by**: [@ggthename](https://github.com/ggthename)
