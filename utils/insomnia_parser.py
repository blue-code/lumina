"""
Insomnia JSON 형식 파서
Insomnia 앱의 export 파일을 Lumina 프로젝트로 변환
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType
from core.project_manager import ProjectManager


class InsomniaParser:
    """Insomnia JSON 파서"""

    @staticmethod
    def parse_insomnia_json(json_data: Dict[str, Any]) -> ProjectManager:
        """
        Insomnia JSON을 ProjectManager로 변환

        Args:
            json_data: Insomnia export JSON 데이터

        Returns:
            변환된 ProjectManager 인스턴스
        """
        # 프로젝트 생성
        pm = ProjectManager()

        # 워크스페이스 정보 추출
        resources = json_data.get('resources', [])
        workspace = None

        # 워크스페이스 찾기
        for resource in resources:
            if resource.get('_type') == 'workspace':
                workspace = resource
                break

        if workspace:
            pm.project_name = workspace.get('name', 'Imported from Insomnia')
        else:
            pm.project_name = 'Imported from Insomnia'

        # 폴더 및 요청 매핑 생성
        folders_map = {}  # folder_id -> RequestFolder
        requests = []  # 모든 요청 리스트

        # 1단계: 모든 폴더 생성
        for resource in resources:
            if resource.get('_type') == 'request_group':
                folder = InsomniaParser._create_folder(resource)
                folders_map[resource['_id']] = folder

        # 2단계: 모든 요청 생성
        for resource in resources:
            if resource.get('_type') == 'request':
                request_model = InsomniaParser._create_request(resource)
                requests.append({
                    'model': request_model,
                    'parent_id': resource.get('parentId')
                })

        # 3단계: 폴더 계층 구조 생성
        for folder_id, folder in folders_map.items():
            # 각 폴더의 부모 찾기
            for resource in resources:
                if resource.get('_id') == folder_id:
                    parent_id = resource.get('parentId')
                    if parent_id and parent_id in folders_map:
                        # 부모 폴더에 추가
                        folders_map[parent_id].add_folder(folder)
                    elif parent_id:
                        # 부모가 워크스페이스이거나 없으면 루트에 추가
                        pm.root_folder.add_folder(folder)
                    break

        # 워크스페이스 직속 폴더 추가 (아직 추가되지 않은 경우)
        for folder_id, folder in folders_map.items():
            if folder not in pm.root_folder.folders:
                # 다른 폴더의 하위가 아닌지 확인
                is_subfolder = False
                for parent_folder in folders_map.values():
                    if folder in parent_folder.folders:
                        is_subfolder = True
                        break
                if not is_subfolder:
                    pm.root_folder.add_folder(folder)

        # 4단계: 요청을 해당 폴더나 루트에 추가
        for request_data in requests:
            request_model = request_data['model']
            parent_id = request_data['parent_id']

            if parent_id in folders_map:
                # 폴더에 추가
                folders_map[parent_id].add_request(request_model)
            else:
                # 루트에 추가
                pm.root_folder.add_request(request_model)

        # 5단계: 환경 변수 처리
        InsomniaParser._import_environments(resources, pm, workspace['_id'] if workspace else None)

        return pm

    @staticmethod
    def _import_environments(resources: List[Dict[str, Any]], pm: ProjectManager, workspace_id: str):
        """Insomnia environment를 ProjectManager로 import"""
        from models.environment import Environment

        for resource in resources:
            if resource.get('_type') == 'environment':
                env_name = resource.get('name', 'Imported Environment')
                env_data = resource.get('data', {})

                # Base Environment는 Global로 처리
                if env_name == 'Base Environment' or resource.get('parentId') == workspace_id:
                    # Global environment에 변수 추가
                    for key, value in env_data.items():
                        pm.env_manager.global_environment.set(key, str(value))
                else:
                    # Sub Environment는 새로운 환경으로 추가
                    env = Environment(env_name)
                    for key, value in env_data.items():
                        env.set(key, str(value))
                    pm.env_manager.add_environment(env)

                    # 첫 번째 환경을 활성화
                    if not pm.env_manager.active_environment:
                        pm.env_manager.set_active(env.id)

    @staticmethod
    def _create_folder(resource: Dict[str, Any]) -> RequestFolder:
        """Insomnia request_group을 RequestFolder로 변환"""
        folder = RequestFolder(resource.get('name', 'Unnamed Folder'))
        return folder

    @staticmethod
    def _create_request(resource: Dict[str, Any]) -> RequestModel:
        """Insomnia request를 RequestModel로 변환"""
        request = RequestModel(resource.get('name', 'Unnamed Request'))

        # HTTP 메서드
        method_str = resource.get('method', 'GET').upper()
        try:
            request.method = HttpMethod(method_str)
        except ValueError:
            request.method = HttpMethod.GET

        # URL
        request.url = resource.get('url', '')

        # Headers
        headers = {}
        for header in resource.get('headers', []):
            if not header.get('disabled', False):
                headers[header.get('name', '')] = header.get('value', '')
        request.headers = headers

        # Query Parameters
        params = {}
        for param in resource.get('parameters', []):
            if not param.get('disabled', False):
                params[param.get('name', '')] = param.get('value', '')
        request.params = params

        # Body
        body = resource.get('body', {})
        mime_type = body.get('mimeType', '')

        if mime_type == 'application/json':
            request.body_type = BodyType.RAW
            request.body_raw = body.get('text', '')
        elif mime_type in ['multipart/form-data', 'application/x-www-form-urlencoded']:
            request.body_type = BodyType.FORM_URLENCODED
            form_params = {}
            for param in body.get('params', []):
                # 파일 업로드는 제외 (Lumina에서 지원하지 않음)
                if param.get('type') != 'file':
                    form_params[param.get('name', '')] = param.get('value', '')
            request.body_form = form_params
        else:
            request.body_type = BodyType.NONE

        # Authentication
        auth = resource.get('authentication', {})
        auth_type = auth.get('type', 'none')

        if auth_type == 'basic':
            request.auth_type = AuthType.BASIC
            request.auth_basic_username = auth.get('username', '')
            request.auth_basic_password = auth.get('password', '')
        elif auth_type == 'bearer':
            request.auth_type = AuthType.BEARER
            token = auth.get('token', '')
            prefix = auth.get('prefix', '').strip()
            # Insomnia는 prefix를 별도로 저장하지만, Lumina는 토큰에 포함
            if prefix and not token.startswith(prefix):
                request.auth_bearer_token = f"{prefix} {token}"
            else:
                request.auth_bearer_token = token
        else:
            request.auth_type = AuthType.NONE

        # Description (Documentation)
        request.documentation = resource.get('description', '')

        return request

    @staticmethod
    def export_to_insomnia(pm: ProjectManager) -> Dict[str, Any]:
        """
        ProjectManager를 Insomnia JSON 형식으로 변환

        Args:
            pm: ProjectManager 인스턴스

        Returns:
            Insomnia JSON 형식의 딕셔너리
        """
        resources = []

        # 워크스페이스 생성
        workspace_id = f"wrk_{InsomniaParser._generate_id()}"
        workspace = {
            "_id": workspace_id,
            "_type": "workspace",
            "name": pm.project_name,
            "description": "",
            "created": InsomniaParser._get_timestamp(),
            "modified": InsomniaParser._get_timestamp(),
            "parentId": None
        }
        resources.append(workspace)

        # 폴더와 요청 변환 (재귀적)
        InsomniaParser._export_folder_recursive(
            pm.root_folder,
            workspace_id,
            resources
        )

        # 환경 변수 추가
        # Base Environment (Global)
        base_env_id = f"env_{InsomniaParser._generate_id()}"
        base_environment = {
            "_id": base_env_id,
            "_type": "environment",
            "name": "Base Environment",
            "data": pm.env_manager.global_environment.variables,
            "dataPropertyOrder": None,
            "color": None,
            "isPrivate": False,
            "metaSortKey": InsomniaParser._get_timestamp(),
            "created": InsomniaParser._get_timestamp(),
            "modified": InsomniaParser._get_timestamp(),
            "parentId": workspace_id
        }
        resources.append(base_environment)

        # Sub Environments (활성 환경이 있으면 추가)
        if pm.env_manager.active_environment:
            sub_env_id = f"env_{InsomniaParser._generate_id()}"
            sub_environment = {
                "_id": sub_env_id,
                "_type": "environment",
                "name": pm.env_manager.active_environment.name,
                "data": pm.env_manager.active_environment.variables,
                "dataPropertyOrder": None,
                "color": None,
                "isPrivate": False,
                "metaSortKey": InsomniaParser._get_timestamp() + 1,
                "created": InsomniaParser._get_timestamp(),
                "modified": InsomniaParser._get_timestamp(),
                "parentId": base_env_id  # Base Environment의 하위로 설정
            }
            resources.append(sub_environment)

        # Cookie Jar 추가
        jar_id = f"jar_{InsomniaParser._generate_id()}"
        cookie_jar = {
            "_id": jar_id,
            "_type": "cookie_jar",
            "name": "Default Jar",
            "cookies": [],
            "created": InsomniaParser._get_timestamp(),
            "modified": InsomniaParser._get_timestamp(),
            "parentId": workspace_id
        }
        resources.append(cookie_jar)

        # Insomnia export 형식
        return {
            "_type": "export",
            "__export_format": 4,
            "__export_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "__export_source": "lumina.desktop.app:v1.0.0",
            "resources": resources
        }

    @staticmethod
    def _export_folder_recursive(
        folder: RequestFolder,
        parent_id: str,
        resources: List[Dict[str, Any]],
        is_root: bool = True
    ):
        """폴더와 요청을 재귀적으로 Insomnia 형식으로 변환"""
        current_parent_id = parent_id

        # 루트가 아닌 폴더만 추가
        if not is_root:
            folder_id = f"fld_{InsomniaParser._generate_id()}"
            folder_resource = {
                "_id": folder_id,
                "_type": "request_group",
                "name": folder.name,
                "description": "",
                "environment": {},
                "environmentPropertyOrder": None,
                "metaSortKey": InsomniaParser._get_timestamp(),
                "created": InsomniaParser._get_timestamp(),
                "modified": InsomniaParser._get_timestamp(),
                "parentId": parent_id
            }
            resources.append(folder_resource)
            current_parent_id = folder_id

        # 폴더의 요청 추가
        for request in folder.requests:
            request_resource = InsomniaParser._export_request(request, current_parent_id)
            resources.append(request_resource)

        # 하위 폴더 재귀 처리
        for subfolder in folder.folders:
            InsomniaParser._export_folder_recursive(
                subfolder,
                current_parent_id,
                resources,
                is_root=False
            )

    @staticmethod
    def _export_request(request: RequestModel, parent_id: str) -> Dict[str, Any]:
        """RequestModel을 Insomnia request 형식으로 변환"""
        request_id = f"req_{InsomniaParser._generate_id()}"

        # Headers
        headers = []
        for name, value in request.headers.items():
            headers.append({
                "id": f"pair_{InsomniaParser._generate_id()}",
                "name": name,
                "value": value
            })

        # Parameters (Query)
        parameters = []
        for name, value in request.params.items():
            parameters.append({
                "id": f"pair_{InsomniaParser._generate_id()}",
                "name": name,
                "value": value
            })

        # Body
        body = {}
        if request.body_type == BodyType.RAW:
            body = {
                "mimeType": "application/json",
                "text": request.body_raw
            }
        elif request.body_type == BodyType.FORM_URLENCODED:
            params = []
            for name, value in request.body_form.items():
                params.append({
                    "id": f"pair_{InsomniaParser._generate_id()}",
                    "name": name,
                    "value": value
                })
            body = {
                "mimeType": "application/x-www-form-urlencoded",
                "params": params
            }

        # Authentication
        authentication = {}
        if request.auth_type == AuthType.BASIC:
            authentication = {
                "type": "basic",
                "username": request.auth_basic_username,
                "password": request.auth_basic_password
            }
        elif request.auth_type == AuthType.BEARER:
            # Bearer 토큰에서 prefix 분리
            token = request.auth_bearer_token
            prefix = ""
            if token.startswith("Bearer "):
                prefix = "Bearer"
                token = token[7:]
            authentication = {
                "type": "bearer",
                "token": token,
                "prefix": prefix
            }

        return {
            "_id": request_id,
            "_type": "request",
            "name": request.name,
            "description": request.documentation,
            "method": request.method.value,
            "url": request.url,
            "headers": headers,
            "parameters": parameters,
            "body": body,
            "authentication": authentication,
            "isPrivate": False,
            "metaSortKey": InsomniaParser._get_timestamp(),
            "created": InsomniaParser._get_timestamp(),
            "modified": InsomniaParser._get_timestamp(),
            "parentId": parent_id,
            "settingDisableRenderRequestBody": False,
            "settingEncodeUrl": True,
            "settingRebuildPath": True,
            "settingSendCookies": True,
            "settingStoreCookies": True
        }

    @staticmethod
    def _generate_id() -> str:
        """Insomnia 스타일의 ID 생성"""
        import uuid
        return str(uuid.uuid4()).replace('-', '')[:32]

    @staticmethod
    def _get_timestamp() -> int:
        """현재 타임스탬프 (밀리초)"""
        from datetime import datetime
        return int(datetime.now().timestamp() * 1000)
