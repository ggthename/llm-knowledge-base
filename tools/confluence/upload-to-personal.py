#!/usr/bin/env python3
"""
Markdown 파일을 Confluence 개인 공간에 업로드

사용법:
    python3 upload-to-personal.py <markdown_file>

예시:
    python3 upload-to-personal.py ~/Documents/Obsidian\ Vault/02_Work/Projects/Personal/LOC-스키마-설계-리뷰.md
"""

import json
import os
import re
import sys
from pathlib import Path

import requests


def load_config():
    """환경 변수 로드"""
    config_path = Path(__file__).parent.parent.parent / '.confluence-config'

    if not config_path.exists():
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)

    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # 인라인 주석 제거
                    if '#' in value:
                        value = value.split('#')[0]
                    # 따옴표 제거 및 환경변수 치환
                    value = value.strip().strip('"').strip("'")
                    value = os.path.expandvars(value)
                    config[key] = value

    required = ['CONFLUENCE_URL', 'CONFLUENCE_TOKEN', 'PERSONAL_ROOT_PAGE']
    for key in required:
        if key not in config or not config[key]:
            print(f"❌ {key}가 설정되지 않았습니다.")
            print(f"   .confluence-config 파일을 확인해주세요.")
            sys.exit(1)

    return config


def markdown_to_confluence_storage(md_content):
    """
    Markdown을 Confluence Storage Format으로 변환

    간단한 변환만 지원:
    - 헤딩
    - 리스트
    - 코드 블록
    - 링크
    - 볼드/이탤릭
    """
    lines = md_content.split('\n')
    html_lines = []
    in_code_block = False
    code_language = ''
    code_lines = []

    for line in lines:
        # 코드 블록 시작/종료
        if line.startswith('```'):
            if not in_code_block:
                # 코드 블록 시작
                in_code_block = True
                code_language = line[3:].strip() or 'plain'
                code_lines = []
            else:
                # 코드 블록 종료
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

        # 빈 줄
        if not line.strip():
            html_lines.append('<p><br/></p>')
            continue

        # 헤딩
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            html_lines.append(f'<h{level}>{escape_html(text)}</h{level}>')
            continue

        # 리스트
        list_match = re.match(r'^(\s*)([-*])\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            text = list_match.group(3)
            html_lines.append(f'<ul><li>{escape_html(text)}</li></ul>')
            continue

        # 일반 텍스트 (인라인 포맷팅 처리)
        formatted = format_inline(line)
        html_lines.append(f'<p>{formatted}</p>')

    return '\n'.join(html_lines)


def escape_html(text):
    """HTML 특수문자 이스케이프"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_inline(text):
    """인라인 포맷팅 처리"""
    # 볼드
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 이탤릭
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 코드
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # 링크
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    return escape_html(text)


def extract_title_from_markdown(md_content):
    """Markdown에서 제목 추출 (첫 번째 # 헤딩)"""
    for line in md_content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"


def check_page_exists(confluence_url, token, parent_id, title):
    """해당 제목의 페이지가 이미 존재하는지 확인"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 개인 공간 하위 페이지 검색
    url = f"{confluence_url}/rest/api/content"
    params = {
        'spaceKey': 'CDA',
        'title': title,
        'expand': 'version'
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None

    results = response.json().get('results', [])

    # 부모 페이지 확인
    for page in results:
        page_id = page['id']
        # ancestors 확인
        page_detail_url = f"{confluence_url}/rest/api/content/{page_id}?expand=ancestors"
        detail_response = requests.get(page_detail_url, headers=headers)

        if detail_response.status_code == 200:
            ancestors = detail_response.json().get('ancestors', [])
            # 부모가 개인 공간 루트인지 확인
            if any(ancestor['id'] == parent_id for ancestor in ancestors):
                return page

    return None


def create_or_update_page(confluence_url, token, parent_id, title, content):
    """Confluence 페이지 생성 또는 업데이트"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # 기존 페이지 확인
    existing_page = check_page_exists(confluence_url, token, parent_id, title)

    if existing_page:
        # 업데이트 - 사용자 확인 필요
        page_id = existing_page['id']
        version = existing_page['version']['number']
        page_url = f"{confluence_url}/pages/viewpage.action?pageId={page_id}"

        print()
        print("⚠️  이 페이지는 이미 Confluence에 존재합니다.")
        print(f"   제목: {title}")
        print(f"   URL: {page_url}")
        print(f"   버전: {version}")
        print()
        print("   업로드하면 Confluence의 내용을 덮어씁니다.")
        print("   권장: Confluence 웹에서만 편집하고, 여기서는 읽기 전용으로 사용")
        print()

        try:
            response = input("   계속하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("취소되었습니다.")
                return None
        except (EOFError, KeyboardInterrupt):
            print("\n취소되었습니다.")
            return None

        print()
        print("📤 업데이트 중...")

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
            print(f"✅ 페이지 업데이트 완료: {title}")
            print(f"   URL: {confluence_url}/pages/viewpage.action?pageId={page_id}")
            return page_id
        else:
            print(f"❌ 업데이트 실패: {response.status_code}")
            print(response.text)
            return None

    else:
        # 새로 생성
        data = {
            'type': 'page',
            'title': title,
            'space': {
                'key': 'CDA'
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
            print(f"✅ 페이지 생성 완료: {title}")
            print(f"   URL: {confluence_url}/pages/viewpage.action?pageId={page_id}")
            return page_id
        else:
            print(f"❌ 생성 실패: {response.status_code}")
            print(response.text)
            return None


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 upload-to-personal.py <markdown_file> [parent_page_id]")
        print("  parent_page_id 생략 시 개인 공간 루트에 생성")
        sys.exit(1)

    md_file = Path(sys.argv[1])

    if not md_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {md_file}")
        sys.exit(1)

    print(f"📄 Markdown 파일: {md_file}")

    # 설정 로드
    config = load_config()
    confluence_url = config['CONFLUENCE_URL']
    token = config['CONFLUENCE_TOKEN']

    # Parent ID: 명령어 인자 우선, 없으면 개인 공간 루트
    if len(sys.argv) >= 3:
        parent_id = sys.argv[2]
        print(f"📂 부모 페이지 ID: {parent_id}")
    else:
        parent_id = config['PERSONAL_ROOT_PAGE']
        print(f"📂 개인 공간 루트에 업로드")

    # Markdown 읽기
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 제목 추출
    title = extract_title_from_markdown(md_content)
    print(f"📝 제목: {title}")

    # Confluence Storage Format 변환
    print("🔄 Markdown → Confluence 변환 중...")
    confluence_content = markdown_to_confluence_storage(md_content)

    # 업로드
    print(f"📤 Confluence 개인 공간에 업로드 중...")
    page_id = create_or_update_page(confluence_url, token, parent_id, title, confluence_content)

    if page_id:
        print(f"✅ 완료!")
    else:
        print(f"❌ 실패")
        sys.exit(1)


if __name__ == '__main__':
    main()
