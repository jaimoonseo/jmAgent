# jmAgent - 개인용 Claude 코딩 어시스턴트

**목표**: AWS Bedrock을 통한 범용 코딩 agent 구축 (프로젝트 독립적)  
**작성일**: 2026-04-02  
**참고**: FeedOPS의 Bedrock 인증/호출 패턴 재활용  

---

## 1. 개요

### 1.1 목표
- 어떤 프로젝트든 빠르게 코드 생성/수정/분석 가능
- FeedOPS 경험을 바탕으로 한 프로덕션급 품질
- 로컬 CLI 도구 (프로젝트 종속성 없음)

### 1.2 주요 기능
| 기능 | 설명 |
|------|------|
| **Code Generation** | 프롬프트 기반 코드 생성 (Python, JS/TS, SQL, Bash 등) |
| **Refactoring** | 기존 코드 정리 및 최적화 |
| **Testing** | 단위 테스트 자동 생성 (pytest, vitest, jest) |
| **Debugging** | 에러 메시지 기반 버그 수정 |
| **Explanation** | 코드 분석 및 한글 설명 |
| **Interactive** | 대화형 모드 (히스토리 유지) |
| **File Context** | 파일 참고하여 코드 생성 |

### 1.3 기술 스택
- **LLM**: AWS Bedrock Claude (Haiku 4.5 기본, Sonnet/Opus 선택 가능)
- **인증**: Bedrock API Key (ABSK) 또는 IAM 자격증명
- **의존성**: boto3, python-dotenv (최소한)
- **Python**: >= 3.10

---

## 2. FeedOPS의 Bedrock 활용 분석

### 2.1 핵심 코드 패턴 (재사용)

**인증 감지 (`bedrock_titan_test.py`):**
```python
def _detect_auth_mode() -> str:
    """API Key(ABSK) vs IAM 자동 감지"""
    bearer = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
    access_key = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
    
    if bearer or (access_key and access_key.upper().startswith("ABSK")):
        return "api_key"
    return "iam"
```

**클라이언트 생성:**
```python
def _build_bedrock_runtime(region: str):
    """인증 방식에 따라 boto3 client 생성"""
    if _detect_auth_mode() == "api_key":
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
        return boto3.client("bedrock-runtime", region_name=region)
    else:
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
```

**모델 호출 (`document_analyzer.py`):**
```python
response = client.invoke_model(
    modelId=model_id,
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-06-01",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": conversation_history
    })
)
```

### 2.2 배운 교훈
✅ API Key 방식이 간단 (한 번만 설정)  
✅ 대화 히스토리 리스트로 관리 가능  
✅ 토큰 수 추정으로 사전 검증 가능  
✅ 프롬프트 캐싱으로 비용 절감  
✅ 스트리밍 가능 (real-time 응답)  

---

## 3. jmAgent 설계

### 3.1 디렉터리 구조
```
~/Documents/jmAgent/
├── PLAN.md                           # 이 파일
├── README.md                         # 사용 가이드
├── .env.example                      # 설정 예시
├── setup.sh                          # 환경 설정 스크립트
│
├── src/
│   ├── __init__.py
│   ├── agent.py                      # 핵심 Agent 클래스
│   ├── cli.py                        # CLI 진입점 (argparse)
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   └── bedrock_auth.py           # FeedOPS 패턴 기반 인증
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py                # 요청 데이터 클래스
│   │   └── response.py               # 응답 데이터 클래스
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── system.py                 # 시스템 프롬프트
│   │   ├── templates.py              # 액션별 프롬프트 템플릿
│   │   └── context_loader.py         # 프로젝트 컨텍스트 로드
│   │
│   ├── actions/
│   │   ├── __init__.py
│   │   ├── base.py                   # 기본 액션 클래스
│   │   ├── generate.py               # 코드 생성
│   │   ├── refactor.py               # 리팩토링
│   │   ├── test.py                   # 테스트 생성
│   │   ├── explain.py                # 코드 설명
│   │   └── fix.py                    # 버그 수정
│   │
│   └── utils/
│       ├── __init__.py
│       ├── token_counter.py          # 토큰 수 추정
│       ├── code_formatter.py         # 코드 정리
│       ├── file_handler.py           # 파일 읽기/쓰기
│       └── logger.py                 # 로깅
│
├── tests/
│   ├── test_auth.py
│   ├── test_agent.py
│   └── test_prompts.py
│
└── examples/
    ├── generate_api.py               # FastAPI 엔드포인트 예시
    ├── refactor_react.tsx             # React 리팩토링 예시
    └── test_utils.py                 # 테스트 생성 예시
```

### 3.2 핵심 클래스: JmAgent
```python
class JmAgent:
    """
    범용 Claude 코딩 어시스턴트
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-haiku-4-5-20251001-v1:0",
        region: str = "us-east-1",
        temperature: float = 0.2,
        max_tokens: int = 4096,
        project_context: Optional[str] = None
    ):
        """
        Args:
            model_id: Bedrock 모델 ID
            region: AWS 리전
            temperature: 낮을수록 일관성 있음 (0.0~1.0)
            max_tokens: 최대 응답 토큰
            project_context: 프로젝트 설명 (README 또는 커스텀)
        """
    
    # === 주요 메서드 ===
    
    async def generate(
        self,
        prompt: str,
        language: Optional[str] = None,
        context_files: Optional[List[str]] = None,
        streaming: bool = False
    ) -> str:
        """코드 생성"""
    
    async def refactor(
        self,
        code: str,
        requirements: str,
        language: Optional[str] = None
    ) -> str:
        """코드 리팩토링"""
    
    async def add_tests(
        self,
        code: str,
        test_framework: str = "pytest",
        target_coverage: float = 0.8
    ) -> str:
        """테스트 코드 생성"""
    
    async def explain(self, code: str, language: Optional[str] = None) -> str:
        """코드 분석 및 한글 설명"""
    
    async def fix_bug(
        self,
        code: str,
        error_message: str,
        context: Optional[str] = None
    ) -> str:
        """버그 수정"""
    
    async def chat(self, message: str) -> str:
        """대화 (히스토리 유지)"""
    
    def reset_history(self) -> None:
        """대화 히스토리 초기화"""
```

### 3.3 CLI 인터페이스
```bash
# 1. 기본 코드 생성
jm generate --prompt "FastAPI로 GET /api/users 엔드포인트 만들어"

# 2. 파일 참고
jm generate --prompt "이 코드와 같은 패턴으로..." --file src/api.py

# 3. 언어 지정
jm generate --prompt "..." --language typescript

# 4. 리팩토링
jm refactor --file src/main.py --requirements "타입 힌트 추가 및 성능 최적화"

# 5. 테스트 생성
jm test --file src/utils.py --framework pytest

# 6. 코드 설명
jm explain --file src/complex_logic.py

# 7. 버그 수정
jm fix --file src/app.py --error "TypeError: 'NoneType' object is not subscriptable"

# 8. 대화형 모드
jm chat

# 9. 모델 변경
jm generate --prompt "..." --model sonnet

# 10. 프로젝트 컨텍스트 로드
jm generate --prompt "..." --context-file ./PROJECT.md
```

### 3.4 주요 설정
```bash
# ~/.env 또는 ~/Documents/jmAgent/.env
AWS_BEARER_TOKEN_BEDROCK=<ABSK-...>     # 또는 IAM 자격증명
AWS_BEDROCK_REGION=us-east-1

# 선택사항
JM_DEFAULT_MODEL=haiku                   # haiku, sonnet, opus
JM_TEMPERATURE=0.2
JM_MAX_TOKENS=4096
JM_PROJECT_ROOT=.                        # 프로젝트 루트 (자동 감지)
```

---

## 4. 구현 로드맵

### Phase 1: 기초 (2~3일)
- [ ] 프로젝트 초기 구조 생성
- [ ] `bedrock_auth.py` 구현 (FeedOPS 패턴 재사용)
- [ ] `agent.py` - JmAgent 핵심 클래스
- [ ] `cli.py` - argparse 기반 CLI

**산출물**: 기본 코드 생성 가능

### Phase 2: 프롬프트 & 템플릿 (2~3일)
- [ ] 시스템 프롬프트 작성
- [ ] 각 액션별 프롬프트 템플릿
- [ ] 프로젝트 컨텍스트 로더
- [ ] 토큰 추정기

**산출물**: 품질 높은 코드 생성

### Phase 3: 확장 기능 (2~3일)
- [ ] 파일 참고 기능 (여러 파일)
- [ ] 대화형 모드 (히스토리)
- [ ] 스트리밍 응답
- [ ] 코드 자동 포맷팅

**산출물**: 인터랙티브한 사용 경험

### Phase 4: 테스트 & 문서 (1~2일)
- [ ] 단위 테스트 작성
- [ ] 사용 가이드 (README)
- [ ] 예시 코드 모음
- [ ] 성능 최적화

**산출물**: 프로덕션급 도구

---

## 5. 예상 사용 시나리오

### 시나리오 1: 새 FastAPI 프로젝트
```bash
$ jm generate --prompt "FastAPI 프로젝트 구조 만들어줘" --language python
$ jm generate --prompt "사용자 관리 라우터 구현해줘" --file routes/users.py
$ jm test --file routes/users.py
```

### 시나리오 2: React 컴포넌트 리팩토링
```bash
$ jm refactor --file components/Dashboard.tsx \
  --requirements "Tailwind CSS 클래스 정리, useCallback 추가"
$ jm explain --file components/Dashboard.tsx
```

### 시나리오 3: 버그 수정
```bash
$ jm fix --file app.py --error "AttributeError: module 'X' has no attribute 'Y'"
```

### 시나리오 4: 대화형 개발
```bash
$ jm chat
> FastAPI 유저 모델 만들어줄 수 있어?
> (응답...)
> 그 모델로 CRUD 라우터도 만들어줄래?
> (응답...)
```

---

## 6. 비용 & 성능

### 6.1 토큰 예상
| 요청 | 입력 토큰 | 출력 토큰 | 비용 |
|-----|---------|----------|------|
| 간단한 코드 생성 | ~500 | ~1000 | ~$0.003 |
| 파일 참고 + 생성 | ~2000 | ~2000 | ~$0.01 |
| 리팩토링 | ~3000 | ~1500 | ~$0.01 |
| 테스트 생성 | ~2000 | ~2000 | ~$0.01 |

### 6.2 모델 선택
- **개발용** (기본): **Haiku 4.5** (빠르고 저렴)
- **복잡한 작업**: **Sonnet 4.6** (균형)
- **고품질**: **Opus 4.6** (최고 성능, 고가)

---

## 7. 설치 & 설정

### 7.1 초기 설정
```bash
# 저장소 준비
cd ~/Documents/jmAgent
python3.10+ -m venv venv
source venv/bin/activate

# 의존성 설치
pip install boto3 python-dotenv

# 환경 변수 설정
cp .env.example .env
# 편집: AWS_BEARER_TOKEN_BEDROCK 또는 IAM 자격증명 입력

# 테스트
python src/auth/bedrock_auth.py  # 인증 검증
```

### 7.2 CLI 설정 (선택)
```bash
# ~/.zshrc 또는 ~/.bashrc에 추가
alias jm='python ~/Documents/jmAgent/src/cli.py'

# 또는 pip로 설치
cd ~/Documents/jmAgent
pip install -e .
```

---

## 8. 주요 특징

### 8.1 FeedOPS에서 배운 것
✅ **인증 유연성** - API Key와 IAM 모두 지원  
✅ **대화 히스토리** - 여러 턴의 대화 유지  
✅ **토큰 최적화** - 사전 추정으로 불필요한 API 호출 방지  
✅ **모델 선택** - 작업에 맞는 모델 자동 추천  
✅ **프롬프트 템플릿** - 일관된 결과 생성  

### 8.2 차별점 (개인용)
🎯 **프로젝트 독립적** - FeedOPS 종속성 없음  
🎯 **범용성** - 모든 언어/프레임워크 지원  
🎯 **빠른 설정** - 최소 3줄로 시작 가능  
🎯 **대화형** - Claude와 자연스러운 상호작용  

---

## 9. 다음 단계

1. ✅ **계획서 작성** (현재)
2. ⏳ **Phase 1 시작**
   - `bedrock_auth.py` 구현
   - `agent.py` 기본 구조
   - `cli.py` 진입점
3. ⏳ **Phase 2: 프롬프트 작성**
4. ⏳ **Phase 3: 확장 기능**
5. ⏳ **Phase 4: 테스트 & 문서화**

---

**프로젝트 루트**: `~/Documents/jmAgent`  
**작성일**: 2026-04-02  
**상태**: 계획 단계
