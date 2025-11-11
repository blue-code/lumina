# Lumina 사용 가이드

✨ **Elegant REST API Client for Developers**

---

## 시작하기

### 1단계: 프로그램 실행

```bash
cd /Volumes/SSD/DEV_SSD/MY/lumina
./run.sh
```

또는:

```bash
python3 main.py
```

### 2단계: 샘플 프로젝트 확인

프로그램을 처음 실행하면 샘플 프로젝트가 자동으로 로드됩니다.
- JSONPlaceholder API를 사용하는 3개의 샘플 요청이 포함되어 있습니다.
- Development 환경이 미리 설정되어 있습니다.

## 주요 기능 사용법

### 요청 만들기

#### 1. 새 요청 추가
1. 좌측 패널에서 빈 영역 우클릭
2. "새 요청 추가" 선택
3. 요청 이름 입력 (예: "Get User Info")

#### 2. 요청 설정

**HTTP 메서드 선택**
- 우측 상단 드롭다운에서 GET, POST, PUT, DELETE 등 선택

**URL 입력**
- URL 입력란에 엔드포인트 주소 입력
- 예: `https://api.example.com/users/123`

**쿼리 파라미터 추가 (Params 탭)**
1. "Params" 탭 클릭
2. Key-Value 테이블에 파라미터 입력
   - Key: `page`, Value: `1`
   - Key: `limit`, Value: `10`
3. 자동으로 URL에 `?page=1&limit=10` 추가됨

**헤더 추가 (Headers 탭)**
1. "Headers" 탭 클릭
2. 필요한 헤더 입력
   - `Content-Type`: `application/json`
   - `Accept`: `application/json`

**Body 설정 (Body 탭)**
1. "Body" 탭 클릭
2. Body Type 선택:
   - **None**: Body 없음
   - **Raw**: JSON, XML, 텍스트 등
   - **Form URL-Encoded**: 폼 데이터
   - **Form Data**: 멀티파트 폼 데이터

**Raw JSON 예시:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "age": 30
}
```

**인증 설정 (Auth 탭)**
1. "Auth" 탭 클릭
2. 인증 타입 선택:

**Basic Auth:**
- Username: `your_username`
- Password: `your_password`

**Bearer Token:**
- Token: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**API Key:**
- Key Name: `X-API-Key` 또는 `api_key`
- Key Value: `your_api_key_here`
- Add to: Header 또는 Query Params

### 요청 전송 및 응답 확인

1. 모든 설정 완료 후 상단 "Send" 버튼 클릭
2. 응답 패널에서 결과 확인:
   - **Status**: 상태 코드 (200 OK, 404 Not Found 등)
   - **Time**: 응답 시간 (밀리초)
   - **Size**: 응답 크기 (바이트)
   - **Body 탭**: 응답 본문
     - Pretty 버튼: JSON 포맷팅 보기
     - Raw 버튼: 원본 텍스트 보기
   - **Headers 탭**: 응답 헤더 목록

### 환경 변수 사용하기

#### 환경 변수 설정

1. 상단 툴바 "Manage..." 버튼 클릭
2. "Add" 버튼으로 새 환경 추가
3. 환경 이름 입력 (예: "Production")
4. Variables 테이블에 변수 추가:
   - `BASE_URL`: `https://api.production.com`
   - `API_KEY`: `prod_key_12345`
   - `USER_ID`: `42`

#### 환경 변수 사용

요청 설정에서 `{{변수명}}` 형식으로 사용:

**URL:**
```
{{BASE_URL}}/users/{{USER_ID}}
```

**Header:**
```
X-API-Key: {{API_KEY}}
```

**Body:**
```json
{
  "api_url": "{{BASE_URL}}",
  "user": "{{USER_ID}}"
}
```

#### 환경 전환

상단 툴바의 Environment 드롭다운에서 환경 선택:
- Development
- Staging
- Production

선택한 환경의 변수 값이 자동으로 적용됩니다.

### 폴더로 요청 정리하기

#### 폴더 만들기
1. 좌측 패널 빈 영역 우클릭
2. "새 폴더 추가" 선택
3. 폴더 이름 입력 (예: "User API", "Product API")

#### 폴더에 요청 추가
1. 폴더 우클릭
2. "새 요청 추가" 선택
3. 요청 설정

#### 폴더 구조 예시
```
📁 User API
  [GET] Get All Users
  [GET] Get User by ID
  [POST] Create User
  [PUT] Update User
  [DELETE] Delete User

📁 Product API
  [GET] List Products
  [POST] Add Product
```

### 요청 관리

#### 요청 복제
1. 요청 우클릭
2. "복제" 선택
3. 복제된 요청이 생성됨 (이름 뒤에 "(Copy)" 추가)

#### 요청 이름 변경
1. 요청 우클릭
2. "이름 변경" 선택
3. 새 이름 입력

#### 요청 삭제
1. 요청 우클릭
2. "삭제" 선택
3. 확인

### 프로젝트 저장/불러오기

#### 프로젝트 저장
**방법 1: 단축키**
- `Ctrl+S` (또는 `Cmd+S`)

**방법 2: 메뉴**
1. File → Save Project

프로젝트가 JSON 파일로 저장됩니다.

#### 다른 이름으로 저장
1. File → Save Project As...
2. 파일명과 위치 선택
3. 저장

#### 프로젝트 불러오기
1. File → Open Project... (`Ctrl+O`)
2. JSON 파일 선택
3. 프로젝트 로드됨

#### 프로젝트 공유
저장된 JSON 파일을 팀원과 공유하면:
- 모든 요청 구조
- 환경 변수 설정
- 폴더 구조
가 그대로 복원됩니다.

## 실전 예제

### 예제 1: GitHub API 사용하기

**환경 설정:**
```
Environment: GitHub
Variables:
  API_URL: https://api.github.com
  USERNAME: your_github_username
```

**요청 1: 사용자 정보 조회**
```
Method: GET
URL: {{API_URL}}/users/{{USERNAME}}
Headers:
  Accept: application/vnd.github.v3+json
```

**요청 2: Repository 목록**
```
Method: GET
URL: {{API_URL}}/users/{{USERNAME}}/repos
Params:
  sort: updated
  per_page: 10
```

### 예제 2: 인증이 필요한 API

**환경 설정:**
```
Environment: Authenticated
Variables:
  BASE_URL: https://api.myservice.com
  AUTH_TOKEN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**요청: 인증된 사용자 정보**
```
Method: GET
URL: {{BASE_URL}}/me
Auth: Bearer Token
Token: {{AUTH_TOKEN}}
```

### 예제 3: POST 요청으로 데이터 생성

```
Method: POST
URL: https://jsonplaceholder.typicode.com/posts
Headers:
  Content-Type: application/json
Body (Raw):
{
  "title": "My New Post",
  "body": "This is the content of my post",
  "userId": 1
}
```

Send 후 응답 확인:
```json
{
  "id": 101,
  "title": "My New Post",
  "body": "This is the content of my post",
  "userId": 1
}
```

## 팁과 트릭

### 1. 빠른 테스트를 위한 샘플 API
- JSONPlaceholder: `https://jsonplaceholder.typicode.com`
- ReqRes: `https://reqres.in/api`
- httpbin: `https://httpbin.org`

### 2. 환경 변수 활용
- 민감한 정보(API 키, 토큰)는 환경 변수로 관리
- 개발/스테이징/프로덕션 URL을 환경별로 분리

### 3. 폴더 구조화
- API 도메인별로 폴더 생성
- CRUD 작업별로 요청 그룹화

### 4. 요청 복제 활용
- 비슷한 요청은 복제 후 수정
- 시간 절약

### 5. Global 환경 사용
- 모든 프로젝트에 공통으로 사용되는 변수는 Global 환경에 저장

## 문제 해결

### 요청이 실패하는 경우
1. URL 확인 (프로토콜 포함: http:// 또는 https://)
2. 환경 변수가 올바르게 설정되었는지 확인
3. 인증 정보 확인
4. 네트워크 연결 확인

### JSON 파싱 에러
- Body 탭에서 JSON 문법 확인
- 쉼표, 따옴표 누락 확인

### 환경 변수가 치환되지 않는 경우
- 변수명 철자 확인 (대소문자 구분)
- 환경이 활성화되어 있는지 확인 (상단 드롭다운)

## 단축키 요약

- `Ctrl+N`: 새 프로젝트
- `Ctrl+O`: 프로젝트 열기
- `Ctrl+S`: 프로젝트 저장
- `Ctrl+Shift+S`: 다른 이름으로 저장
- `Ctrl+Q`: 프로그램 종료

## 다음 단계

이제 Lumina의 기본 사용법을 익혔습니다! ✨

- 실제 프로젝트에 사용해보세요
- 팀원과 프로젝트 파일을 공유해보세요
- 다양한 API를 테스트해보세요

---

<p align="center">
  <i>Illuminate your APIs with clarity and precision</i><br>
  Made with ❤️ by Python & PyQt5
</p>
