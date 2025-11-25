"""
Postman Import/Export Converter
Postman Collection 형식과 Lumina 형식 간 변환
"""
import uuid
from typing import Dict, List, Any, Optional
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType


class PostmanConverter:
    """Postman Collection 형식 변환기"""

    @staticmethod
    def import_from_postman(postman_data: Dict[str, Any]) -> RequestFolder:
        """
        Postman Collection JSON 데이터를 Lumina RequestFolder로 변환

        Args:
            postman_data: Postman Collection JSON

        Returns:
            RequestFolder: 변환된 폴더
        """
        info = postman_data.get('info', {})
        collection_name = info.get('name', 'Imported from Postman')

        root_folder = RequestFolder(collection_name)

        # Collection의 item들을 처리
        items = postman_data.get('item', [])
        PostmanConverter._process_items(items, root_folder)

        return root_folder

    @staticmethod
    def _process_items(items: List[Dict[str, Any]], parent_folder: RequestFolder):
        """Postman item들을 재귀적으로 처리"""
        for item in items:
            # item이 폴더인지 요청인지 확인
            if 'item' in item:
                # 폴더 (하위 item이 있음)
                folder = RequestFolder(item.get('name', 'Unnamed Folder'))
                parent_folder.add_folder(folder)

                # 하위 아이템 재귀 처리
                PostmanConverter._process_items(item['item'], folder)
            else:
                # 요청
                request = PostmanConverter._convert_postman_request(item)
                parent_folder.add_request(request)

    @staticmethod
    def _convert_postman_request(postman_item: Dict[str, Any]) -> RequestModel:
        """Postman request를 Lumina RequestModel로 변환"""
        request = RequestModel(postman_item.get('name', 'Unnamed Request'))

        # request 객체 가져오기
        req = postman_item.get('request', {})

        # URL 처리
        url = req.get('url', '')
        if isinstance(url, dict):
            # URL이 객체로 되어있는 경우
            raw_url = url.get('raw', '')
            request.url = raw_url

            # Query parameters
            query_params = url.get('query', [])
            if isinstance(query_params, list):
                request.params = {
                    q.get('key', ''): q.get('value', '')
                    for q in query_params
                    if q.get('key') and not q.get('disabled', False)
                }
        else:
            # URL이 문자열인 경우
            request.url = str(url)

        # Method
        method_str = req.get('method', 'GET').upper()
        try:
            request.method = HttpMethod[method_str]
        except KeyError:
            request.method = HttpMethod.GET

        # Headers
        headers = req.get('header', [])
        if isinstance(headers, list):
            request.headers = {
                h.get('key', ''): h.get('value', '')
                for h in headers
                if h.get('key') and not h.get('disabled', False)
            }

        # Body
        body = req.get('body', {})
        if body:
            body_mode = body.get('mode', '')

            if body_mode == 'raw':
                request.body_type = BodyType.RAW
                request.body_raw = body.get('raw', '')
            elif body_mode == 'urlencoded':
                request.body_type = BodyType.FORM_URLENCODED
                urlencoded = body.get('urlencoded', [])
                if isinstance(urlencoded, list):
                    request.body_form = {
                        p.get('key', ''): p.get('value', '')
                        for p in urlencoded
                        if p.get('key') and not p.get('disabled', False)
                    }
            elif body_mode == 'formdata':
                request.body_type = BodyType.FORM_DATA
                formdata = body.get('formdata', [])
                if isinstance(formdata, list):
                    request.body_form = {
                        p.get('key', ''): p.get('value', '')
                        for p in formdata
                        if p.get('key') and p.get('type') != 'file' and not p.get('disabled', False)
                    }

        # Authentication
        auth = req.get('auth', {})
        if auth:
            auth_type = auth.get('type', '').lower()

            if auth_type == 'basic':
                request.auth_type = AuthType.BASIC
                basic = auth.get('basic', [])
                auth_dict = {item.get('key'): item.get('value') for item in basic}
                request.auth_basic_username = auth_dict.get('username', '')
                request.auth_basic_password = auth_dict.get('password', '')
            elif auth_type == 'bearer':
                request.auth_type = AuthType.BEARER
                bearer = auth.get('bearer', [])
                auth_dict = {item.get('key'): item.get('value') for item in bearer}
                request.auth_bearer_token = auth_dict.get('token', '')
            elif auth_type == 'apikey':
                request.auth_type = AuthType.API_KEY
                apikey = auth.get('apikey', [])
                auth_dict = {item.get('key'): item.get('value') for item in apikey}
                request.auth_api_key_name = auth_dict.get('key', '')
                request.auth_api_key_value = auth_dict.get('value', '')
                in_location = auth_dict.get('in', 'header')
                request.auth_api_key_location = 'header' if in_location == 'header' else 'query'

        # Description
        description = postman_item.get('request', {}).get('description', '')
        if description:
            request.documentation = description

        return request

    @staticmethod
    def export_to_postman(folder: RequestFolder) -> Dict[str, Any]:
        """
        Lumina RequestFolder를 Postman Collection JSON 형식으로 변환

        Args:
            folder: 변환할 폴더

        Returns:
            Dict: Postman Collection JSON
        """
        collection = {
            "info": {
                "_postman_id": str(uuid.uuid4()),
                "name": folder.name,
                "description": "Exported from Lumina",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }

        # 재귀적으로 폴더와 요청 변환
        PostmanConverter._export_items(folder, collection['item'])

        return collection

    @staticmethod
    def _export_items(folder: RequestFolder, items: List[Dict[str, Any]]):
        """재귀적으로 폴더와 요청을 Postman item으로 변환"""
        # 요청 변환
        for request in folder.requests:
            item = PostmanConverter._convert_to_postman_request(request)
            items.append(item)

        # 하위 폴더 변환
        for sub_folder in folder.folders:
            folder_item = {
                "name": sub_folder.name,
                "item": []
            }
            PostmanConverter._export_items(sub_folder, folder_item['item'])
            items.append(folder_item)

    @staticmethod
    def _convert_to_postman_request(request: RequestModel) -> Dict[str, Any]:
        """Lumina RequestModel을 Postman request로 변환"""
        postman_req = {
            "name": request.name,
            "request": {
                "method": request.method.value,
                "header": [],
                "url": {
                    "raw": request.url,
                    "protocol": "",
                    "host": [],
                    "path": [],
                    "query": []
                }
            },
            "response": []
        }

        # Headers
        postman_req['request']['header'] = [
            {"key": key, "value": value, "type": "text"}
            for key, value in request.headers.items()
        ]

        # Query Parameters
        if request.params:
            postman_req['request']['url']['query'] = [
                {"key": key, "value": value}
                for key, value in request.params.items()
            ]

        # Body
        if request.body_type == BodyType.RAW and request.body_raw:
            postman_req['request']['body'] = {
                "mode": "raw",
                "raw": request.body_raw,
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        elif request.body_type == BodyType.FORM_URLENCODED:
            postman_req['request']['body'] = {
                "mode": "urlencoded",
                "urlencoded": [
                    {"key": key, "value": value, "type": "text"}
                    for key, value in request.body_form.items()
                ]
            }
        elif request.body_type == BodyType.FORM_DATA:
            postman_req['request']['body'] = {
                "mode": "formdata",
                "formdata": [
                    {"key": key, "value": value, "type": "text"}
                    for key, value in request.body_form.items()
                ]
            }

        # Authentication
        if request.auth_type == AuthType.BASIC:
            postman_req['request']['auth'] = {
                "type": "basic",
                "basic": [
                    {"key": "username", "value": request.auth_basic_username, "type": "string"},
                    {"key": "password", "value": request.auth_basic_password, "type": "string"}
                ]
            }
        elif request.auth_type == AuthType.BEARER:
            postman_req['request']['auth'] = {
                "type": "bearer",
                "bearer": [
                    {"key": "token", "value": request.auth_bearer_token, "type": "string"}
                ]
            }
        elif request.auth_type == AuthType.API_KEY:
            postman_req['request']['auth'] = {
                "type": "apikey",
                "apikey": [
                    {"key": "key", "value": request.auth_api_key_name, "type": "string"},
                    {"key": "value", "value": request.auth_api_key_value, "type": "string"},
                    {"key": "in", "value": request.auth_api_key_location, "type": "string"}
                ]
            }

        # Description
        if request.documentation:
            postman_req['request']['description'] = request.documentation

        return postman_req
