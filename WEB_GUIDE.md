# Lumina 웹 인터페이스 가이드

✨ **브라우저에서 사용하는 REST API 클라이언트**

---

## 개요

Lumina는 데스크톱 앱 뿐만 아니라 **웹 브라우저**에서도 사용할 수 있습니다. Flask 기반 웹 서버를 통해 어디서나 접근 가능한 API 테스트 도구를 제공합니다.

## 실행 방법

### 방법 1: 웹 서버 단독 실행

```bash
cd /Volumes/SSD/DEV_SSD/MY/lumina
python web_server_standalone.py
```

브라우저에서 http://localhost:5000 접속

### 방법 2: 데스크톱 앱에서 실행

1. Lumina 데스크톱 앱 실행
2. 메뉴바에서 `View` → `Open Web Interface` 선택
3. 또는 단축키 `Ctrl+W` (macOS: `Cmd+W`)
4. 자동으로 브라우저가 열림

## 주요 기능

### 1. 요청 목록 (좌측 사이드바)

- 모든 저장된 요청이 표시됨
- HTTP 메서드별 색상 구분
  - **GET**: 녹색
  - **POST**: 파란색
  - **PUT**: 주황색
  - **DELETE**: 빨간색
- 클릭하여 요청 선택

### 2. 요청 편집 (상단 영역)

**기본 설정:**
- HTTP 메서드 선택 (드롭다운)
- URL 입력
- **Send** 버튼으로 요청 전송

**탭 메뉴:**

**Params 탭**
- 쿼리 파라미터 추가
- Key-Value 형식
- 자동으로 URL에 `?key=value` 추가

**Headers 탭**
- HTTP 헤더 설정
- `Content-Type`, `Authorization` 등

**Body 탭**
- Raw 모드: JSON, XML, 텍스트 입력
- 자동 문법 하이라이팅

### 3. 응답 보기 (하단 영역)

요청 전송 후 자동으로 표시:

- **Status**: HTTP 상태 코드 (200 OK, 404 Not Found 등)
- **Time**: 응답 시간 (밀리초)
- **Size**: 응답 크기 (바이트)
- **Body**: Pretty JSON 포맷으로 자동 표시

## 사용 예시

### 1. 새 요청 만들기

1. 좌측 상단 **+ New** 버튼 클릭
2. 요청 이름 입력
3. HTTP 메서드와 URL 설정
4. **Send** 버튼 클릭

### 2. 기존 요청 수정

1. 좌측 목록에서 요청 선택
2. URL이나 파라미터 수정
3. 자동으로 저장됨
4. **Send** 버튼으로 실행

### 3. GET 요청 보내기

```
1. 메서드: GET 선택
2. URL: https://jsonplaceholder.typicode.com/users
3. Send 클릭
4. 응답에서 사용자 목록 확인
```

### 4. POST 요청 (JSON Body)

```
1. 메서드: POST 선택
2. URL: https://jsonplaceholder.typicode.com/posts
3. Body 탭 클릭
4. JSON 입력:
   {
     "title": "My Post",
     "body": "Content here",
     "userId": 1
   }
5. Send 클릭
```

## API 엔드포인트

웹 서버는 다음 REST API를 제공합니다:

### 프로젝트 관리
- `GET /api/project` - 프로젝트 정보
- `POST /api/project/save` - 프로젝트 저장
- `POST /api/project/load` - 프로젝트 불러오기

### 요청 관리
- `GET /api/requests` - 모든 요청 목록
- `GET /api/requests/<id>` - 특정 요청 조회
- `POST /api/requests` - 새 요청 생성
- `PUT /api/requests/<id>` - 요청 수정
- `DELETE /api/requests/<id>` - 요청 삭제
- `POST /api/requests/<id>/execute` - 요청 실행

### 환경 변수
- `GET /api/environments` - 환경 목록
- `GET /api/environments/active` - 활성 환경
- `POST /api/environments/active` - 환경 설정

## 데스크톱 vs 웹 인터페이스

| 기능 | 데스크톱 | 웹 |
|------|----------|-----|
| HTTP 요청 전송 | ✅ | ✅ |
| 요청 편집 | ✅ | ✅ |
| 응답 Pretty JSON | ✅ | ✅ |
| 프로젝트 저장/불러오기 | ✅ | ✅ |
| 환경 변수 | ✅ | ✅ |
| 폴더 구조 | ✅ | 부분 지원 |
| 드래그 앤 드롭 | ✅ | ❌ |
| 오프라인 사용 | ✅ | ❌ |

## 장점

### 웹 인터페이스의 장점
- 설치 불필요 (브라우저만 있으면 됨)
- 어디서나 접근 가능
- 서버에서 실행 시 팀원과 공유 가능
- 가볍고 빠른 로딩

### 데스크톱 앱의 장점
- 오프라인 사용 가능
- 더 풍부한 UI/UX
- 파일 시스템 직접 접근
- 고급 기능 (폴더 관리, 환경 변수 관리 등)

## 포트 변경

기본 포트는 `5000`입니다. 변경하려면:

**web/web_server.py 수정:**
```python
server = LuminaWebServer(host='0.0.0.0', port=8080)  # 원하는 포트로 변경
```

## 보안 주의사항

⚠️ **주의**: 웹 서버는 기본적으로 `127.0.0.1` (localhost)에서만 접근 가능합니다.

외부 접근을 허용하려면:
```python
server = LuminaWebServer(host='0.0.0.0', port=5000)
```

단, 보안을 위해 다음을 고려하세요:
- HTTPS 사용
- 인증 추가
- 방화벽 설정

## 문제 해결

### 포트가 이미 사용 중입니다
```
Error: Address already in use
```

**해결 방법:**
1. 다른 프로세스가 5000번 포트를 사용 중입니다
2. 해당 프로세스를 종료하거나
3. 다른 포트 번호를 사용하세요

### 브라우저에서 연결할 수 없습니다

**확인사항:**
1. 웹 서버가 실행 중인지 확인
2. 올바른 URL 사용 (`http://localhost:5000`)
3. 방화벽이 포트를 차단하지 않는지 확인

## 다음 단계

- 샘플 API로 테스트해보기
  - JSONPlaceholder: https://jsonplaceholder.typicode.com
  - ReqRes: https://reqres.in/api
- 환경 변수 설정하여 재사용성 높이기
- 팀원과 프로젝트 JSON 파일 공유하기

---

<p align="center">
  <i>Illuminate your APIs with clarity and precision</i><br>
  Made with ❤️ by Python, Flask & JavaScript
</p>
