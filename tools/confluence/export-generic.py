#!/usr/bin/env python3
"""
Obsidian 변환 v7 - 환경변수 통합
- .confluence-config에서 경로 로드
- Confluence 계층 구조를 Obsidian 폴더로 반영
- Page ID 추적 및 스마트 업데이트
- Confluence Storage Format → Markdown 변환
- Confluence 내부 링크 → [[Obsidian 링크]] 변환
"""

import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from confluence_converter import ConfluenceConverter
from load_config import get_paths, load_confluence_config
from attachment_downloader import AttachmentDownloader

# 설정 로드
KNOWLEDGE_ROOT, OBSIDIAN_VAULT, WORK_DIR = get_paths()
TEMP_DIR = KNOWLEDGE_ROOT / ".temp"
CATCH_DIR = WORK_DIR / "Projects" / "CATCH"

# 소스 디렉토리
SOURCE_DIR = TEMP_DIR / "catch-full"

# 페이지 ID 매핑 파일
MAPPING_FILE = WORK_DIR / ".confluence-mapping.json"

# CATCH Root를 건너뛸 ancestors ID
SKIP_ANCESTORS = {
    "28911233",  # 데이터서비스개발팀
    "909930969",  # ├─ 02-2 CATCH
}


def load_mapping() -> Dict:
    """Confluence Page ID → Obsidian 파일 매핑 로드"""
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_mapping(mapping: Dict):
    """매핑 저장"""
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def clean_filename(title: str) -> str:
    """파일명으로 사용 가능하도록 정리"""
    # 번호. 제목 형식에서 번호 제거
    title = re.sub(r'^\d+\.\s*', '', title)

    # 특수문자 제거/변경
    replacements = {
        '/': '-', '\\': '-', ':': '-', '*': '',
        '?': '', '"': '', '<': '', '>': '', '|': '-',
        '├': '', '└': '', '─': '', '│': ''  # 계층 표시 문자 제거
    }
    for old, new in replacements.items():
        title = title.replace(old, new)

    # 공백을 하이픈으로
    title = re.sub(r'\s+', '-', title)
    # 연속 하이픈 제거
    title = re.sub(r'-+', '-', title)
    # 앞뒤 하이픈 제거
    title = title.strip('-')

    return title


def build_hierarchy_path(ancestors: List[Dict]) -> Path:
    """Ancestors 정보로 폴더 경로 생성

    예: 17 CATCH / 91. 회의자료 / [내부] Weekly
    """
    path_parts = []

    for ancestor in ancestors:
        ancestor_id = ancestor.get('id', '')
        ancestor_title = ancestor.get('title', '')

        # SKIP_ANCESTORS에 포함되면 무시
        if ancestor_id in SKIP_ANCESTORS:
            continue

        # 폴더명 정리
        folder_name = clean_filename(ancestor_title)
        if folder_name:
            path_parts.append(folder_name)

    # CATCH 루트부터 시작
    result_path = CATCH_DIR
    for part in path_parts:
        result_path = result_path / part

    return result_path


def detect_doc_type(title: str, body: str) -> str:
    """문서 타입 자동 판별"""
    title_lower = title.lower()
    body_lower = body.lower()[:1000]

    if any(kw in title_lower for kw in ['architecture', '아키텍처', '구조']):
        return 'architecture'
    elif any(kw in title_lower for kw in ['integration', '통합', '연동']):
        return 'integration'
    elif any(kw in title_lower for kw in ['api', 'interface', '인터페이스']):
        return 'api'
    elif any(kw in title_lower for kw in ['tutorial', '튜토리얼', '가이드']):
        return 'tutorial'
    elif any(kw in title_lower for kw in ['weekly', 'biweekly', '회의']):
        return 'meeting'
    else:
        return 'tech-article'


def create_properties_frontmatter(page_data: Dict, relative_path: Path) -> str:
    """Properties Frontmatter 생성"""
    page_id = page_data.get('id', '')
    title = page_data.get('title', 'Untitled')
    version_data = page_data.get('version', {})
    last_updated = version_data.get('when', '')
    body = page_data.get('body', {}).get('storage', {}).get('value', '')

    doc_type = detect_doc_type(title, body)
    date_str = datetime.now().strftime('%Y-%m-%d')

    props = f"""---
title: "{title}"
project: CATCH
doc_type: {doc_type}
status: active
priority: medium
source: realtime-marketing-platform
confluence_id: "{page_id}"
updated: {date_str}
tags:
  - catch
  - {doc_type}
  - work
---

"""
    return props


def build_parent_link(ancestors: List[Dict], mapping: Dict) -> Optional[str]:
    """ancestors에서 직접 부모의 Obsidian 링크 생성

    Returns:
        [[부모-경로]] 또는 None
    """
    # ancestors는 루트부터 → 마지막이 직접 부모
    for ancestor in reversed(ancestors):
        ancestor_id = ancestor.get('id', '')

        # SKIP_ANCESTORS는 제외
        if ancestor_id in SKIP_ANCESTORS:
            continue

        # 매핑에서 부모 경로 찾기
        if ancestor_id in mapping.get('CATCH', {}):
            parent_path = mapping['CATCH'][ancestor_id]
            # .md 제거
            parent_path_no_ext = str(parent_path).replace('.md', '')
            return f"[[{parent_path_no_ext}]]"

    return None


def process_page(json_file: Path, mapping: Dict, stats: Dict,
                 converter: ConfluenceConverter = None,
                 attachment_downloader: AttachmentDownloader = None) -> Optional[Dict]:
    """페이지 처리 (생성 또는 업데이트)

    Args:
        json_file: JSON 파일 경로
        mapping: 매핑 데이터
        stats: 통계 정보
        converter: Confluence → Markdown 변환기
        attachment_downloader: 첨부파일 다운로더
    """

    # JSON 파일 읽기
    with open(json_file, 'r', encoding='utf-8') as f:
        page_data = json.load(f)

    page_id = page_data.get('id', '')
    title = page_data.get('title', 'Untitled')
    ancestors = page_data.get('ancestors', [])
    version_data = page_data.get('version', {})
    last_updated = version_data.get('when', '')
    body_storage = page_data.get('body', {}).get('storage', {}).get('value', '')

    if not page_id:
        print(f"  ⚠️  Skip: No page ID in {json_file.name}")
        return None

    # 계층 구조 경로 생성
    parent_dir = build_hierarchy_path(ancestors)
    parent_dir.mkdir(parents=True, exist_ok=True)

    # 파일명 생성
    clean_title = clean_filename(title)
    filename = f"{clean_title}.md"
    file_path = parent_dir / filename

    # 상대 경로 (WORK_DIR 기준)
    relative_path = file_path.relative_to(WORK_DIR)

    # 기존 매핑 확인
    existing_path = mapping.get('CATCH', {}).get(page_id)

    # 내용 생성
    frontmatter = create_properties_frontmatter(page_data, relative_path)

    confluence_url = f"https://confluence.tde.sktelecom.com/pages/viewpage.action?pageId={page_id}"

    # 부모 링크 생성
    parent_link = build_parent_link(ancestors, mapping)
    parent_section = ""
    if parent_link:
        parent_section = f"\n> 📁 **Parent**: {parent_link}\n"

    # 첨부파일 다운로드 (이미지 + 다이어그램)
    attachment_dir = parent_dir / f"attachments_{clean_title}"
    attachments_downloaded = 0
    if attachment_downloader:
        try:
            downloaded = attachment_downloader.download_page_attachments(page_id, attachment_dir)
            attachments_downloaded = len(downloaded)
            if attachments_downloaded > 0:
                stats['attachments_downloaded'] = stats.get('attachments_downloaded', 0) + attachments_downloaded

                # 이미지를 Obsidian 링크로 변환 (Markdown 변환 전)
                body_storage = attachment_downloader.replace_images_with_obsidian_links(
                    body_storage, page_id, attachment_dir, WORK_DIR
                )
        except Exception as e:
            print(f"  ⚠️  Attachment download failed for {title}: {e}")

    # Confluence Storage Format → Markdown + Obsidian 링크 변환
    if converter:
        body_markdown = converter.convert_to_markdown(body_storage)
        links_count = body_markdown.count('[[')

        # Markdown 이미지 링크를 Obsidian 형식으로 변환
        # ![alt](path) → ![[path]]
        if attachments_downloaded > 0:
            # \( \) escape 제거
            body_markdown = body_markdown.replace(r'\(', '(').replace(r'\)', ')')

            # 이미지 링크만 변환 (attachments_로 시작하는 경로)
            # 경로에 괄호가 있을 수 있으므로 정확한 매칭 필요
            body_markdown = re.sub(
                r'!\[([^\]]*)\]\((\attachments_.+?\.(?:png|jpg|jpeg|gif|svg|bmp))\)',
                r'![[\2]]',
                body_markdown,
                flags=re.IGNORECASE
            )
    else:
        body_markdown = body_storage
        links_count = 0

    # 다이어그램 파일 목록 (Draw.io, Gliffy 등)
    diagram_files_section = ""
    if attachments_downloaded > 0 and attachment_dir.exists():
        diagram_files = []
        for f in attachment_dir.iterdir():
            if f.is_file() and not f.name.startswith('.') and not f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.bmp']:
                diagram_files.append(f.name)

        if diagram_files:
            diagram_files_section = "\n## 📊 Diagrams\n"
            for df in sorted(diagram_files):
                diagram_files_section += f"- [[{attachment_dir.name}/{df}]]\n"

    content = f"""{frontmatter}
---
id: {page_id}
title: {title}
last_updated: {last_updated}
source: {confluence_url}
---
{parent_section}
# {title}

{body_markdown}

---
*Source: Confluence Page ID {page_id}*
*Last Updated: {last_updated}*

{diagram_files_section}
---

## Related Notes
- [[02_Work/Projects/CATCH/README|CATCH Overview]]

## Code Repository
- [catch-stream-common](file:///Users/1112007/IdeaProjects/catch-stream-common)
"""

    # 기존 파일 확인
    if existing_path:
        existing_full_path = WORK_DIR / existing_path

        # 경로가 변경되었는지 확인
        if existing_full_path != file_path:
            # 경로 변경: 기존 파일 삭제 후 새 위치에 생성
            if existing_full_path.exists():
                existing_full_path.unlink()
                print(f"  🔄 Move: {existing_path} → {relative_path}")

        # 파일 존재 여부 확인
        if file_path.exists():
            # 타임스탬프 비교
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            existing_ts_match = re.search(r'last_updated:\s*([^\n]+)', existing_content)
            new_ts = last_updated

            if existing_ts_match and existing_ts_match.group(1).strip() == new_ts.strip():
                # 변경 없음
                stats['skipped'] += 1
                return None

        # 업데이트
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  🔄 Update: {relative_path}")
        stats['updated'] += 1
    else:
        # 새로 생성
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✨ New: {relative_path}")
        stats['created'] += 1

    # 매핑 업데이트
    if 'CATCH' not in mapping:
        mapping['CATCH'] = {}
    mapping['CATCH'][page_id] = str(relative_path)

    return {
        'page_id': page_id,
        'title': title,
        'path': str(relative_path),
        'links_count': links_count
    }


def main(disable_delete_detection=False):
    """메인 함수

    Args:
        disable_delete_detection: True일 경우 삭제 감지 비활성화 (증분 동기화용)
    """
    print("=" * 60)
    print("  📝 Obsidian 변환 v7 (이미지 다운로드 + 링크 변환)")
    print("=" * 60)
    print()

    # 소스 디렉토리 확인
    if not SOURCE_DIR.exists():
        print(f"❌ 소스 디렉토리 없음: {SOURCE_DIR}")
        print(f"   sync-confluence-full.sh를 먼저 실행하세요.")
        return

    # JSON 파일 목록
    json_files = list(SOURCE_DIR.glob('*.json'))

    if not json_files:
        print(f"❌ JSON 파일 없음: {SOURCE_DIR}")
        return

    print(f"📂 소스: {SOURCE_DIR}")
    print(f"📄 파일 수: {len(json_files)}개")
    print()

    # 매핑 로드
    mapping = load_mapping()

    # Confluence → Obsidian 변환기 초기화
    converter = ConfluenceConverter(mapping)

    # 첨부파일 다운로더 초기화
    config = load_confluence_config()
    attachment_downloader = AttachmentDownloader(
        config['CONFLUENCE_URL'],
        config['CONFLUENCE_TOKEN']
    )

    # 1단계: 전체 프로젝트(CATCH, Common, CAMA)의 제목 → 경로 매핑 구축
    print("🔗 전체 프로젝트 제목 매핑 구축 중...")
    converter.build_full_title_mapping(TEMP_DIR)
    print(f"   ✅ {len(converter.title_to_path)} 페이지 매핑 완료 (교차 링크 지원)")
    print()

    # 통계
    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'deleted': 0,
        'links_converted': 0
    }

    # 현재 동기화된 Page ID 목록 수집
    synced_page_ids = {json_file.stem for json_file in json_files}

    # 2단계: 각 페이지 처리 (링크 변환 포함)
    for json_file in json_files:
        result = process_page(json_file, mapping, stats, converter, attachment_downloader)
        if result and result.get('links_count', 0) > 0:
            stats['links_converted'] += result['links_count']

    # 삭제된 페이지 감지 및 정리 (전체 동기화만)
    if not disable_delete_detection and 'CATCH' in mapping:
        orphaned_ids = []
        for page_id, relative_path in mapping['CATCH'].items():
            if page_id not in synced_page_ids:
                # Confluence에서 삭제된 페이지
                orphaned_file = WORK_DIR / relative_path
                if orphaned_file.exists():
                    orphaned_file.unlink()
                    print(f"  🗑️  Delete: {relative_path} (Page ID {page_id} removed from Confluence)")
                    stats['deleted'] += 1
                orphaned_ids.append(page_id)

        # 매핑에서 제거
        for page_id in orphaned_ids:
            del mapping['CATCH'][page_id]
    elif disable_delete_detection:
        print("  ℹ️  삭제 감지 비활성화 (증분 동기화 모드)")
        print()

    # 매핑 저장
    save_mapping(mapping)

    print()
    print("=" * 60)
    print("  ✅ 변환 완료")
    print("=" * 60)
    print()
    print(f"📊 통계:")
    print(f"  - 새로 생성: {stats['created']}개")
    print(f"  - 업데이트: {stats['updated']}개")
    print(f"  - 건너뜀: {stats['skipped']}개")
    print(f"  - 삭제됨: {stats['deleted']}개")
    print(f"  - 🔗 링크 변환: {stats['links_converted']}개")
    if stats.get('attachments_downloaded', 0) > 0:
        print(f"  - 📎 첨부파일 다운로드: {stats['attachments_downloaded']}개 (이미지 + 다이어그램)")
    print()
    print(f"📂 위치: {CATCH_DIR}")
    print()


if __name__ == '__main__':
    import sys
    # 커맨드 라인 인자로 --no-delete 전달 가능
    disable_delete = '--no-delete' in sys.argv
    main(disable_delete_detection=disable_delete)
