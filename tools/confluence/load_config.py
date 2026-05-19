#!/usr/bin/env python3
"""
.confluence-config Loader Utility
Converts Bash environment variables for Python usage
"""

import os
import subprocess
from pathlib import Path
from typing import Dict


def load_confluence_config() -> Dict[str, str]:
    """
    Load .confluence-config file and return environment variables

    Returns:
        dict: Environment variable dictionary
            - CONFLUENCE_URL
            - CONFLUENCE_TOKEN
            - *_ROOT_PAGE (all variables ending with _ROOT_PAGE)
            - KNOWLEDGE_ROOT
            - OBSIDIAN_VAULT
    """
    # Find project root dynamically (2 levels up from this script)
    script_dir = Path(__file__).parent
    knowledge_root = script_dir.parent.parent
    config_file = knowledge_root / ".confluence-config"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_file}\n"
            f"Please create it from .confluence-config.template"
        )

    # Load all variables from config file
    cmd = f"""
    source "{config_file}"
    # Export all variables defined in the config
    set | grep -E "^(CONFLUENCE_|KNOWLEDGE_|OBSIDIAN_|.*_ROOT_PAGE=)"
    """

    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        check=True
    )

    # Parse
    config = {}
    for line in result.stdout.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            config[key] = value

    return config


def get_paths() -> tuple:
    """
    Return frequently used paths as Path objects

    Returns:
        tuple: (knowledge_root, obsidian_vault, work_dir)
    """
    config = load_confluence_config()

    knowledge_root = Path(config["KNOWLEDGE_ROOT"])
    obsidian_vault = Path(config["OBSIDIAN_VAULT"])
    work_dir = obsidian_vault / "02_Work"

    return knowledge_root, obsidian_vault, work_dir


if __name__ == "__main__":
    # Test
    config = load_confluence_config()
    print("✅ Config loaded:")
    for key, value in config.items():
        # Show partial token only
        if key == "CONFLUENCE_TOKEN":
            if len(value) > 20:
                print(f"  {key}: {value[:10]}...{value[-10:]}")
            else:
                print(f"  {key}: [hidden]")
        else:
            print(f"  {key}: {value}")
