# Release 문서 목차

> jmAgent v1.0.0 GitHub Release 게시를 위한 모든 가이드 및 참고 자료

---

## 빠른 선택 가이드

### 지금 바로 Release를 게시하고 싶어요
👉 **[빠른 참조 가이드](./GITHUB_RELEASE_QUICK_REFERENCE.md)** (5-10분)

### 단계를 상세히 알고 싶어요
👉 **[완전 가이드](./GITHUB_RELEASE_GUIDE.md)** (15-20분, 초보자용)

### Release 내용을 미리 보고 싶어요
👉 **[Release 전체 내용](../GITHUB_RELEASE_v1.0.0.md)** (Release description)

### 일반 Release 정보
👉 **[Release Notes](../RELEASE_NOTES.md)** (v1.0.0 주요 사항)

---

## 모든 Release 관련 문서

### 게시 가이드 (Step by Step)

| 문서 | 설명 | 소요시간 | 대상 |
|------|------|--------|------|
| [GITHUB_RELEASE_QUICK_REFERENCE.md](./GITHUB_RELEASE_QUICK_REFERENCE.md) | 빠른 명령어 체크리스트 | 5-10분 | 경험자 |
| [GITHUB_RELEASE_GUIDE.md](./GITHUB_RELEASE_GUIDE.md) | 완전한 단계별 가이드 | 15-20분 | 초보자 |
| [RELEASES_README.md](../RELEASES_README.md) | Release 디렉토리 설명 | 3분 | 모두 |

### Release 내용 문서

| 문서 | 설명 | 사용처 |
|------|------|--------|
| [GITHUB_RELEASE_v1.0.0.md](../GITHUB_RELEASE_v1.0.0.md) | GitHub에 붙여넣을 전체 Release 내용 | Release description |
| [RELEASE_NOTES.md](../RELEASE_NOTES.md) | v1.0.0 주요 기능 및 변경사항 | 문서 참고 |
| [RELEASE_TEMPLATE.md](../RELEASE_TEMPLATE.md) | Release 작성 템플릿 (재사용) | 미래 Release |
| [RELEASE_GUIDELINES.md](../RELEASE_GUIDELINES.md) | Release 작성 및 관리 가이드 | 정책 참조 |

### 설치 및 사용

| 문서 | 설명 |
|------|------|
| [../README.md](../README.md) | 프로젝트 개요 및 빠른 시작 |
| [QUICKSTART.md](./QUICKSTART.md) | 자세한 설치 및 사용 가이드 |
| [../DEPLOYMENT.md](../DEPLOYMENT.md) | 배포 및 설정 상세 가이드 |

### 참고 자료

| 문서 | 설명 |
|------|------|
| [../CLAUDE.md](../CLAUDE.md) | 개발자 가이드 및 아키텍처 |
| [../CONTRIBUTING.md](../CONTRIBUTING.md) | 기여 가이드 |
| [PHASE4_FEATURES.md](./PHASE4_FEATURES.md) | Phase 4 Enterprise 기능 상세 |
| [PHASE3_FEATURES.md](./PHASE3_FEATURES.md) | Phase 3 고급 기능 상세 |

---

## 게시 프로세스 요약

### 1단계: 준비 (2분)
- Git 설정 확인
- GitHub 계정 로그인
- 로컬 저장소 상태 확인

### 2단계: 로컬 커밋 (1분)
```bash
git add .
git commit -m "Prepare v1.0.0 for release"
```

### 3단계: 태그 생성 (1분)
```bash
git tag -a v1.0.0 -m "jmAgent v1.0.0 - Production Ready Release"
```

### 4단계: Push (2분)
```bash
git push origin main
git push origin v1.0.0
```

### 5단계: GitHub Release 생성 (5분)
- GitHub 웹사이트 → Releases → Create new release
- Tag 선택: v1.0.0
- Title 입력: `jmAgent v1.0.0 - Production Ready`
- Description 입력: [GITHUB_RELEASE_v1.0.0.md](../GITHUB_RELEASE_v1.0.0.md) 내용 복사
- Publish release 클릭

### 6단계: 검증 (3분)
- Release 페이지 확인
- 링크 작동 확인
- Tag 페이지 확인

**총 소요시간: 10-15분**

---

## 가이드 선택 기준

### 초보자 (GitHub, Git 경험 부족)
1. [GITHUB_RELEASE_GUIDE.md](./GITHUB_RELEASE_GUIDE.md) 읽기
2. 각 단계를 차례로 따라하기
3. 문제 해결 섹션 참고

### 경험자 (Git, GitHub 경험 많음)
1. [GITHUB_RELEASE_QUICK_REFERENCE.md](./GITHUB_RELEASE_QUICK_REFERENCE.md) 참고
2. "한 번에 따라하기" 섹션의 명령어 실행
3. 필요시 [GITHUB_RELEASE_GUIDE.md](./GITHUB_RELEASE_GUIDE.md) 참조

### CLI 선호자 (GitHub CLI 사용)
1. GitHub CLI 설치: `brew install gh`
2. GitHub 로그인: `gh auth login`
3. Release 생성: `gh release create v1.0.0 --title "..."`

### 웹 UI 선호자 (브라우저 사용)
1. [GITHUB_RELEASE_GUIDE.md](./GITHUB_RELEASE_GUIDE.md) 의 "단계 4" 참고
2. GitHub 웹사이트 → Releases 메뉴
3. "Create a new release" 클릭

---

## 자주 묻는 질문 (FAQ)

### Q: Release와 Tag의 차이는?
**A**: 
- **Tag**: Git 개념, 특정 커밋을 표시
- **Release**: GitHub 개념, Tag를 기반으로 Release 노트, 링크, 다운로드 제공

### Q: 실수로 Tag를 생성했다면?
**A**: 
```bash
git tag -d v1.0.0         # 로컬 삭제
git push origin :v1.0.0   # 원격 삭제
```

### Q: 이미 Push한 Release를 수정할 수 있나?
**A**: 네, GitHub 웹사이트에서 Release를 수정할 수 있습니다. 
- Release 페이지 → 연필 아이콘 → 수정 → Save

### Q: Release Description을 마크다운으로 작성할 수 있나?
**A**: 네! GitHub는 마크다운을 완벽히 지원합니다.

### Q: 여러 파일을 Release에 첨부하려면?
**A**: Release 수정 페이지에서 파일 드래그 또는 선택으로 업로드 가능

### Q: Release를 삭제하려면?
**A**: GitHub 웹사이트의 Release 페이지에서 "Delete" 버튼 클릭

### Q: Pre-release는 언제 사용하나?
**A**: 베타, 알파, RC 버전 등 정식 릴리스 전 테스트 버전에 사용

### Q: "Latest release" 배지를 변경할 수 있나?
**A**: 네, Release 편집 페이지에서 "Set as latest release" 체크박스로 변경

---

## 유용한 명령어 모음

### 로컬 확인
```bash
# 모든 태그 보기
git tag -l

# 특정 태그 상세 정보
git show v1.0.0

# 최근 태그 확인
git describe --tags

# 커밋 로그로 태그 찾기
git log --all --graph --decorate
```

### Push 작업
```bash
# 모든 태그 푸시
git push origin --tags

# 특정 태그만 푸시
git push origin v1.0.0

# 모든 브랜치와 태그 푸시
git push origin --all --tags
```

### GitHub CLI
```bash
# 설치
brew install gh

# 로그인
gh auth login

# Release 생성
gh release create v1.0.0 --title "Title" --notes "Notes"

# Release 수정
gh release edit v1.0.0 --notes-file GITHUB_RELEASE_v1.0.0.md

# Release 조회
gh release view v1.0.0

# 모든 Release 나열
gh release list
```

---

## 체크리스트 다운로드

### Release 체크리스트
```
Release Checklist for jmAgent v1.0.0
====================================

Pre-Release
  [ ] Git 설정 확인
  [ ] GitHub 계정 로그인
  [ ] 로컬 저장소 clean
  [ ] 원격 리포지토리 연결 확인

Local Operations
  [ ] 모든 변경사항 커밋
  [ ] 태그 생성
  [ ] 로컬에서 태그 확인

Push
  [ ] main 브랜치 push
  [ ] v1.0.0 태그 push
  [ ] GitHub에서 tag 확인

GitHub Release
  [ ] Tag 선택
  [ ] Title 입력
  [ ] Description 작성
  [ ] 옵션 설정 (pre-release, latest)
  [ ] Publish release

Post-Release
  [ ] Release 페이지 확인
  [ ] 링크 작동 확인
  [ ] Tag 페이지 확인
  [ ] 설명 정확성 확인
```

---

## 다음 단계

Release 게시 후:

1. **소셜 미디어 공지**
   - Twitter/X
   - LinkedIn
   - GitHub Discussions

2. **사용자 피드백 수집**
   - GitHub Issues 모니터
   - GitHub Discussions 활성화

3. **다음 버전 계획**
   - Phase 5 계획
   - Community feedback 반영

4. **Documentation 업데이트**
   - Release History 작성
   - 이전 버전 아카이빙

---

## 추가 도움말

### GitHub 공식 문서
- [Release 관리](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [Git Tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [GitHub CLI](https://cli.github.com/)

### jmAgent 문서
- [README](../README.md) - 프로젝트 개요
- [DEPLOYMENT](../DEPLOYMENT.md) - 설치 가이드
- [CONTRIBUTING](../CONTRIBUTING.md) - 기여 가이드

### 커뮤니티
- [GitHub Issues](https://github.com/yourusername/jmAgent/issues)
- [GitHub Discussions](https://github.com/yourusername/jmAgent/discussions)

---

## 피드백 및 개선

이 가이드에 개선 제안이 있으신가요?

- GitHub Issues에서 제안하기
- Pull Request로 개선 제시하기
- Discussions에서 의견 나누기

---

**마지막 수정**: April 2026  
**버전**: 1.0.0  
**상태**: Production Ready  
**총 문서 수**: 7개  
**총 단계**: 6단계  
**예상 소요시간**: 10-15분

🚀 **Ready to release jmAgent v1.0.0!**
