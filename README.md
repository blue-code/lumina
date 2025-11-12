# Lumina

✨ **Elegant REST API Client for Developers**

Python 기반의 세련되고 강력한 REST API 테스트 도구

<p align="center">
  <i>"Illuminate your APIs with clarity and precision"</i>
</p>

---

## 🌟 주요 기능

- **데스크톱 & 웹 인터페이스**: PyQt5 GUI와 웹 브라우저 양쪽에서 사용 가능
- **다양한 HTTP 메서드 지원**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **직관적인 요청 구성**: Headers, URL Parameters, Query Parameters, Body (Raw/Form)
- **다중 인증 방식**: Basic Auth, Bearer Token, API Key
- **스마트 환경 변수**: 재사용 가능한 환경별 변수 관리 (`{{variable}}` 지원)
- **아름다운 응답 표시**: Pretty JSON, Raw 뷰, Headers 확인
- **프로젝트 관리**: JSON 파일로 요청 저장/불러오기/팀 공유
- **폴더 구조**: 요청을 폴더로 그룹화하여 체계적 관리
- **마크다운 Import/Export**: 마크다운 형식으로 API 정의를 가져오고 내보내기

## 🚀 빠른 시작

### 필수 요구사항

- Python 3.7 이상
- pip

### 설치

```bash
cd lumina
pip install -r requirements.txt
```

또는:

```bash
pip install PyQt5 requests pygments
```

### 실행

**데스크톱 앱 (PyQt5 GUI):**

```bash
python main.py
```

또는:

```bash
./run.sh
```

**웹 인터페이스 (브라우저):**

```bash
python web_server_standalone.py
```

그리고 브라우저에서 `http://localhost:5000` 접속

또는 데스크톱 앱에서 `View` → `Open Web Interface` (`Ctrl+W`)

## 📖 사용 방법

### 1. 새 요청 만들기

1. 좌측 패널에서 우클릭 → "새 요청 추가"
2. 요청 이름 입력
3. HTTP 메서드 선택 및 URL 입력
4. Headers, Params, Body, Auth 설정
5. **Send** 버튼 클릭 ⚡

### 2. 환경 변수 활용

```
Environment: Development
Variables:
  API_URL = https://api.example.com
  USER_ID = 123

Request URL:
  {{API_URL}}/users/{{USER_ID}}

→ https://api.example.com/users/123
```

### 3. 프로젝트 관리

- **저장**: `Ctrl+S` or File → Save Project
- **불러오기**: `Ctrl+O` or File → Open Project
- **공유**: JSON 파일을 팀원과 공유

### 4. 마크다운으로 API 가져오기/내보내기

**가져오기 (Import):**
1. 데스크톱: `File` → `Import from Markdown...` (`Ctrl+I`)
2. 웹: 좌측 사이드바에서 `📥 Import` 버튼 클릭
3. 마크다운 파일 선택 또는 내용 붙여넣기
4. 자동으로 요청이 생성됨

**내보내기 (Export):**
1. 데스크톱: `File` → `Export to Markdown...` (`Ctrl+E`)
2. 웹: 좌측 사이드바에서 `📤 Export` 버튼 클릭
3. 마크다운 형식으로 모든 요청이 변환됨
4. 파일로 저장하거나 클립보드에 복사

**마크다운 형식 예시:**

```markdown
# API Collection Name

## Request Name
- Method: GET
- URL: https://api.example.com/users
- Headers:
  - Content-Type: application/json
  - Authorization: Bearer {{TOKEN}}
- Params:
  - page: 1
  - limit: 10
- Body:
\```json
{
  "key": "value"
}
\```
```

샘플 파일: `sample_api.md` 참고

## 🏗️ 프로젝트 구조

```
lumina/
├── main.py                      # 데스크톱 앱 메인
├── web_server_standalone.py    # 웹 서버 단독 실행
├── test_concurrency.py          # 동시성 테스트 스크립트
├── requirements.txt             # 의존성 목록
├── sample_api.md                # 마크다운 샘플 파일
├── models/                      # 데이터 모델
│   ├── request_model.py         # 요청/폴더 모델
│   ├── environment.py           # 환경 변수 모델
│   └── response_model.py        # 응답 모델
├── core/                        # 핵심 로직
│   ├── http_client.py           # HTTP 클라이언트
│   ├── auth_manager.py          # 인증 관리자
│   └── project_manager.py       # 프로젝트 관리자
├── ui/                          # 데스크톱 UI
│   ├── main_window.py           # 메인 윈도우
│   ├── request_tree_widget.py   # 요청 트리
│   ├── request_editor_panel.py  # 요청 편집 패널
│   ├── response_panel.py        # 응답 표시 패널
│   └── environment_dialog.py    # 환경 관리 다이얼로그
├── web/                         # 웹 인터페이스
│   ├── web_server.py            # Flask 웹 서버
│   ├── templates/               # HTML 템플릿
│   │   └── index.html
│   └── static/                  # CSS, JavaScript
│       ├── css/style.css
│       └── js/app.js
└── utils/                       # 유틸리티
    ├── variable_resolver.py     # 변수 치환 도구
    └── markdown_parser.py       # 마크다운 파서
```

## 💡 샘플 사용 예시

### GET 요청

```
Method: GET
URL: https://jsonplaceholder.typicode.com/users
```

### POST 요청 (JSON Body)

```
Method: POST
URL: https://jsonplaceholder.typicode.com/posts
Headers:
  Content-Type: application/json
Body (Raw):
{
  "title": "Sample Post",
  "body": "This is a sample post",
  "userId": 1
}
```

### Bearer Token 인증

```
Auth Type: Bearer Token
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## ⌨️ 단축키 (데스크톱 앱)

- `Ctrl+N`: 새 프로젝트
- `Ctrl+O`: 프로젝트 열기
- `Ctrl+S`: 프로젝트 저장
- `Ctrl+Shift+S`: 다른 이름으로 저장
- `Ctrl+I`: 마크다운 가져오기
- `Ctrl+E`: 마크다운 내보내기
- `Ctrl+W`: 웹 인터페이스 열기
- `Ctrl+Q`: 종료

## ✨ 주요 기능

### 🔒 동시 작업자 지원 (Thread-Safe & Session Isolation)

Lumina는 서버 환경에서 여러 사용자가 동시에 작업해도 안전합니다:

- **Thread-Safe 구현**: 모든 프로젝트 매니저 작업에 RLock 적용
- **세션별 프로젝트 격리**: 각 웹 사용자가 독립적인 프로젝트 공간 보유
- **Race Condition 방지**: 동시 읽기/쓰기 작업에서 데이터 무결성 보장
- **동시성 테스트 통과**: 수백 개의 동시 작업 검증 완료

**동시성 테스트 실행:**
```bash
python test_concurrency.py
```

**작동 방식:**
- **데스크톱 앱 모드**: 단일 프로젝트를 데스크톱과 웹 UI가 공유
- **웹 서버 단독 모드**: 각 사용자는 세션별로 독립적인 프로젝트 보유

### 듀얼 인터페이스
- **데스크톱 앱**: PyQt5 기반 네이티브 애플리케이션
- **웹 인터페이스**: Flask 기반 브라우저 접근
- 동일한 프로젝트를 양쪽에서 사용 가능

### 요청 관리
- 폴더 구조로 요청 그룹화
- 요청 복제 기능
- 컨텍스트 메뉴로 빠른 작업

### 환경 변수
- Global 환경: 모든 프로젝트에 공통 적용
- 프로젝트별 환경: Development, Staging, Production
- `{{변수명}}` 형식으로 어디서든 사용

### 인증 방식
- **Basic Auth**: 사용자명/비밀번호
- **Bearer Token**: JWT 등의 토큰
- **API Key**: Header 또는 Query Parameter

### 응답 표시
- **Pretty JSON**: 자동 포맷팅
- **Raw**: 원본 텍스트
- **Headers**: 응답 헤더 목록
- 상태 코드, 응답 시간, 크기 표시

## 🔮 향후 계획

- OAuth 2.0 인증 지원
- 요청 히스토리 관리
- 자동 테스트 스크립팅
- 응답 검증 기능
- WebSocket 지원
- GraphQL 지원
- 플러그인 시스템
- 세션 타임아웃 및 자동 정리 기능

## 📝 라이선스

본 프로젝트는 교육/학습 목적으로 제작되었습니다.

## 🤝 기여

버그 리포트나 기능 제안은 언제나 환영합니다!

---

<p align="center">
  Made with ❤️ by Python & PyQt5
</p>
