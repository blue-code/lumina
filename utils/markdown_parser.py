"""
Markdown API Parser
마크다운 형식으로 API 정보를 파싱하고 생성하는 모듈
"""
import re
from typing import List, Dict, Optional
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType


class MarkdownAPIParser:
    """마크다운 API 파서"""

    @staticmethod
    def parse_file(file_path: str) -> RequestFolder:
        """
        마크다운 파일을 파싱하여 RequestFolder 생성

        Args:
            file_path: 마크다운 파일 경로

        Returns:
            RequestFolder: 파싱된 요청들이 포함된 폴더
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return MarkdownAPIParser.parse_content(content)

    @staticmethod
    def parse_content(content: str) -> RequestFolder:
        """
        마크다운 콘텐츠를 파싱하여 RequestFolder 생성

        마크다운 형식:
        # Collection Name

        ## Request Name
        - Method: GET
        - URL: https://api.example.com/endpoint
        - Headers:
          - Key: Value
        - Params:
          - key: value
        - Body:
        ```json
        {"key": "value"}
        ```

        Args:
            content: 마크다운 콘텐츠

        Returns:
            RequestFolder: 파싱된 폴더
        """
        lines = content.split('\n')
        folder_name = "Imported Collection"
        requests = []
        current_request = None
        current_section = None
        body_lines = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # 폴더 이름 (# Title)
            if stripped.startswith('# ') and not stripped.startswith('## '):
                folder_name = stripped[2:].strip()
                continue

            # 요청 시작 (## Request Name)
            if stripped.startswith('## '):
                # 이전 요청 저장
                if current_request:
                    if body_lines:
                        current_request.body_raw = '\n'.join(body_lines).strip()
                    requests.append(current_request)

                # 새 요청 생성
                request_name = stripped[3:].strip()
                current_request = RequestModel(request_name)
                current_section = None
                body_lines = []
                in_code_block = False
                continue

            # 구분선 (---)
            if stripped.startswith('---'):
                if current_request:
                    if body_lines:
                        current_request.body_raw = '\n'.join(body_lines).strip()
                    requests.append(current_request)
                    current_request = None
                    body_lines = []
                    in_code_block = False
                continue

            if not current_request:
                continue

            # Method
            if stripped.startswith('- Method:'):
                method_str = stripped.split(':', 1)[1].strip().upper()
                try:
                    current_request.method = HttpMethod[method_str]
                except KeyError:
                    current_request.method = HttpMethod.GET
                continue

            # URL
            if stripped.startswith('- URL:'):
                current_request.url = stripped.split(':', 1)[1].strip()
                continue

            # 섹션 시작
            if stripped.startswith('- Headers:'):
                current_section = 'headers'
                continue

            if stripped.startswith('- Params:'):
                current_section = 'params'
                continue

            if stripped.startswith('- Body:'):
                current_section = 'body'
                current_request.body_type = BodyType.RAW
                continue

            if stripped.startswith('- Auth:'):
                current_section = 'auth'
                continue

            # 코드 블록 (Body)
            if current_section == 'body':
                if stripped.startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or stripped:
                    body_lines.append(line.rstrip())
                continue

            # Key-Value 파싱 (들여쓰기된 항목)
            if stripped.startswith('- ') and ':' in stripped:
                kv_part = stripped[2:].strip()
                if ':' in kv_part:
                    key, value = kv_part.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if current_section == 'headers':
                        current_request.headers[key] = value
                    elif current_section == 'params':
                        current_request.params[key] = value

        # 마지막 요청 저장
        if current_request:
            if body_lines:
                current_request.body_raw = '\n'.join(body_lines).strip()
            requests.append(current_request)

        # RequestFolder 생성
        folder = RequestFolder(folder_name)
        for req in requests:
            folder.add_request(req)

        return folder

    @staticmethod
    def generate_markdown(folder: RequestFolder) -> str:
        """
        RequestFolder를 마크다운 형식으로 변환

        Args:
            folder: 변환할 폴더

        Returns:
            str: 마크다운 문자열
        """
        lines = []

        # 제목
        lines.append(f"# {folder.name}\n")
        lines.append(f"*Generated by Lumina - {len(folder.requests)} requests*\n")

        # 각 요청 변환
        for i, request in enumerate(folder.requests):
            if i > 0:
                lines.append("\n---\n")

            lines.append(f"\n## {request.name}\n")

            # Method
            lines.append(f"- Method: {request.method.value}")

            # URL
            lines.append(f"- URL: {request.url}")

            # Headers
            if request.headers:
                lines.append("- Headers:")
                for key, value in request.headers.items():
                    lines.append(f"  - {key}: {value}")

            # Params
            if request.params:
                lines.append("- Params:")
                for key, value in request.params.items():
                    lines.append(f"  - {key}: {value}")

            # Body
            if request.body_type == BodyType.RAW and request.body_raw:
                lines.append("- Body:")
                lines.append("```json")
                lines.append(request.body_raw)
                lines.append("```")

            lines.append("")  # 빈 줄

        return '\n'.join(lines)

    @staticmethod
    def export_to_file(folder: RequestFolder, file_path: str):
        """
        RequestFolder를 마크다운 파일로 내보내기

        Args:
            folder: 내보낼 폴더
            file_path: 저장할 파일 경로
        """
        markdown_content = MarkdownAPIParser.generate_markdown(folder)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)


def test_parser():
    """파서 테스트"""
    sample_md = """# Sample API Collection

## Get All Users

- Method: GET
- URL: https://jsonplaceholder.typicode.com/users
- Headers:
  - Content-Type: application/json
  - Accept: application/json
- Params:
  - page: 1
  - limit: 10

---

## Create User

- Method: POST
- URL: https://jsonplaceholder.typicode.com/users
- Headers:
  - Content-Type: application/json
- Body:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "username": "johndoe"
}
```

---

## Get Single User

- Method: GET
- URL: https://jsonplaceholder.typicode.com/users/1
- Headers:
  - Accept: application/json
"""

    folder = MarkdownAPIParser.parse_content(sample_md)
    print(f"Folder: {folder.name}")
    print(f"Requests: {len(folder.requests)}")
    for req in folder.requests:
        print(f"  - {req.method.value} {req.name}: {req.url}")

    # Generate markdown back
    generated = MarkdownAPIParser.generate_markdown(folder)
    print("\n=== Generated Markdown ===")
    print(generated)


if __name__ == '__main__':
    test_parser()
