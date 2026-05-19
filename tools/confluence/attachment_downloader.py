#!/usr/bin/env python3
"""
Confluence 첨부파일 다운로드 유틸리티
이미지 파일을 Obsidian Vault에 저장
"""

import requests
from pathlib import Path
from typing import List, Dict, Optional
import json


class AttachmentDownloader:
    """Confluence 첨부파일 다운로드"""

    def __init__(self, confluence_url: str, token: str):
        self.confluence_url = confluence_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

    def get_attachments(self, page_id: str) -> List[Dict]:
        """페이지의 첨부파일 목록 조회

        Args:
            page_id: Confluence 페이지 ID

        Returns:
            첨부파일 정보 리스트
        """
        url = f"{self.confluence_url}/rest/api/content/{page_id}/child/attachment"
        params = {
            'limit': 100,  # 최대 100개
            'expand': 'metadata'  # MIME type 정보 포함
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            print(f"  ⚠️  Failed to get attachments for page {page_id}: {e}")
            return []

    def is_downloadable_file(self, filename: str, media_type: str = '') -> bool:
        """다운로드할 파일 여부 확인 (이미지 + 다이어그램)"""
        # 확장자 기반
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.drawio.png', '.bmp', '.drawio', '.mxfile']
        filename_lower = filename.lower()

        for ext in image_extensions:
            if filename_lower.endswith(ext):
                return True

        # MIME type 기반 (Gliffy, Draw.io)
        diagram_types = [
            'application/vnd.jgraph.mxfile',  # Draw.io
            'application/gliffy+json',         # Gliffy
            'application/x-drawio',            # Draw.io
        ]

        if media_type in diagram_types:
            return True

        # .tmp 파일은 제외
        if '.tmp' in filename_lower:
            return False

        return False

    def download_attachment(self, attachment: Dict, target_dir: Path) -> Optional[Path]:
        """첨부파일 다운로드

        Args:
            attachment: 첨부파일 정보 (Confluence API 응응)
            target_dir: 저장 디렉토리

        Returns:
            저장된 파일 경로 또는 None
        """
        attachment_id = attachment.get('id', '')
        title = attachment.get('title', '')
        version = attachment.get('version', {}).get('number', 1)
        media_type = attachment.get('metadata', {}).get('mediaType', '')

        if not self.is_downloadable_file(title, media_type):
            return None

        # 다운로드 URL
        download_url = self.confluence_url + attachment.get('_links', {}).get('download', '')
        if not download_url or download_url == self.confluence_url:
            return None

        # 저장 경로
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / title

        # 이미 존재하는 경우 버전 확인
        version_file = target_dir / f".{title}.version"
        if file_path.exists() and version_file.exists():
            try:
                existing_version = int(version_file.read_text().strip())
                if existing_version >= version:
                    # 최신 버전이면 스킵
                    return file_path
            except:
                pass

        # 다운로드
        try:
            response = requests.get(download_url, headers=self.headers, timeout=60)
            response.raise_for_status()

            # 저장
            file_path.write_bytes(response.content)

            # 버전 정보 저장
            version_file.write_text(str(version))

            return file_path
        except Exception as e:
            print(f"  ⚠️  Failed to download {title}: {e}")
            return None

    def download_page_attachments(self, page_id: str, target_dir: Path) -> List[Path]:
        """페이지의 모든 이미지 첨부파일 다운로드

        Args:
            page_id: Confluence 페이지 ID
            target_dir: 저장 디렉토리

        Returns:
            다운로드된 파일 경로 리스트
        """
        attachments = self.get_attachments(page_id)
        downloaded_files = []

        for attachment in attachments:
            file_path = self.download_attachment(attachment, target_dir)
            if file_path:
                downloaded_files.append(file_path)

        return downloaded_files

    def replace_images_with_obsidian_links(self, body_storage: str, page_id: str,
                                           attachment_dir: Path, work_dir: Path) -> str:
        """Confluence Storage Format의 이미지를 Obsidian 링크로 변환

        HTML → Markdown 변환 전에 호출해야 함

        Args:
            body_storage: Confluence Storage Format (HTML-like XML)
            page_id: 페이지 ID
            attachment_dir: 첨부파일 디렉토리 (절대 경로)
            work_dir: WORK_DIR (02_Work)

        Returns:
            이미지가 Obsidian 링크로 변환된 텍스트
        """
        import re

        # Confluence <ac:image> 태그 찾기
        # 예: <ac:image><ri:attachment ri:filename="diagram.png" /></ac:image>
        image_pattern = re.compile(
            r'<ac:image[^>]*>.*?<ri:attachment ri:filename="([^"]+)".*?</ac:image>',
            re.DOTALL
        )

        def replace_image(match):
            filename = match.group(1)
            image_path = attachment_dir / filename

            if image_path.exists():
                # Markdown 파일과 같은 폴더의 .attachments_XXX에 있으므로 상대 경로 사용
                attachment_folder_name = attachment_dir.name
                relative_path = f"{attachment_folder_name}/{filename}"
                # HTML 형식으로 삽입 (html2text가 처리할 수 있도록)
                return f'<p><img src="{relative_path}" alt="{filename}" /></p>'
            else:
                # 파일이 없으면 제거 (빈 문자열)
                return ''

        return image_pattern.sub(replace_image, body_storage)
