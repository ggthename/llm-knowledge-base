#!/usr/bin/env python3
"""
.confluence-config 로드 유틸리티
Bash 환경변수를 Python에서 사용 가능하게 변환
"""

import os
import subprocess
from pathlib import Path
from typing import Dict


def load_confluence_config() -> Dict[str, str]:
    """
    .confluence-config 파일을 로드하여 환경변수 딕셔너리 반환

    Returns:
        dict: 환경변수 딕셔너리
            - CONFLUENCE_URL
            - CONFLUENCE_TOKEN
            - CATCH_ROOT_PAGE
            - COMMON_ROOT_PAGE
            - CAMA_ROOT_PAGE
            - KNOWLEDGE_ROOT
            - OBSIDIAN_VAULT
    """
    # Find project root dynamically (from tools/confluence/ to project root)
    script_dir = Path(__file__).parent  # tools/confluence/
    knowledge_root = script_dir.parent.parent  # project root
    config_file = knowledge_root / ".confluence-config"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_file}\n"
            f"Please create it from .confluence-config.template"
        )

    # Bash로 변수 로드 후 출력 (echo 방식으로 따옴표 자동 제거)
    cmd = f"""
    source "{config_file}"
    echo "CONFLUENCE_URL=$CONFLUENCE_URL"
    echo "CONFLUENCE_TOKEN=$CONFLUENCE_TOKEN"
    echo "KNOWLEDGE_ROOT=$KNOWLEDGE_ROOT"
    echo "OBSIDIAN_VAULT=$OBSIDIAN_VAULT"
    # Export all *_ROOT_PAGE variables
    set | grep "_ROOT_PAGE=" | while read line; do echo "$line"; done
    """

    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True,
        text=True,
        check=True
    )

    # 파싱
    config = {}
    for line in result.stdout.strip().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            config[key] = value

    return config


def get_paths() -> tuple:
    """
    자주 사용하는 경로들을 Path 객체로 반환

    Returns:
        tuple: (knowledge_root, obsidian_vault, work_dir)
    """
    config = load_confluence_config()

    knowledge_root = Path(config["KNOWLEDGE_ROOT"])
    obsidian_vault = Path(config["OBSIDIAN_VAULT"])
    work_dir = obsidian_vault / "02_Work"

    return knowledge_root, obsidian_vault, work_dir


if __name__ == "__main__":
    # 테스트
    config = load_confluence_config()
    print("✅ Config loaded:")
    for key, value in config.items():
        # 토큰은 일부만 표시
        if key == "CONFLUENCE_TOKEN":
            print(f"  {key}: {value[:10]}...{value[-10:]}")
        else:
            print(f"  {key}: {value}")
