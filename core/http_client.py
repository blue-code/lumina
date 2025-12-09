"""
HTTP 요청을 처리하는 클라이언트
"""
import requests
from typing import Dict
import time
import json
from models.request_model import RequestModel, HttpMethod, BodyType
from models.response_model import ResponseModel
from models.environment import EnvironmentManager
from core.auth_manager import AuthManager
from utils.variable_resolver import VariableResolver


class HttpClient:
    """HTTP 클라이언트"""

    DEFAULT_TIMEOUT = 30  # 기본 타임아웃 (초)

    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.session = requests.Session()

    def send_request(self, request: RequestModel, runtime_data: Dict = None, runtime_files: Dict = None) -> ResponseModel:
        """
        HTTP 요청 전송

        Args:
            request: 요청 모델

        Returns:
            응답 모델
        """
        response_model = ResponseModel()

        try:
            # 환경 변수로 치환
            resolved_request = self._resolve_variables(request)

            # 요청 파라미터 준비
            method = resolved_request.method.value
            url = resolved_request.url

            # 헤더와 파라미터 복사
            headers = dict(resolved_request.headers)
            params = dict(resolved_request.params)

            # 인증 적용
            auth = AuthManager.apply_auth(resolved_request, headers, params)

            # Body 준비
            body_data = None
            files = None

            if resolved_request.body_type == BodyType.RAW:
                body_data = resolved_request.body_raw
                # Content-Type이 없으면 자동 설정
                if body_data and 'Content-Type' not in headers:
                    try:
                        json.loads(body_data)  # JSON인지 확인
                        headers['Content-Type'] = 'application/json'
                    except:
                        headers['Content-Type'] = 'text/plain'

            elif resolved_request.body_type == BodyType.FORM_URLENCODED:
                body_data = resolved_request.body_form
                headers['Content-Type'] = 'application/x-www-form-urlencoded'

            elif resolved_request.body_type == BodyType.FORM_DATA:
                # multipart/form-data
                # 런타임 파일/데이터가 있으면 그것을 사용 (웹 UI 업로드)
                if runtime_files or runtime_data:
                    files = runtime_files
                    # 텍스트 필드는 body_data 로 전달 (requests가 files와 data를 함께 처리함)
                    body_data = runtime_data
                else:
                    # 저장된 설정 사용 (텍스트 필드만 가능)
                    # requests의 files 파라미터를 사용하여 multipart로 강제
                    # 튜플 형식: (filename, fileobj, content_type) -> filename이 None이면 텍스트 필드
                    files = {key: (None, value) for key, value in resolved_request.body_form.items()}

            # 요청 전송
            start_time = time.time()

            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body_data, # files와 함께 사용되면 폼 필드로 처리됨
                files=files,
                auth=auth,
                timeout=self.DEFAULT_TIMEOUT,
                allow_redirects=True,
                verify=True,  # SSL 검증
            )

            elapsed_time = time.time() - start_time

            # 응답 처리
            response_model.status_code = response.status_code
            response_model.status_text = response.reason
            response_model.headers = dict(response.headers)
            response_model.elapsed_ms = elapsed_time * 1000
            response_model.size_bytes = len(response.content)
            response_model.content_type = response.headers.get('Content-Type', '')

            # Body 처리
            try:
                response_model.body = response.text
                response_model.body_bytes = response.content
            except Exception as e:
                response_model.body = f"[Error decoding response: {str(e)}]"
                response_model.body_bytes = response.content

        except requests.exceptions.Timeout:
            response_model.error = "Request timeout"
        except requests.exceptions.ConnectionError as e:
            response_model.error = f"Connection error: {str(e)}"
        except requests.exceptions.RequestException as e:
            response_model.error = f"Request error: {str(e)}"
        except Exception as e:
            response_model.error = f"Unexpected error: {str(e)}"

        return response_model

    def _resolve_variables(self, request: RequestModel) -> RequestModel:
        """
        요청의 환경 변수를 실제 값으로 치환

        Args:
            request: 원본 요청 모델

        Returns:
            치환된 요청 모델 (새 인스턴스)
        """
        # 복제본 생성
        resolved = RequestModel.from_dict(request.to_dict())

        # 환경 변수 딕셔너리 생성
        variables = {}
        if self.env_manager.active_environment:
            variables.update(self.env_manager.active_environment.variables)
        variables.update(self.env_manager.global_environment.variables)

        # URL 치환
        resolved.url = VariableResolver.resolve(request.url, variables)

        # 헤더 치환
        resolved.headers = VariableResolver.resolve_dict(request.headers, variables)

        # 파라미터 치환
        resolved.params = VariableResolver.resolve_dict(request.params, variables)

        # Body 치환
        if request.body_type == BodyType.RAW:
            resolved.body_raw = VariableResolver.resolve(request.body_raw, variables)
        elif request.body_type in [BodyType.FORM_URLENCODED, BodyType.FORM_DATA]:
            resolved.body_form = VariableResolver.resolve_dict(request.body_form, variables)

        # 인증 정보 치환
        resolved.auth_basic_username = VariableResolver.resolve(request.auth_basic_username, variables)
        resolved.auth_basic_password = VariableResolver.resolve(request.auth_basic_password, variables)
        resolved.auth_bearer_token = VariableResolver.resolve(request.auth_bearer_token, variables)
        resolved.auth_api_key_value = VariableResolver.resolve(request.auth_api_key_value, variables)

        return resolved

    def close(self):
        """세션 종료"""
        self.session.close()
