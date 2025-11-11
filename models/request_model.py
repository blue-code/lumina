"""
HTTP 요청을 표현하는 데이터 모델
"""
import uuid
from typing import Dict, List, Optional, Any
from enum import Enum


class HttpMethod(Enum):
    """HTTP 메서드"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType(Enum):
    """인증 타입"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


class BodyType(Enum):
    """Body 타입"""
    NONE = "none"
    RAW = "raw"
    FORM_URLENCODED = "form_urlencoded"
    FORM_DATA = "form_data"


class RequestModel:
    """단일 HTTP 요청의 데이터 모델"""

    def __init__(self, name: str = "New Request"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.method = HttpMethod.GET
        self.url = ""

        # 헤더 (키-값 쌍)
        self.headers: Dict[str, str] = {}

        # 쿼리 파라미터 (키-값 쌍)
        self.params: Dict[str, str] = {}

        # Body 설정
        self.body_type = BodyType.NONE
        self.body_raw = ""  # raw 모드일 때
        self.body_form: Dict[str, str] = {}  # form 모드일 때

        # 인증 설정
        self.auth_type = AuthType.NONE
        self.auth_basic_username = ""
        self.auth_basic_password = ""
        self.auth_bearer_token = ""
        self.auth_api_key_name = ""
        self.auth_api_key_value = ""
        self.auth_api_key_location = "header"  # "header" or "query"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 저장용)"""
        return {
            "id": self.id,
            "name": self.name,
            "method": self.method.value,
            "url": self.url,
            "headers": self.headers,
            "params": self.params,
            "body_type": self.body_type.value,
            "body_raw": self.body_raw,
            "body_form": self.body_form,
            "auth_type": self.auth_type.value,
            "auth_basic_username": self.auth_basic_username,
            "auth_basic_password": self.auth_basic_password,
            "auth_bearer_token": self.auth_bearer_token,
            "auth_api_key_name": self.auth_api_key_name,
            "auth_api_key_value": self.auth_api_key_value,
            "auth_api_key_location": self.auth_api_key_location,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestModel':
        """딕셔너리에서 복원 (JSON 로드용)"""
        request = cls(data.get("name", "New Request"))
        request.id = data.get("id", str(uuid.uuid4()))
        request.method = HttpMethod(data.get("method", "GET"))
        request.url = data.get("url", "")
        request.headers = data.get("headers", {})
        request.params = data.get("params", {})
        request.body_type = BodyType(data.get("body_type", "none"))
        request.body_raw = data.get("body_raw", "")
        request.body_form = data.get("body_form", {})
        request.auth_type = AuthType(data.get("auth_type", "none"))
        request.auth_basic_username = data.get("auth_basic_username", "")
        request.auth_basic_password = data.get("auth_basic_password", "")
        request.auth_bearer_token = data.get("auth_bearer_token", "")
        request.auth_api_key_name = data.get("auth_api_key_name", "")
        request.auth_api_key_value = data.get("auth_api_key_value", "")
        request.auth_api_key_location = data.get("auth_api_key_location", "header")
        return request

    def clone(self) -> 'RequestModel':
        """요청 복제"""
        cloned = RequestModel.from_dict(self.to_dict())
        cloned.id = str(uuid.uuid4())
        cloned.name = f"{self.name} (Copy)"
        return cloned


class RequestFolder:
    """요청을 그룹화하는 폴더"""

    def __init__(self, name: str = "New Folder"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.requests: List[RequestModel] = []
        self.folders: List['RequestFolder'] = []

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "requests": [req.to_dict() for req in self.requests],
            "folders": [folder.to_dict() for folder in self.folders],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestFolder':
        """딕셔너리에서 복원"""
        folder = cls(data.get("name", "New Folder"))
        folder.id = data.get("id", str(uuid.uuid4()))
        folder.requests = [RequestModel.from_dict(req) for req in data.get("requests", [])]
        folder.folders = [RequestFolder.from_dict(f) for f in data.get("folders", [])]
        return folder

    def add_request(self, request: RequestModel):
        """요청 추가"""
        self.requests.append(request)

    def remove_request(self, request_id: str) -> bool:
        """요청 삭제"""
        for i, req in enumerate(self.requests):
            if req.id == request_id:
                del self.requests[i]
                return True
        return False

    def add_folder(self, folder: 'RequestFolder'):
        """하위 폴더 추가"""
        self.folders.append(folder)

    def remove_folder(self, folder_id: str) -> bool:
        """폴더 삭제"""
        for i, folder in enumerate(self.folders):
            if folder.id == folder_id:
                del self.folders[i]
                return True
        return False
