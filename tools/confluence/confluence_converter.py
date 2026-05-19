#!/usr/bin/env python3
"""
Confluence Storage Format → Markdown 변환 + Obsidian 링크 생성
"""

import re
import html
from typing import Dict, Optional, List, Tuple
from bs4 import BeautifulSoup
import html2text


class ConfluenceConverter:
    """Confluence Storage Format을 Obsidian Markdown으로 변환"""

    def __init__(self, mapping: Dict):
        """
        Args:
            mapping: .confluence-mapping.json 데이터
                     {'CATCH': {'page_id': 'relative/path.md'}, 'Common': {...}}
        """
        self.mapping = mapping
        self.html_converter = html2text.HTML2Text()
        self.html_converter.body_width = 0  # 줄바꿈 방지
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False

        # Page ID → 파일 경로 매핑
        self.id_to_path = {}
        for section in ['CATCH', 'Common', 'CAMA']:
            if section in mapping:
                self.id_to_path.update(mapping[section])

        # Page Title → 파일 경로 역매핑 (나중에 구축)
        self.title_to_path = {}

    def add_title_mapping(self, page_id: str, title: str, path: str):
        """페이지 제목 → 경로 매핑 추가"""
        clean_title = title.strip().lower()
        self.title_to_path[clean_title] = path

    def build_full_title_mapping(self, temp_dir):
        """모든 프로젝트(CATCH, Common, CAMA)의 제목 매핑 구축

        Args:
            temp_dir: .temp 디렉토리 경로 (pathlib.Path)
        """
        from pathlib import Path
        import json

        sections = [
            ('CATCH', 'catch-full'),
            ('Common', 'common-full'),
            ('CAMA', 'cama-full'),
        ]

        for section_name, folder_name in sections:
            section_dir = temp_dir / folder_name
            if not section_dir.exists():
                continue

            json_files = list(section_dir.glob('*.json'))
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        page_data = json.load(f)

                    page_id = page_data.get('id', '')
                    title = page_data.get('title', '')

                    if page_id in self.mapping.get(section_name, {}):
                        path = self.mapping[section_name][page_id]
                        self.add_title_mapping(page_id, title, path)
                except Exception:
                    continue

    def extract_confluence_links(self, body_storage: str) -> List[Tuple[str, str, str]]:
        """Confluence Storage Format에서 내부 링크 추출 (정규표현식 사용)

        Returns:
            List[(원본_HTML, page_title, link_text)]
        """
        import re
        links = []

        # <ac:link>...</ac:link> 전체를 찾기 (정규표현식)
        link_pattern = re.compile(r'<ac:link>(.*?)</ac:link>', re.DOTALL)

        for match in link_pattern.finditer(body_storage):
            original_html = match.group(0)  # 전체 <ac:link>...</ac:link>
            inner_html = match.group(1)     # 내부 내용

            # ri:content-title 추출
            title_match = re.search(r'ri:content-title="([^"]+)"', inner_html)
            if title_match:
                page_title = title_match.group(1)

                # link_body 추출 (있으면)
                body_match = re.search(r'<ac:link-body>(.*?)</ac:link-body>', inner_html, re.DOTALL)
                link_text = body_match.group(1) if body_match else page_title

                links.append((original_html, page_title, link_text))

        return links

    def confluence_link_to_obsidian(self, page_title: str, link_text: str) -> str:
        """Confluence 페이지 제목 → Obsidian [[링크]]

        Args:
            page_title: Confluence 페이지 제목
            link_text: 표시할 텍스트

        Returns:
            [[파일경로|표시텍스트]] 또는 원본
        """
        clean_title = page_title.strip().lower()

        # 제목으로 파일 찾기
        if clean_title in self.title_to_path:
            target_path = self.title_to_path[clean_title]
            # 확장자 제거
            target_path = target_path.replace('.md', '')

            if link_text and link_text != page_title:
                return f"[[{target_path}|{link_text}]]"
            else:
                return f"[[{target_path}]]"

        # 못 찾으면 제목만 표시
        return f"**{link_text or page_title}**"

    def convert_to_markdown(self, body_storage: str) -> str:
        """Confluence Storage Format → Markdown + Obsidian 링크 변환

        Args:
            body_storage: Confluence Storage Format (HTML-like XML)

        Returns:
            Markdown 텍스트 with [[Obsidian Links]]
        """
        if not body_storage:
            return ""

        # 1. Confluence 내부 링크 추출
        confluence_links = self.extract_confluence_links(body_storage)

        # 2. Confluence 링크를 임시 플레이스홀더로 교체
        text = body_storage
        link_map = {}  # placeholder → obsidian_link

        for idx, (original_html, page_title, link_text) in enumerate(confluence_links):
            placeholder = f"___CONFLUENCE_LINK_{idx}___"
            obsidian_link = self.confluence_link_to_obsidian(page_title, link_text)
            link_map[placeholder] = obsidian_link
            text = text.replace(original_html, placeholder)

        # 3. Confluence 매크로 정리 (코드 블록 등)
        text = self._clean_confluence_macros(text)

        # 4. HTML → Markdown 변환
        try:
            markdown = self.html_converter.handle(text)
        except Exception as e:
            # 변환 실패 시 기본 정리
            markdown = self._basic_html_clean(text)

        # 5. 플레이스홀더를 Obsidian 링크로 복원
        for placeholder, obsidian_link in link_map.items():
            markdown = markdown.replace(placeholder, obsidian_link)

        # 6. 최종 정리
        markdown = self._post_process_markdown(markdown)

        return markdown

    def _clean_confluence_macros(self, text: str) -> str:
        """Confluence 매크로 태그 정리"""
        soup = BeautifulSoup(text, 'lxml')

        # 코드 블록 변환
        for code_macro in soup.find_all('ac:structured-macro', {'ac:name': 'code'}):
            language = 'text'
            for param in code_macro.find_all('ac:parameter'):
                if param.get('ac:name') == 'language':
                    language = param.get_text()

            code_body = code_macro.find('ac:plain-text-body')
            if code_body:
                code_text = code_body.get_text()
                code_block = f'\n```{language}\n{code_text}\n```\n'
                code_macro.replace_with(BeautifulSoup(code_block, 'html.parser'))

        # 기타 매크로는 제거 (gliffy, info 등)
        for macro in soup.find_all('ac:structured-macro'):
            macro.decompose()

        return str(soup)

    def _basic_html_clean(self, text: str) -> str:
        """기본 HTML 정리 (html2text 실패 시)"""
        # HTML 엔티티 디코딩
        text = html.unescape(text)

        # 기본 태그 제거
        text = re.sub(r'<[^>]+>', '', text)

        # 연속 공백 정리
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

        return text.strip()

    def _post_process_markdown(self, markdown: str) -> str:
        """Markdown 후처리"""
        # 연속 빈 줄 정리
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # CDATA 잔여물 제거
        markdown = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', markdown, flags=re.DOTALL)

        # XML 선언 제거
        markdown = re.sub(r'<\?xml[^>]*\?>', '', markdown)

        return markdown.strip()
