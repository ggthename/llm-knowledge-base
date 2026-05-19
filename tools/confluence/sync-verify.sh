#!/bin/bash
#
# Confluence 동기화 검증 스크립트
# - 문서 수 검증
# - 깨진 링크 검사
# - 필수 파일 존재 확인
# - 매핑 파일 일관성 체크
#

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 스크립트 디렉토리
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 설정 로드
source "$PROJECT_ROOT/.confluence-config"

OBSIDIAN_ROOT="$OBSIDIAN_VAULT/02_Work/Projects"
MAPPING_FILE="$OBSIDIAN_VAULT/02_Work/.confluence-mapping.json"

# 결과 카운터
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

echo "============================================================"
echo "  🔍 Confluence Sync Verification"
echo "============================================================"
echo ""

# 검증 함수
verify_check() {
    local check_name="$1"
    local result="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $check_name"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $check_name"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# 1. 매핑 파일 존재 확인
echo -e "${BLUE}📋 Check 1: Mapping File Exists${NC}"
if [ -f "$MAPPING_FILE" ]; then
    verify_check "Mapping file exists" "PASS"
else
    verify_check "Mapping file exists" "FAIL"
    echo "  Error: $MAPPING_FILE not found"
fi
echo ""

# 2. Space별 문서 수 검증
echo -e "${BLUE}📊 Check 2: Document Count Verification${NC}"

for space in CATCH Common CAMA OFFERING; do
    space_dir="$OBSIDIAN_ROOT/$space"

    if [ ! -d "$space_dir" ]; then
        echo -e "  ${YELLOW}⚠️  SKIP${NC}: $space directory not found"
        continue
    fi

    # 실제 파일 수 (README 제외)
    actual_count=$(find "$space_dir" -name "*.md" -type f ! -name "README.md" | wc -l | tr -d ' ')

    # 매핑 파일의 문서 수
    if [ -f "$MAPPING_FILE" ]; then
        mapped_count=$(jq -r ".$space | length // 0" "$MAPPING_FILE" 2>/dev/null || echo "0")
    else
        mapped_count=0
    fi

    # Allow ±1 difference (README가 생성되면서 차이 발생 가능)
    diff=$((actual_count - mapped_count))
    if [ $diff -lt 0 ]; then
        diff=$((-diff))
    fi

    echo "  $space: actual=$actual_count, mapped=$mapped_count (diff=$diff)"

    if [ $diff -le 1 ]; then
        verify_check "$space document count matches" "PASS"
    else
        verify_check "$space document count matches" "FAIL"
        echo -e "    ${RED}Mismatch: $actual_count files vs $mapped_count in mapping${NC}"
    fi
done
echo ""

# 3. README 파일 존재 확인
echo -e "${BLUE}📝 Check 3: README Files Exist${NC}"

for space in CATCH Common CAMA OFFERING; do
    space_dir="$OBSIDIAN_ROOT/$space"

    # Space 디렉토리가 없으면 스킵
    if [ ! -d "$space_dir" ]; then
        echo -e "  ${YELLOW}⚠️  SKIP${NC}: $space directory not found"
        continue
    fi

    readme_file="$space_dir/README.md"

    if [ -f "$readme_file" ]; then
        verify_check "$space README.md exists" "PASS"

        # README 내용 검증 (Statistics 섹션 있는지)
        if grep -q "## Statistics" "$readme_file"; then
            verify_check "$space README has Statistics section" "PASS"
        else
            verify_check "$space README has Statistics section" "FAIL"
        fi
    else
        echo -e "  ${YELLOW}⚠️  WARN${NC}: $space README.md missing (run sync to generate)"
    fi
done
echo ""

# 4. 깨진 링크 검사 (문서 링크만, 이미지는 제외)
echo -e "${BLUE}🔗 Check 4: Broken Document Wikilinks${NC}"

broken_links_found=0

for space in CATCH Common CAMA OFFERING; do
    space_dir="$OBSIDIAN_ROOT/$space"

    if [ ! -d "$space_dir" ]; then
        continue
    fi

    # [[링크]] 형태 찾기 (attachments_로 시작하지 않는 것만)
    while IFS= read -r file; do
        # 파일에서 [[링크]] 추출 (이미지는 ![[...]]이므로 제외)
        grep -o '\[\[.*\]\]' "$file" 2>/dev/null | grep -v '!\[\[' | while read -r link; do
            # [[path]] 또는 [[path|alias]] 형태 처리
            link_path=$(echo "$link" | sed 's/\[\[\(.*\)\]\]/\1/' | sed 's/|.*//')

            # 이미지 링크 스킵 (attachments_ 또는 이미지 확장자)
            if [[ "$link_path" == attachments_* ]] || [[ "$link_path" == *.png ]] || [[ "$link_path" == *.jpg ]] || [[ "$link_path" == *.jpeg ]]; then
                continue
            fi

            # 절대 경로 변환
            if [[ "$link_path" == 02_Work/* ]]; then
                target_file="$OBSIDIAN_VAULT/$link_path.md"
            elif [[ "$link_path" == Projects/* ]]; then
                target_file="$OBSIDIAN_VAULT/02_Work/$link_path.md"
            else
                # 상대 경로는 현재 파일 기준
                target_file="$(dirname "$file")/$link_path.md"
            fi

            # 파일 존재 확인
            if [ ! -f "$target_file" ]; then
                if [ $broken_links_found -eq 0 ]; then
                    echo "  Broken document links found:"
                fi
                echo -e "    ${RED}✗${NC} $(basename "$file")"
                echo "      → $link"
                broken_links_found=$((broken_links_found + 1))
            fi
        done
    done < <(find "$space_dir" -name "*.md" -type f)
done

if [ $broken_links_found -eq 0 ]; then
    verify_check "No broken document links" "PASS"
else
    verify_check "No broken document links" "FAIL"
    echo -e "  ${YELLOW}Found $broken_links_found broken document links (images excluded)${NC}"
fi
echo ""

# 5. Orphaned files 검사 (매핑에는 있는데 파일 없음)
echo -e "${BLUE}🗑️  Check 5: Orphaned Mappings${NC}"

orphaned_count=0

if [ -f "$MAPPING_FILE" ]; then
    for space in CATCH Common CAMA OFFERING; do
        # 매핑에 있는 파일들 확인
        jq -r ".$space // {} | to_entries[] | .value" "$MAPPING_FILE" 2>/dev/null | while read -r relative_path; do
            full_path="$OBSIDIAN_VAULT/02_Work/$relative_path"

            if [ ! -f "$full_path" ]; then
                if [ $orphaned_count -eq 0 ]; then
                    echo "  Orphaned mappings (in JSON but file missing):"
                fi
                echo -e "    ${YELLOW}⚠${NC} $relative_path"
                orphaned_count=$((orphaned_count + 1))
            fi
        done
    done
fi

if [ $orphaned_count -eq 0 ]; then
    verify_check "No orphaned mappings" "PASS"
else
    verify_check "No orphaned mappings" "FAIL"
    echo -e "  ${YELLOW}Found $orphaned_count orphaned mappings (run full sync to clean up)${NC}"
fi
echo ""

# 최종 결과
echo "============================================================"
echo "  📊 Verification Summary"
echo "============================================================"
echo ""
echo "  Total Checks: $TOTAL_CHECKS"
echo -e "  ${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "  ${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review.${NC}"
    exit 1
fi
