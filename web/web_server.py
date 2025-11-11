"""
Lumina Web Server
Flask 기반 REST API 서버
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import os
import sys

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project_manager import ProjectManager
from core.http_client import HttpClient
from models.request_model import RequestModel, HttpMethod, BodyType, AuthType


class LuminaWebServer:
    """Lumina 웹 서버"""

    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)  # CORS 활성화

        # 프로젝트 매니저 초기화
        self.project_manager = ProjectManager()
        self.project_manager.create_sample_project()

        # HTTP 클라이언트 초기화
        self.http_client = HttpClient(self.project_manager.env_manager)

        # 서버 스레드
        self.server_thread = None
        self.is_running = False

        # 라우트 설정
        self.setup_routes()

    def setup_routes(self):
        """라우트 설정"""

        # 메인 페이지
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # API: 프로젝트 정보
        @self.app.route('/api/project', methods=['GET'])
        def get_project():
            return jsonify({
                'name': self.project_manager.project_name,
                'folder': self.project_manager.root_folder.to_dict()
            })

        # API: 모든 요청 목록
        @self.app.route('/api/requests', methods=['GET'])
        def get_requests():
            requests = self.project_manager.get_all_requests()
            return jsonify([req.to_dict() for req in requests])

        # API: 특정 요청 조회
        @self.app.route('/api/requests/<request_id>', methods=['GET'])
        def get_request(request_id):
            req = self.project_manager.find_request_by_id(request_id)
            if req:
                return jsonify(req.to_dict())
            return jsonify({'error': 'Request not found'}), 404

        # API: 요청 생성
        @self.app.route('/api/requests', methods=['POST'])
        def create_request():
            data = request.json
            new_request = RequestModel(data.get('name', 'New Request'))
            if 'url' in data:
                new_request.url = data['url']
            if 'method' in data:
                new_request.method = HttpMethod(data['method'])

            self.project_manager.root_folder.add_request(new_request)
            return jsonify(new_request.to_dict()), 201

        # API: 요청 수정
        @self.app.route('/api/requests/<request_id>', methods=['PUT'])
        def update_request(request_id):
            req = self.project_manager.find_request_by_id(request_id)
            if not req:
                return jsonify({'error': 'Request not found'}), 404

            data = request.json

            # 업데이트
            if 'name' in data:
                req.name = data['name']
            if 'url' in data:
                req.url = data['url']
            if 'method' in data:
                req.method = HttpMethod(data['method'])
            if 'headers' in data:
                req.headers = data['headers']
            if 'params' in data:
                req.params = data['params']
            if 'body_type' in data:
                req.body_type = BodyType(data['body_type'])
            if 'body_raw' in data:
                req.body_raw = data['body_raw']
            if 'body_form' in data:
                req.body_form = data['body_form']
            if 'auth_type' in data:
                req.auth_type = AuthType(data['auth_type'])
            if 'auth_basic_username' in data:
                req.auth_basic_username = data['auth_basic_username']
            if 'auth_basic_password' in data:
                req.auth_basic_password = data['auth_basic_password']
            if 'auth_bearer_token' in data:
                req.auth_bearer_token = data['auth_bearer_token']
            if 'auth_api_key_name' in data:
                req.auth_api_key_name = data['auth_api_key_name']
            if 'auth_api_key_value' in data:
                req.auth_api_key_value = data['auth_api_key_value']
            if 'auth_api_key_location' in data:
                req.auth_api_key_location = data['auth_api_key_location']

            return jsonify(req.to_dict())

        # API: 요청 삭제
        @self.app.route('/api/requests/<request_id>', methods=['DELETE'])
        def delete_request(request_id):
            if self.project_manager.root_folder.remove_request(request_id):
                return jsonify({'success': True})
            return jsonify({'error': 'Request not found'}), 404

        # API: 요청 실행
        @self.app.route('/api/requests/<request_id>/execute', methods=['POST'])
        def execute_request(request_id):
            req = self.project_manager.find_request_by_id(request_id)
            if not req:
                return jsonify({'error': 'Request not found'}), 404

            # 요청 실행
            response = self.http_client.send_request(req)

            # 응답 변환
            return jsonify({
                'status_code': response.status_code,
                'status_text': response.status_text,
                'headers': response.headers,
                'body': response.body,
                'elapsed_ms': response.elapsed_ms,
                'size_bytes': response.size_bytes,
                'error': response.error,
                'content_type': response.content_type
            })

        # API: 환경 목록
        @self.app.route('/api/environments', methods=['GET'])
        def get_environments():
            return jsonify([env.to_dict() for env in self.project_manager.env_manager.environments])

        # API: 활성 환경
        @self.app.route('/api/environments/active', methods=['GET'])
        def get_active_environment():
            if self.project_manager.env_manager.active_environment:
                return jsonify(self.project_manager.env_manager.active_environment.to_dict())
            return jsonify(None)

        # API: 환경 설정
        @self.app.route('/api/environments/active', methods=['POST'])
        def set_active_environment():
            data = request.json
            env_id = data.get('environment_id')
            if env_id:
                self.project_manager.env_manager.set_active(env_id)
                return jsonify({'success': True})
            return jsonify({'error': 'Invalid environment ID'}), 400

        # API: 프로젝트 저장
        @self.app.route('/api/project/save', methods=['POST'])
        def save_project():
            data = request.json
            file_path = data.get('file_path', 'project.json')
            try:
                self.project_manager.save_to_file(file_path)
                return jsonify({'success': True, 'file_path': file_path})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 프로젝트 불러오기
        @self.app.route('/api/project/load', methods=['POST'])
        def load_project():
            data = request.json
            file_path = data.get('file_path')
            if not file_path:
                return jsonify({'error': 'File path required'}), 400

            try:
                self.project_manager = ProjectManager.load_from_file(file_path)
                self.http_client = HttpClient(self.project_manager.env_manager)
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 마크다운 임포트
        @self.app.route('/api/import/markdown', methods=['POST'])
        def import_markdown():
            data = request.json
            markdown_content = data.get('content')
            if not markdown_content:
                return jsonify({'error': 'Markdown content required'}), 400

            try:
                from utils.markdown_parser import MarkdownAPIParser
                imported_folder = MarkdownAPIParser.parse_content(markdown_content)
                self.project_manager.root_folder.add_folder(imported_folder)
                return jsonify({
                    'success': True,
                    'imported_count': len(imported_folder.requests),
                    'folder_name': imported_folder.name
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 마크다운 내보내기
        @self.app.route('/api/export/markdown', methods=['GET'])
        def export_markdown():
            try:
                from utils.markdown_parser import MarkdownAPIParser
                markdown_content = MarkdownAPIParser.generate_markdown(self.project_manager.root_folder)
                return jsonify({
                    'success': True,
                    'content': markdown_content,
                    'request_count': len(self.project_manager.root_folder.requests)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def start(self):
        """서버 시작 (별도 스레드에서)"""
        if self.is_running:
            return

        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"✨ Lumina Web Server started at http://{self.host}:{self.port}")

    def _run_server(self):
        """서버 실행 (내부 메서드)"""
        self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

    def stop(self):
        """서버 중지"""
        self.is_running = False
        print("Lumina Web Server stopped")


def main():
    """웹 서버 단독 실행"""
    server = LuminaWebServer(host='0.0.0.0', port=5000)
    print(f"✨ Starting Lumina Web Server...")
    print(f"Access at: http://localhost:5000")
    server.app.run(host=server.host, port=server.port, debug=True)


if __name__ == '__main__':
    main()
