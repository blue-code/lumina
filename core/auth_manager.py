"""
인증을 관리하는 모듈
"""
import base64
from typing import Dict, Optional, Tuple
from requests.auth import HTTPBasicAuth
from models.request_model import RequestModel, AuthType


class AuthManager:
    """인증 관리자"""

    @staticmethod
    def apply_auth(request: RequestModel, headers: Dict[str, str], params: Dict[str, str]) -> Optional[HTTPBasicAuth]:
        """
        요청에 인증 정보 적용

        Args:
            request: 요청 모델
            headers: 헤더 딕셔너리 (수정됨)
            params: 파라미터 딕셔너리 (수정됨)

        Returns:
            HTTPBasicAuth 객체 (Basic Auth 사용 시) 또는 None
        """
        if request.auth_type == AuthType.NONE:
            return None

        elif request.auth_type == AuthType.BASIC:
            # Basic Auth - requests 라이브러리의 HTTPBasicAuth 사용
            return HTTPBasicAuth(request.auth_basic_username, request.auth_basic_password)

        elif request.auth_type == AuthType.BEARER:
            # Bearer Token - Authorization 헤더에 추가
            if request.auth_bearer_token:
                headers['Authorization'] = f'Bearer {request.auth_bearer_token}'

        elif request.auth_type == AuthType.API_KEY:
            # API Key - 헤더 또는 쿼리 파라미터로 추가
            if request.auth_api_key_name and request.auth_api_key_value:
                if request.auth_api_key_location == "header":
                    headers[request.auth_api_key_name] = request.auth_api_key_value
                else:  # query
                    params[request.auth_api_key_name] = request.auth_api_key_value

        return None

    @staticmethod
    def get_auth_preview(request: RequestModel) -> str:
        """
        인증 설정 미리보기 텍스트

        Args:
            request: 요청 모델

        Returns:
            인증 정보 문자열
        """
        if request.auth_type == AuthType.NONE:
            return "No authentication"

        elif request.auth_type == AuthType.BASIC:
            username = request.auth_basic_username or "(none)"
            return f"Basic Auth: {username}"

        elif request.auth_type == AuthType.BEARER:
            token_preview = request.auth_bearer_token[:20] + "..." if len(request.auth_bearer_token) > 20 else request.auth_bearer_token
            return f"Bearer Token: {token_preview or '(none)'}"

        elif request.auth_type == AuthType.API_KEY:
            location = "Header" if request.auth_api_key_location == "header" else "Query Param"
            key_name = request.auth_api_key_name or "(none)"
            return f"API Key ({location}): {key_name}"

        return "Unknown authentication type"
