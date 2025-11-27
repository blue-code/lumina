"""
OpenAPI (Swagger) Import Converter
OpenAPI 3.0 YAML/JSON 형식과 Lumina 형식 간 변환
"""
import yaml
import json
from typing import Dict, List, Any, Optional
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType


class OpenAPIConverter:
    """OpenAPI Specification 형식 변환기"""

    @staticmethod
    def import_from_file(file_path: str) -> RequestFolder:
        """
        OpenAPI 파일(YAML/JSON)을 Lumina RequestFolder로 변환

        Args:
            file_path: 파일 경로

        Returns:
            RequestFolder: 변환된 폴더
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return OpenAPIConverter.import_from_content(content)

    @staticmethod
    def import_from_content(content: str) -> RequestFolder:
        """
        OpenAPI 내용(YAML/JSON 문자열)을 Lumina RequestFolder로 변환
        
        Args:
            content: YAML 또는 JSON 문자열
            
        Returns:
            RequestFolder: 변환된 폴더
        """
        # YAML/JSON 파싱
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError:
            # YAML 파싱 실패 시 JSON으로 시도
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError("Invalid OpenAPI content format. Must be YAML or JSON.")

        return OpenAPIConverter._parse_openapi_data(data)

    @staticmethod
    def _parse_openapi_data(data: Dict[str, Any]) -> RequestFolder:
        """OpenAPI 데이터를 파싱하여 RequestFolder 생성"""
        info = data.get('info', {})
        title = info.get('title', 'Imported API')
        
        root_folder = RequestFolder(title)
        
        # 서버 URL (기본 URL)
        servers = data.get('servers', [])
        base_url = servers[0].get('url', '') if servers else ''
        
        # 태그별 폴더 생성을 위한 맵
        folder_map: Dict[str, RequestFolder] = {}
        
        paths = data.get('paths', {})
        for path, operations in paths.items():
            for method_str, operation in operations.items():
                if method_str.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    continue
                    
                # 요청 모델 생성
                request = OpenAPIConverter._create_request(
                    base_url, path, method_str, operation, data.get('components', {})
                )
                
                # 태그 확인 (폴더링)
                tags = operation.get('tags', [])
                if tags:
                    tag_name = tags[0] # 첫 번째 태그를 폴더명으로 사용
                    if tag_name not in folder_map:
                        folder = RequestFolder(tag_name)
                        folder_map[tag_name] = folder
                        root_folder.add_folder(folder)
                    
                    folder_map[tag_name].add_request(request)
                else:
                    # 태그가 없으면 루트에 추가
                    root_folder.add_request(request)
                    
        return root_folder

    @staticmethod
    def _create_request(base_url: str, path: str, method: str, operation: Dict[str, Any], components: Dict[str, Any]) -> RequestModel:
        """개별 요청 생성"""
        summary = operation.get('summary', operation.get('operationId', 'Unnamed Request'))
        request = RequestModel(summary)
        
        # URL 설정
        full_url = base_url.rstrip('/') + '/' + path.lstrip('/')
        request.url = full_url
        
        # Method 설정
        try:
            request.method = HttpMethod[method.upper()]
        except KeyError:
            request.method = HttpMethod.GET
            
        # Documentation
        request.documentation = operation.get('description', '')
        
        # Parameters (Header, Query)
        parameters = operation.get('parameters', [])
        for param in parameters:
            # $ref 처리 (간단하게 components 참조 확인)
            if '$ref' in param:
                ref_key = param['$ref'].split('/')[-1]
                if 'parameters' in components and ref_key in components['parameters']:
                    param = components['parameters'][ref_key]
            
            name = param.get('name')
            in_loc = param.get('in')
            # schema = param.get('schema', {})
            # example = schema.get('example', '') # 스키마 예제
            example = param.get('example', '') # 파라미터 직접 예제
            
            if not example and 'schema' in param:
                 example = param['schema'].get('example', '')

            if in_loc == 'header':
                request.headers[name] = str(example)
            elif in_loc == 'query':
                request.params[name] = str(example)
                
        # Request Body
        request_body = operation.get('requestBody', {})
        content = request_body.get('content', {})
        
        if 'application/json' in content:
            request.body_type = BodyType.RAW
            schema = content['application/json'].get('schema', {})
            
            # 예제 생성 로직 (간소화)
            example_body = OpenAPIConverter._generate_example_from_schema(schema, components)
            request.body_raw = json.dumps(example_body, indent=2, ensure_ascii=False)
            
            request.headers['Content-Type'] = 'application/json'
            
        elif 'application/x-www-form-urlencoded' in content:
            request.body_type = BodyType.FORM_URLENCODED
            schema = content['application/x-www-form-urlencoded'].get('schema', {})
            props = schema.get('properties', {})
            for key, prop in props.items():
                request.body_form[key] = str(prop.get('example', prop.get('default', '')))
                
            request.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        elif 'multipart/form-data' in content:
            request.body_type = BodyType.FORM_DATA
            schema = content['multipart/form-data'].get('schema', {})
            props = schema.get('properties', {})
            for key, prop in props.items():
                request.body_form[key] = str(prop.get('example', prop.get('default', '')))
            
            # Content-Type 헤더는 클라이언트가 자동으로 설정하게 둠 (boundary 때문에)
            # request.headers['Content-Type'] = 'multipart/form-data'

        return request

    @staticmethod
    def _generate_example_from_schema(schema: Dict[str, Any], components: Dict[str, Any]) -> Any:
        """스키마로부터 예제 데이터 생성"""
        if '$ref' in schema:
            ref_key = schema['$ref'].split('/')[-1]
            if 'schemas' in components and ref_key in components['schemas']:
                return OpenAPIConverter._generate_example_from_schema(components['schemas'][ref_key], components)
            return {}
            
        if 'example' in schema:
            return schema['example']
            
        schema_type = schema.get('type')
        
        if schema_type == 'object':
            result = {}
            properties = schema.get('properties', {})
            for key, prop in properties.items():
                result[key] = OpenAPIConverter._generate_example_from_schema(prop, components)
            return result
            
        elif schema_type == 'array':
            items = schema.get('items', {})
            return [OpenAPIConverter._generate_example_from_schema(items, components)]
            
        elif schema_type == 'string':
            return "string"
        elif schema_type == 'integer' or schema_type == 'number':
            return 0
        elif schema_type == 'boolean':
            return False
            
        return None
