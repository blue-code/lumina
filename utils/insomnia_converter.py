"""
Insomnia Import/Export Converter
Insomnia 형식과 Lumina 형식 간 변환
"""
import uuid
from typing import Dict, List, Any
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType


class InsomniaConverter:
    """Insomnia 형식 변환기"""

    @staticmethod
    def import_from_insomnia(insomnia_data: Dict[str, Any]) -> RequestFolder:
        """
        Insomnia JSON 데이터를 Lumina RequestFolder로 변환

        Args:
            insomnia_data: Insomnia export JSON

        Returns:
            RequestFolder: 변환된 폴더
        """
        resources = insomnia_data.get('resources', [])

        # ID 매핑 (Insomnia ID -> Lumina 객체)
        id_mapping = {}

        # 폴더 먼저 생성
        folders = {}
        root_folder = RequestFolder("Imported from Insomnia")
        folders['__root__'] = root_folder

        # 폴더 생성
        for resource in resources:
            if resource.get('_type') == 'request_group':
                folder = RequestFolder(resource.get('name', 'Unnamed Folder'))
                folder.id = resource.get('_id', str(uuid.uuid4()))
                id_mapping[resource['_id']] = folder
                folders[resource['_id']] = folder

        # 요청 생성 및 폴더에 할당
        for resource in resources:
            if resource.get('_type') == 'request':
                request = InsomniaConverter._convert_insomnia_request(resource)

                # 부모 폴더 찾기
                parent_id = resource.get('parentId', '__root__')
                parent_folder = folders.get(parent_id, root_folder)
                parent_folder.add_request(request)

        # 폴더 계층 구조 구성
        for resource in resources:
            if resource.get('_type') == 'request_group':
                folder_id = resource['_id']
                parent_id = resource.get('parentId', '__root__')

                if folder_id in folders:
                    folder = folders[folder_id]
                    parent = folders.get(parent_id, root_folder)
                    if folder != parent:  # 자기 자신이 아닌 경우만
                        parent.add_folder(folder)

        return root_folder

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

        # Headers
        headers = insomnia_req.get('headers', [])
        if isinstance(headers, list):
            request.headers = {h.get('name', ''): h.get('value', '') for h in headers if h.get('name')}

        # Parameters (query params)
        parameters = insomnia_req.get('parameters', [])
        if isinstance(parameters, list):
            request.params = {p.get('name', ''): p.get('value', '') for p in parameters if p.get('name')}

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
                    request.body_form = {p.get('name', ''): p.get('value', '') for p in params if p.get('name')}
            elif mime_type == 'multipart/form-data':
                request.body_type = BodyType.FORM_DATA
                params = body.get('params', [])
                if isinstance(params, list):
                    request.body_form = {p.get('name', ''): p.get('value', '') for p in params if p.get('name')}
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
    def export_to_insomnia(folder: RequestFolder) -> Dict[str, Any]:
        """
        Lumina RequestFolder를 Insomnia JSON 형식으로 변환

        Args:
            folder: 변환할 폴더

        Returns:
            Dict: Insomnia export JSON
        """
        resources = []

        # 재귀적으로 폴더와 요청 변환
        InsomniaConverter._export_folder_recursive(folder, resources, None)

        return {
            "_type": "export",
            "__export_format": 4,
            "__export_date": None,
            "__export_source": "lumina",
            "resources": resources
        }

    @staticmethod
    def _export_folder_recursive(folder: RequestFolder, resources: List[Dict], parent_id: str = None):
        """재귀적으로 폴더와 요청을 Insomnia 형식으로 변환"""
        # 루트 폴더가 아닌 경우 폴더 자체를 추가
        current_parent_id = parent_id
        if folder.name != "Root":
            folder_resource = {
                "_type": "request_group",
                "_id": folder.id,
                "name": folder.name,
                "parentId": parent_id,
                "environment": {},
                "environmentPropertyOrder": None,
                "metaSortKey": -1
            }
            resources.append(folder_resource)
            current_parent_id = folder.id

        # 요청 변환
        for request in folder.requests:
            request_resource = InsomniaConverter._convert_to_insomnia_request(request, current_parent_id)
            resources.append(request_resource)

        # 하위 폴더 재귀 처리
        for sub_folder in folder.folders:
            InsomniaConverter._export_folder_recursive(sub_folder, resources, current_parent_id)

    @staticmethod
    def _convert_to_insomnia_request(request: RequestModel, parent_id: str = None) -> Dict[str, Any]:
        """Lumina RequestModel을 Insomnia 요청으로 변환"""
        insomnia_req = {
            "_type": "request",
            "_id": request.id,
            "parentId": parent_id,
            "name": request.name,
            "url": request.url,
            "method": request.method.value,
            "headers": [],
            "parameters": [],
            "body": {},
            "authentication": {},
            "metaSortKey": -1,
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
            {"name": key, "value": value, "disabled": False}
            for key, value in request.headers.items()
        ]

        # Parameters
        insomnia_req['parameters'] = [
            {"name": key, "value": value, "disabled": False}
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
                    {"name": key, "value": value, "disabled": False}
                    for key, value in request.body_form.items()
                ]
            }
        elif request.body_type == BodyType.FORM_DATA:
            insomnia_req['body'] = {
                "mimeType": "multipart/form-data",
                "params": [
                    {"name": key, "value": value, "disabled": False, "type": "text"}
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
