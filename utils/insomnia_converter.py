"""
Insomnia Import/Export Converter
Insomnia 형식과 Lumina 형식 간 변환
"""
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType


class InsomniaConverter:
    """Insomnia 형식 변환기"""

    @staticmethod
    def import_from_insomnia(insomnia_data: Dict[str, Any]) -> tuple[RequestFolder, Dict[str, str]]:
        """
        Insomnia JSON 데이터를 Lumina RequestFolder로 변환

        Args:
            insomnia_data: Insomnia export JSON

        Returns:
            Tuple[RequestFolder, Dict[str, str]]: 변환된 폴더와 전역 변수
        """
        resources = insomnia_data.get('resources', [])

        # 워크스페이스 찾기
        workspace = None
        for resource in resources:
            if resource.get('_type') == 'workspace':
                workspace = resource
                break
        
        root_name = workspace.get('name', 'Imported from Insomnia') if workspace else 'Imported from Insomnia'
        root_folder = RequestFolder(root_name)
        
        workspace_id = workspace.get('_id') if workspace else None

        # 폴더 매핑 (ID -> Folder)
        folders = {}
        folders['__root__'] = root_folder
        if workspace_id:
            folders[workspace_id] = root_folder

        # 1. 폴더 생성 (Request Groups)
        for resource in resources:
            if resource.get('_type') == 'request_group':
                folder = RequestFolder(resource.get('name', 'Unnamed Folder'))
                folder.id = resource.get('_id', str(uuid.uuid4()))
                folders[resource['_id']] = folder

        # 2. 폴더 계층 구조 연결
        for resource in resources:
            if resource.get('_type') == 'request_group':
                folder_id = resource['_id']
                parent_id = resource.get('parentId')

                if folder_id in folders:
                    folder = folders[folder_id]
                    # 부모가 없거나 워크스페이스면 루트에 추가
                    if not parent_id or parent_id == workspace_id:
                        parent_folder = root_folder
                    else:
                        parent_folder = folders.get(parent_id, root_folder)
                    
                    # 루트가 자기 자신이 아니고, 부모의 자식에 아직 없으면 추가
                    if folder != parent_folder and folder not in parent_folder.folders:
                        parent_folder.add_folder(folder)

        # 3. 요청 생성 및 폴더에 할당
        for resource in resources:
            if resource.get('_type') == 'request':
                request = InsomniaConverter._convert_insomnia_request(resource)
                parent_id = resource.get('parentId')
                
                # 부모가 없거나 워크스페이스면 루트에 추가
                if not parent_id or parent_id == workspace_id:
                    parent_folder = root_folder
                else:
                    parent_folder = folders.get(parent_id, root_folder)
                
                parent_folder.add_request(request)

        # 4. 환경 변수 추출 (Base Environment)
        global_vars = {}
        for resource in resources:
            if resource.get('_type') == 'environment':
                # Base Environment는 parentId가 워크스페이스 ID임
                if resource.get('parentId') == workspace_id:
                    env_data = resource.get('data', {})
                    for k, v in env_data.items():
                        global_vars[k] = str(v)
                    break

        return root_folder, global_vars

    @staticmethod
    def _convert_insomnia_request(insomnia_req: Dict[str, Any]) -> RequestModel:
        """Insomnia 요청을 Lumina RequestModel로 변환"""
        request = RequestModel(insomnia_req.get('name', 'Unnamed Request'))

        # Method
        method_str = insomnia_req.get('method', 'GET').upper()
        try:
            request.method = HttpMethod[method_str]
        except KeyError:
            request.method = HttpMethod.GET

        # URL
        request.url = insomnia_req.get('url', '')

        # Headers (disabled 파라미터 제외)
        headers = insomnia_req.get('headers', [])
        if isinstance(headers, list):
            request.headers = {
                h.get('name', ''): h.get('value', '')
                for h in headers
                if h.get('name') and not h.get('disabled', False)
            }

        # Parameters (query params, disabled 파라미터 제외)
        parameters = insomnia_req.get('parameters', [])
        if isinstance(parameters, list):
            request.params = {
                p.get('name', ''): p.get('value', '')
                for p in parameters
                if p.get('name') and not p.get('disabled', False)
            }

        # Body
        body = insomnia_req.get('body', {})
        if body:
            mime_type = body.get('mimeType', '')

            if mime_type == 'application/json' or 'json' in mime_type.lower():
                request.body_type = BodyType.RAW
                request.body_raw = body.get('text', '')
            elif mime_type == 'application/x-www-form-urlencoded':
                request.body_type = BodyType.FORM_URLENCODED
                params = body.get('params', [])
                if isinstance(params, list):
                    request.body_form = {
                        p.get('name', ''): p.get('value', '')
                        for p in params
                        if p.get('name') and not p.get('disabled', False)
                    }
            elif mime_type == 'multipart/form-data':
                request.body_type = BodyType.FORM_DATA
                params = body.get('params', [])
                if isinstance(params, list):
                    request.body_form = {
                        p.get('name', ''): p.get('value', '')
                        for p in params
                        if p.get('name') and not p.get('disabled', False)
                    }
            else:
                request.body_type = BodyType.RAW
                request.body_raw = body.get('text', '')

        # Authentication
        auth = insomnia_req.get('authentication', {})
        if auth:
            auth_type = auth.get('type', '').lower()

            if auth_type == 'basic':
                request.auth_type = AuthType.BASIC
                request.auth_basic_username = auth.get('username', '')
                request.auth_basic_password = auth.get('password', '')
            elif auth_type == 'bearer':
                request.auth_type = AuthType.BEARER
                request.auth_bearer_token = auth.get('token', '')
            elif auth_type == 'apikey':
                request.auth_type = AuthType.API_KEY
                request.auth_api_key_name = auth.get('key', '')
                request.auth_api_key_value = auth.get('value', '')
                # Insomnia uses "addTo" field: "header" or "queryParams"
                add_to = auth.get('addTo', 'header')
                request.auth_api_key_location = 'header' if add_to == 'header' else 'query'

        return request

    @staticmethod
    def export_to_insomnia(folder: RequestFolder, project_name: str = None) -> Dict[str, Any]:
        """
        Lumina RequestFolder를 Insomnia JSON 형식으로 변환

        Args:
            folder: 변환할 폴더
            project_name: 프로젝트 이름 (워크스페이스 이름으로 사용)

        Returns:
            Dict: Insomnia export JSON
        """
        resources = []
        current_time = int(time.time() * 1000)  # 밀리초 단위 타임스탬프

        # 워크스페이스 생성
        workspace_id = f"wrk_{str(uuid.uuid4()).replace('-', '')}"
        workspace_name = project_name or (folder.name if folder.name != "Root" else "Lumina Export")
        workspace = {
            "_id": workspace_id,
            "_type": "workspace",
            "parentId": None,
            "modified": current_time,
            "created": current_time,
            "name": workspace_name,
            "description": "Exported from Lumina",
            "scope": "collection"
        }
        resources.append(workspace)

        # 재귀적으로 폴더와 요청 변환 (워크스페이스를 부모로 설정)
        InsomniaConverter._export_folder_recursive(folder, resources, workspace_id, current_time)

        # ISO 8601 형식의 날짜 생성
        export_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        return {
            "_type": "export",
            "__export_format": 4,
            "__export_date": export_date,
            "__export_source": "lumina.desktop.app:v1.0",
            "resources": resources
        }

    @staticmethod
    def _export_folder_recursive(folder: RequestFolder, resources: List[Dict], parent_id: str = None, base_time: int = None):
        """재귀적으로 폴더와 요청을 Insomnia 형식으로 변환"""
        if base_time is None:
            base_time = int(time.time() * 1000)

        # 루트 폴더가 아닌 경우 폴더 자체를 추가
        current_parent_id = parent_id
        if folder.name != "Root":
            folder_resource = {
                "_id": folder.id,
                "_type": "request_group",
                "parentId": parent_id,
                "modified": base_time,
                "created": base_time,
                "name": folder.name,
                "description": "",
                "environment": {},
                "environmentPropertyOrder": None,
                "metaSortKey": -base_time
            }
            resources.append(folder_resource)
            current_parent_id = folder.id

        # 요청 변환
        for idx, request in enumerate(folder.requests):
            request_resource = InsomniaConverter._convert_to_insomnia_request(
                request, current_parent_id, base_time - idx
            )
            resources.append(request_resource)

        # 하위 폴더 재귀 처리
        for sub_folder in folder.folders:
            InsomniaConverter._export_folder_recursive(sub_folder, resources, current_parent_id, base_time)

    @staticmethod
    def _convert_to_insomnia_request(request: RequestModel, parent_id: str = None, timestamp: int = None) -> Dict[str, Any]:
        """Lumina RequestModel을 Insomnia 요청으로 변환"""
        if timestamp is None:
            timestamp = int(time.time() * 1000)

        insomnia_req = {
            "_id": request.id,
            "_type": "request",
            "parentId": parent_id,
            "modified": timestamp,
            "created": timestamp,
            "url": request.url,
            "name": request.name,
            "description": "",
            "method": request.method.value,
            "body": {},
            "parameters": [],
            "headers": [],
            "authentication": {},
            "metaSortKey": -timestamp,
            "isPrivate": False,
            "settingStoreCookies": True,
            "settingSendCookies": True,
            "settingDisableRenderRequestBody": False,
            "settingEncodeUrl": True,
            "settingRebuildPath": True,
            "settingFollowRedirects": "global"
        }

        # Headers
        insomnia_req['headers'] = [
            {
                "id": f"pair_{str(uuid.uuid4()).replace('-', '')}",
                "name": key,
                "value": value,
                "disabled": False
            }
            for key, value in request.headers.items()
        ]

        # Parameters
        insomnia_req['parameters'] = [
            {
                "id": f"pair_{str(uuid.uuid4()).replace('-', '')}",
                "name": key,
                "value": value,
                "disabled": False
            }
            for key, value in request.params.items()
        ]

        # Body
        if request.body_type == BodyType.RAW and request.body_raw:
            insomnia_req['body'] = {
                "mimeType": "application/json",
                "text": request.body_raw
            }
        elif request.body_type == BodyType.FORM_URLENCODED:
            insomnia_req['body'] = {
                "mimeType": "application/x-www-form-urlencoded",
                "params": [
                    {
                        "id": f"pair_{str(uuid.uuid4()).replace('-', '')}",
                        "name": key,
                        "value": value,
                        "disabled": False
                    }
                    for key, value in request.body_form.items()
                ]
            }
        elif request.body_type == BodyType.FORM_DATA:
            insomnia_req['body'] = {
                "mimeType": "multipart/form-data",
                "params": [
                    {
                        "id": f"pair_{str(uuid.uuid4()).replace('-', '')}",
                        "name": key,
                        "value": value,
                        "disabled": False,
                        "type": "text"
                    }
                    for key, value in request.body_form.items()
                ]
            }

        # Authentication
        if request.auth_type == AuthType.BASIC:
            insomnia_req['authentication'] = {
                "type": "basic",
                "username": request.auth_basic_username,
                "password": request.auth_basic_password,
                "disabled": False
            }
        elif request.auth_type == AuthType.BEARER:
            insomnia_req['authentication'] = {
                "type": "bearer",
                "token": request.auth_bearer_token,
                "prefix": "",
                "disabled": False
            }
        elif request.auth_type == AuthType.API_KEY:
            insomnia_req['authentication'] = {
                "type": "apikey",
                "key": request.auth_api_key_name,
                "value": request.auth_api_key_value,
                "addTo": "header" if request.auth_api_key_location == "header" else "queryParams",
                "disabled": False
            }

        return insomnia_req
