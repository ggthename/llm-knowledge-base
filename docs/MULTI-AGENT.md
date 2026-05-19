# 🤝 Multi-Agent Orchestration Guide

How to use Codex + Claude collaboration for better code quality.

---

## Overview

Multi-Agent Orchestration allows two AI models to collaborate on code generation:
- **Codex**: Fast implementation
- **Claude**: Robust review and architecture

They exchange feedback until converging on the best solution.

---

## Benefits

1. **Higher Quality**: Two perspectives catch more edge cases
2. **Faster Iteration**: Auto-convergence saves manual review rounds
3. **Architecture Compliance**: Claude checks team patterns
4. **Context Awareness**: Wiki context provides team knowledge

---

## How It Works

```
User: "Optimize the authentication flow"
  ↓
System searches wiki for "authentication" docs
  ↓
Codex (Round 1): Proposes fast implementation
  ↓
Claude (Round 1): Reviews, suggests improvements
  ↓
Codex (Round 2): Incorporates feedback
  ↓
Claude (Round 2): Approves or suggests more
  ↓
Auto-convergence when both agree
  ↓
Final code generated
```

---

## Configuration

### Per-Project `.moe-config`

Place in your project root:

```yaml
task_types:
  simple_code:
    primary: codex
    validator: claude
    keywords:
      - crud
      - rest
      - dto

  complex_code:
    primary: claude
    validator: codex
    keywords:
      - authentication
      - security
      - distributed
```

### Routing Logic

- **Keywords match**: Use specified primary agent
- **No match**: Default to `simple_code` rules
- **Validator**: Always reviews primary's output

---

## Usage

See [examples/EXAMPLE-SETUP.md](../examples/EXAMPLE-SETUP.md) for real-world usage patterns.

---

## Advanced

### Custom Convergence Criteria

Edit `tools/agent_orchestrate_moe.py`:
- Max rounds (default: 3)
- Similarity threshold (default: 0.8)
- Feedback keywords for convergence

### Performance Tuning

- Simple tasks: Use single agent (faster)
- Critical code: Use multi-agent (quality)
- Adjust `.moe-config` based on team learning

---

**Note**: Multi-agent orchestration requires Claude Code or similar AI assistant with agent support.
