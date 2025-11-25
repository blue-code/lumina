"""
Lumina Web Server
Flask 기반 REST API 서버 - Thread-safe with session isolation
"""
from flask import Flask, render_template, jsonify, request, session
from flask_cors import CORS
import threading
import os
import sys
import uuid
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project_manager import ProjectManager
from core.http_client import HttpClient
from core.share_manager import ShareManager
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType, AuthType
from models.history_model import HistoryManager


class LuminaWebServer:
    """Lumina 웹 서버 - 세션별 프로젝트 격리"""

    def __init__(self, host='127.0.0.1', port=15555):
        self.host = host
        self.port = port
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app, supports_credentials=True)  # CORS with credentials

        # 세션 설정 (보안 강화)
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['SESSION_TYPE'] = 'filesystem'
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

        # 데이터 디렉토리 설정
        self.data_dir = Path('.lumina_data')
        self.data_dir.mkdir(exist_ok=True)

        # 세션별 프로젝트 매니저 저장소 (thread-safe)
        # 구조: {session_id: {project_id: ProjectManager}}
        self.sessions: Dict[str, Dict[str, ProjectManager]] = {}
        self.sessions_lock = threading.RLock()

        # 세션별 활성 프로젝트 ID
        self.active_projects: Dict[str, str] = {}

        # 세션별 히스토리 매니저 저장소
        # 구조: {session_id: {project_id: HistoryManager}}
        self.histories: Dict[str, Dict[str, HistoryManager]] = {}

        # 세션 메타데이터 (마지막 접근 시간)
        self.session_metadata: Dict[str, Dict] = {}

        # 레거시 지원: 데스크톱 앱과의 공유를 위한 기본 프로젝트 (옵션)
        self.project_manager = None  # Will be set by desktop app if needed
        self.http_client = None
        self.history_manager = None  # Shared history for desktop mode

        # 공유 관리자
        self.share_manager = ShareManager()

        # 서버 스레드
        self.server_thread = None
        self.is_running = False

        # 자동 저장/정리 타이머
        self.auto_save_timer = None
        self.cleanup_timer = None

        # 기존 세션 데이터 로드
        self.load_all_sessions()

        # 라우트 설정
        self.setup_routes()

        # 자동 저장 및 정리 시작
        self.start_auto_save()
        self.start_cleanup_timer()

    def get_session_project_manager(self) -> ProjectManager:
        """현재 세션의 활성 프로젝트 매니저 가져오기 (없으면 생성)"""
        # 데스크톱 앱에서 공유 모드일 경우
        if self.project_manager is not None:
            return self.project_manager

        # 세션별 격리 모드
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        session_id = session['session_id']

        # 세션 접근 시간 업데이트
        self.update_session_access_time(session_id)

        with self.sessions_lock:
            # 세션 초기화
            if session_id not in self.sessions:
                self.sessions[session_id] = {}

            # 활성 프로젝트 ID 가져오기
            if session_id not in self.active_projects or self.active_projects[session_id] not in self.sessions[session_id]:
                # 기본 프로젝트 생성
                default_project_id = str(uuid.uuid4())
                pm = ProjectManager()
                pm.project_name = "Default Project"
                pm.create_sample_project()
                self.sessions[session_id][default_project_id] = pm
                self.active_projects[session_id] = default_project_id

            active_project_id = self.active_projects[session_id]
            return self.sessions[session_id][active_project_id]

    def get_session_http_client(self) -> HttpClient:
        """현재 세션의 HTTP 클라이언트 가져오기"""
        # 데스크톱 앱에서 공유 모드일 경우
        if self.http_client is not None:
            return self.http_client

        # 세션별 HTTP 클라이언트 생성
        pm = self.get_session_project_manager()
        return HttpClient(pm.env_manager)

    def get_session_history_manager(self) -> HistoryManager:
        """현재 세션의 활성 프로젝트 히스토리 매니저 가져오기"""
        # 데스크톱 앱에서 공유 모드일 경우
        if self.history_manager is not None:
            return self.history_manager

        # 세션별 히스토리 매니저
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

        session_id = session['session_id']

        with self.sessions_lock:
            # 세션 초기화
            if session_id not in self.histories:
                self.histories[session_id] = {}

            # 활성 프로젝트 ID 가져오기 (없으면 기본 프로젝트 생성됨)
            if session_id not in self.active_projects:
                self.get_session_project_manager()

            active_project_id = self.active_projects[session_id]

            # 프로젝트별 히스토리 매니저 생성
            if active_project_id not in self.histories[session_id]:
                self.histories[session_id][active_project_id] = HistoryManager()

            return self.histories[session_id][active_project_id]

    def save_session(self, session_id: str):
        """세션 데이터를 파일로 저장"""
        with self.sessions_lock:
            if session_id not in self.sessions:
                return

            session_file = self.data_dir / f'session_{session_id}.json'

            try:
                # 세션 데이터 직렬화
                session_data = {
                    'session_id': session_id,
                    'last_accessed': time.time(),
                    'active_project_id': self.active_projects.get(session_id),
                    'projects': {}
                }

                # 모든 프로젝트 저장
                for project_id, pm in self.sessions[session_id].items():
                    session_data['projects'][project_id] = pm.to_dict()

                # 파일로 저장
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)

            except Exception as e:
                print(f"Failed to save session {session_id}: {e}")

    def load_session(self, session_id: str) -> bool:
        """세션 데이터를 파일에서 로드"""
        session_file = self.data_dir / f'session_{session_id}.json'

        if not session_file.exists():
            return False

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            with self.sessions_lock:
                # 세션 초기화
                if session_id not in self.sessions:
                    self.sessions[session_id] = {}

                # 프로젝트 복원
                for project_id, project_data in session_data['projects'].items():
                    pm = ProjectManager.from_dict(project_data)
                    self.sessions[session_id][project_id] = pm

                # 활성 프로젝트 설정
                active_id = session_data.get('active_project_id')
                if active_id and active_id in self.sessions[session_id]:
                    self.active_projects[session_id] = active_id

                # 메타데이터 저장
                self.session_metadata[session_id] = {
                    'last_accessed': session_data.get('last_accessed', time.time())
                }

            return True
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return False

    def load_all_sessions(self):
        """모든 저장된 세션 데이터 로드"""
        if not self.data_dir.exists():
            return

        session_files = self.data_dir.glob('session_*.json')
        loaded_count = 0

        for session_file in session_files:
            session_id = session_file.stem.replace('session_', '')
            if self.load_session(session_id):
                loaded_count += 1

        if loaded_count > 0:
            print(f"✨ Loaded {loaded_count} session(s) from disk")

    def save_all_sessions(self):
        """모든 세션 데이터 저장"""
        with self.sessions_lock:
            for session_id in list(self.sessions.keys()):
                self.save_session(session_id)

    def cleanup_old_sessions(self):
        """30일 이상 미사용 세션 정리"""
        cutoff_time = time.time() - (30 * 24 * 60 * 60)  # 30일

        with self.sessions_lock:
            sessions_to_remove = []

            for session_id, metadata in self.session_metadata.items():
                last_accessed = metadata.get('last_accessed', 0)
                if last_accessed < cutoff_time:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                # 메모리에서 제거
                if session_id in self.sessions:
                    del self.sessions[session_id]
                if session_id in self.active_projects:
                    del self.active_projects[session_id]
                if session_id in self.histories:
                    del self.histories[session_id]
                if session_id in self.session_metadata:
                    del self.session_metadata[session_id]

                # 파일 삭제
                session_file = self.data_dir / f'session_{session_id}.json'
                if session_file.exists():
                    session_file.unlink()

            if sessions_to_remove:
                print(f"🧹 Cleaned up {len(sessions_to_remove)} old session(s)")

    def start_auto_save(self):
        """자동 저장 타이머 시작 (30초마다)"""
        def auto_save():
            while self.is_running:
                time.sleep(30)
                self.save_all_sessions()

        self.auto_save_timer = threading.Thread(target=auto_save, daemon=True)
        self.auto_save_timer.start()

    def start_cleanup_timer(self):
        """세션 정리 타이머 시작 (1시간마다)"""
        def cleanup():
            while self.is_running:
                time.sleep(3600)  # 1시간
                self.cleanup_old_sessions()

        self.cleanup_timer = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_timer.start()

    def update_session_access_time(self, session_id: str):
        """세션 마지막 접근 시간 업데이트"""
        self.session_metadata.setdefault(session_id, {})['last_accessed'] = time.time()

    def setup_routes(self):
        """라우트 설정"""

        # 메인 페이지
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # API 문서 페이지
        @self.app.route('/docs')
        def api_docs():
            return render_template('api_docs.html')

        # API: 프로젝트 정보
        @self.app.route('/api/project', methods=['GET'])
        def get_project():
            pm = self.get_session_project_manager()
            return jsonify({
                'name': pm.project_name,
                'folder': pm.root_folder.to_dict()
            })

        # API: 모든 요청 목록
        @self.app.route('/api/requests', methods=['GET'])
        def get_requests():
            pm = self.get_session_project_manager()
            requests = pm.get_all_requests()
            return jsonify([req.to_dict() for req in requests])

        # API: 특정 요청 조회
        @self.app.route('/api/requests/<request_id>', methods=['GET'])
        def get_request(request_id):
            pm = self.get_session_project_manager()
            req = pm.find_request_by_id(request_id)
            if req:
                return jsonify(req.to_dict())
            return jsonify({'error': 'Request not found'}), 404

        # API: 요청 생성
        @self.app.route('/api/requests', methods=['POST'])
        def create_request():
            pm = self.get_session_project_manager()
            data = request.json
            new_request = RequestModel(data.get('name', 'New Request'))
            if 'url' in data:
                new_request.url = data['url']
            if 'method' in data:
                new_request.method = HttpMethod(data['method'])

            pm.root_folder.add_request(new_request)
            return jsonify(new_request.to_dict()), 201

        # API: 요청 수정
        @self.app.route('/api/requests/<request_id>', methods=['PUT'])
        def update_request(request_id):
            pm = self.get_session_project_manager()
            req = pm.find_request_by_id(request_id)
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
            if 'documentation' in data:
                req.documentation = data['documentation']

            return jsonify(req.to_dict())

        # API: 요청 삭제
        @self.app.route('/api/requests/<request_id>', methods=['DELETE'])
        def delete_request(request_id):
            pm = self.get_session_project_manager()
            if pm.root_folder.remove_request(request_id):
                return jsonify({'success': True})
            return jsonify({'error': 'Request not found'}), 404

        # API: 요청 실행
        @self.app.route('/api/requests/<request_id>/execute', methods=['POST'])
        def execute_request(request_id):
            pm = self.get_session_project_manager()
            http_client = self.get_session_http_client()
            history_mgr = self.get_session_history_manager()
            req = pm.find_request_by_id(request_id)
            if not req:
                return jsonify({'error': 'Request not found'}), 404

            # 요청 실행
            response = http_client.send_request(req)

            # 히스토리에 저장
            history_mgr.add_entry(req, response)

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
            pm = self.get_session_project_manager()
            return jsonify([env.to_dict() for env in pm.env_manager.environments])

        # API: 활성 환경
        @self.app.route('/api/environments/active', methods=['GET'])
        def get_active_environment():
            pm = self.get_session_project_manager()
            if pm.env_manager.active_environment:
                return jsonify(pm.env_manager.active_environment.to_dict())
            return jsonify(None)

        # API: 환경 설정
        @self.app.route('/api/environments/active', methods=['POST'])
        def set_active_environment():
            pm = self.get_session_project_manager()
            data = request.json
            env_id = data.get('environment_id')
            if env_id:
                pm.env_manager.set_active(env_id)
                return jsonify({'success': True})
            return jsonify({'error': 'Invalid environment ID'}), 400

        # API: Global Constants 조회
        @self.app.route('/api/global-constants', methods=['GET'])
        def get_global_constants():
            pm = self.get_session_project_manager()
            return jsonify(pm.env_manager.global_environment.to_dict())

        # API: Global Constants 업데이트
        @self.app.route('/api/global-constants', methods=['POST'])
        def update_global_constants():
            pm = self.get_session_project_manager()
            data = request.json
            constants = data.get('constants', {})

            # 기존 변수 모두 삭제하고 새로운 것으로 교체
            pm.env_manager.global_environment.variables = constants
            return jsonify({'success': True})

        # API: 프로젝트 저장
        @self.app.route('/api/project/save', methods=['POST'])
        def save_project():
            pm = self.get_session_project_manager()
            data = request.json
            file_path = data.get('file_path', 'project.json')
            try:
                pm.save_to_file(file_path)
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
                pm = ProjectManager.load_from_file(file_path)
                # 세션에 저장
                if 'session_id' not in session:
                    session['session_id'] = str(uuid.uuid4())
                session_id = session['session_id']

                with self.sessions_lock:
                    # 새 프로젝트로 추가
                    project_id = str(uuid.uuid4())
                    if session_id not in self.sessions:
                        self.sessions[session_id] = {}
                    self.sessions[session_id][project_id] = pm
                    self.active_projects[session_id] = project_id

                return jsonify({
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': pm.project_name
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: Insomnia 임포트
        @self.app.route('/api/import/insomnia', methods=['POST'])
        def import_insomnia():
            pm = self.get_session_project_manager()
            data = request.json
            insomnia_data = data.get('data')
            if not insomnia_data:
                return jsonify({'error': 'Insomnia data required'}), 400

            try:
                from utils.insomnia_converter import InsomniaConverter
                imported_folder = InsomniaConverter.import_from_insomnia(insomnia_data)

                # 폴더 추가
                pm.root_folder.add_folder(imported_folder)

                # 모든 요청 개수 계산
                all_requests = pm.get_all_requests()

                return jsonify({
                    'success': True,
                    'imported_count': len(imported_folder.requests),
                    'folder_name': imported_folder.name
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: Insomnia 내보내기
        @self.app.route('/api/export/insomnia', methods=['GET'])
        def export_insomnia():
            pm = self.get_session_project_manager()
            try:
                from utils.insomnia_converter import InsomniaConverter
                insomnia_data = InsomniaConverter.export_to_insomnia(pm.root_folder)
                return jsonify({
                    'success': True,
                    'data': insomnia_data,
                    'request_count': len(pm.get_all_requests())
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: Postman 임포트
        @self.app.route('/api/import/postman', methods=['POST'])
        def import_postman():
            pm = self.get_session_project_manager()
            data = request.json
            postman_data = data.get('data')
            if not postman_data:
                return jsonify({'error': 'Postman data required'}), 400

            try:
                from utils.postman_converter import PostmanConverter
                imported_folder = PostmanConverter.import_from_postman(postman_data)

                # 폴더 추가
                pm.root_folder.add_folder(imported_folder)

                # 모든 요청 개수 계산
                all_requests = pm.get_all_requests()

                return jsonify({
                    'success': True,
                    'imported_count': len(imported_folder.requests),
                    'folder_name': imported_folder.name
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: Postman 내보내기
        @self.app.route('/api/export/postman', methods=['GET'])
        def export_postman():
            pm = self.get_session_project_manager()
            try:
                from utils.postman_converter import PostmanConverter
                postman_data = PostmanConverter.export_to_postman(pm.root_folder)
                return jsonify({
                    'success': True,
                    'data': postman_data,
                    'request_count': len(pm.get_all_requests())
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 히스토리 조회
        @self.app.route('/api/history/<request_id>', methods=['GET'])
        def get_history(request_id):
            history_mgr = self.get_session_history_manager()
            limit = request.args.get('limit', 20, type=int)
            history = history_mgr.get_history(request_id, limit)
            return jsonify({
                'success': True,
                'request_id': request_id,
                'count': len(history),
                'history': history
            })

        # API: 전체 히스토리 조회
        @self.app.route('/api/history', methods=['GET'])
        def get_all_history():
            history_mgr = self.get_session_history_manager()
            all_history = history_mgr.get_all_histories()
            return jsonify({
                'success': True,
                'histories': all_history
            })

        # API: 히스토리 삭제
        @self.app.route('/api/history/<request_id>', methods=['DELETE'])
        def clear_history(request_id):
            history_mgr = self.get_session_history_manager()
            history_mgr.clear_history(request_id)
            return jsonify({'success': True})

        # API: 전체 히스토리 삭제
        @self.app.route('/api/history', methods=['DELETE'])
        def clear_all_history():
            history_mgr = self.get_session_history_manager()
            history_mgr.clear_history()
            return jsonify({'success': True})

        # ======================
        # 프로젝트 관리 API
        # ======================

        # API: 모든 프로젝트 목록 조회
        @self.app.route('/api/projects', methods=['GET'])
        def get_projects():
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id not in self.sessions:
                    self.sessions[session_id] = {}

                projects = []
                for project_id, pm in self.sessions[session_id].items():
                    projects.append({
                        'id': project_id,
                        'name': pm.project_name,
                        'is_active': self.active_projects.get(session_id) == project_id
                    })

                return jsonify({
                    'success': True,
                    'projects': projects
                })

        # API: 활성 프로젝트 조회
        @self.app.route('/api/projects/active', methods=['GET'])
        def get_active_project():
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id in self.active_projects:
                    active_id = self.active_projects[session_id]
                    if active_id in self.sessions.get(session_id, {}):
                        pm = self.sessions[session_id][active_id]
                        return jsonify({
                            'success': True,
                            'project': {
                                'id': active_id,
                                'name': pm.project_name
                            }
                        })

                return jsonify({
                    'success': True,
                    'project': None
                })

        # API: 새 프로젝트 생성
        @self.app.route('/api/projects', methods=['POST'])
        def create_project():
            data = request.json
            project_name = data.get('name', 'New Project')

            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id not in self.sessions:
                    self.sessions[session_id] = {}

                # 새 프로젝트 생성
                project_id = str(uuid.uuid4())
                pm = ProjectManager()
                pm.project_name = project_name
                self.sessions[session_id][project_id] = pm

                return jsonify({
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': pm.project_name
                    }
                }), 201

        # API: 프로젝트 이름 변경
        @self.app.route('/api/projects/<project_id>', methods=['PUT'])
        def update_project(project_id):
            data = request.json
            new_name = data.get('name')

            if not new_name:
                return jsonify({'error': 'Project name required'}), 400

            if 'session_id' not in session:
                return jsonify({'error': 'Session not found'}), 404

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id not in self.sessions or project_id not in self.sessions[session_id]:
                    return jsonify({'error': 'Project not found'}), 404

                pm = self.sessions[session_id][project_id]
                pm.project_name = new_name

                return jsonify({
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': pm.project_name
                    }
                })

        # API: 프로젝트 삭제
        @self.app.route('/api/projects/<project_id>', methods=['DELETE'])
        def delete_project(project_id):
            if 'session_id' not in session:
                return jsonify({'error': 'Session not found'}), 404

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id not in self.sessions or project_id not in self.sessions[session_id]:
                    return jsonify({'error': 'Project not found'}), 404

                # 프로젝트 삭제
                del self.sessions[session_id][project_id]

                # 히스토리도 삭제
                if session_id in self.histories and project_id in self.histories[session_id]:
                    del self.histories[session_id][project_id]

                # 활성 프로젝트였다면 다른 프로젝트로 전환 또는 None으로
                if self.active_projects.get(session_id) == project_id:
                    if self.sessions[session_id]:
                        # 다른 프로젝트가 있으면 첫 번째 것으로 전환
                        self.active_projects[session_id] = list(self.sessions[session_id].keys())[0]
                    else:
                        # 프로젝트가 없으면 제거
                        del self.active_projects[session_id]

                return jsonify({'success': True})

        # API: 활성 프로젝트 전환
        @self.app.route('/api/projects/<project_id>/activate', methods=['PUT'])
        def activate_project(project_id):
            if 'session_id' not in session:
                return jsonify({'error': 'Session not found'}), 404

            session_id = session['session_id']

            with self.sessions_lock:
                if session_id not in self.sessions or project_id not in self.sessions[session_id]:
                    return jsonify({'error': 'Project not found'}), 404

                # 활성 프로젝트 전환
                self.active_projects[session_id] = project_id
                pm = self.sessions[session_id][project_id]

                return jsonify({
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': pm.project_name
                    }
                })

        # API: 폴더 트리 구조 조회
        @self.app.route('/api/folders/tree', methods=['GET'])
        def get_folder_tree():
            pm = self.get_session_project_manager()
            return jsonify({
                'success': True,
                'tree': pm.root_folder.to_dict()
            })

        # API: 새 폴더 생성
        @self.app.route('/api/folders', methods=['POST'])
        def create_folder():
            pm = self.get_session_project_manager()
            data = request.json
            folder_name = data.get('name', 'New Folder')
            parent_id = data.get('parent_id', None)

            new_folder = RequestFolder(folder_name)

            if parent_id:
                # 부모 폴더 찾기
                parent_folder = pm.find_folder_by_id(parent_id)
                if not parent_folder:
                    return jsonify({'error': 'Parent folder not found'}), 404
                parent_folder.add_folder(new_folder)
            else:
                # 루트에 추가
                pm.root_folder.add_folder(new_folder)

            return jsonify({
                'success': True,
                'folder': new_folder.to_dict()
            }), 201

        # API: 폴더 이름 수정
        @self.app.route('/api/folders/<folder_id>', methods=['PUT'])
        def update_folder(folder_id):
            pm = self.get_session_project_manager()
            folder = pm.find_folder_by_id(folder_id)

            if not folder:
                return jsonify({'error': 'Folder not found'}), 404

            data = request.json
            if 'name' in data:
                folder.name = data['name']

            return jsonify({
                'success': True,
                'folder': folder.to_dict()
            })

        # API: 폴더 삭제
        @self.app.route('/api/folders/<folder_id>', methods=['DELETE'])
        def delete_folder(folder_id):
            pm = self.get_session_project_manager()

            # 루트 폴더는 삭제 불가
            if folder_id == pm.root_folder.id:
                return jsonify({'error': 'Cannot delete root folder'}), 400

            if pm.remove_folder_recursive(folder_id):
                return jsonify({'success': True})

            return jsonify({'error': 'Folder not found'}), 404

        # API: 폴더에 새 요청 추가
        @self.app.route('/api/folders/<folder_id>/requests', methods=['POST'])
        def create_request_in_folder(folder_id):
            pm = self.get_session_project_manager()
            folder = pm.find_folder_by_id(folder_id)

            if not folder:
                return jsonify({'error': 'Folder not found'}), 404

            data = request.json
            new_request = RequestModel(data.get('name', 'New Request'))
            if 'url' in data:
                new_request.url = data['url']
            if 'method' in data:
                new_request.method = HttpMethod(data['method'])

            folder.add_request(new_request)

            return jsonify({
                'success': True,
                'request': new_request.to_dict()
            }), 201

        # API: 요청을 다른 폴더로 이동
        @self.app.route('/api/requests/<request_id>/move', methods=['PUT'])
        def move_request(request_id):
            pm = self.get_session_project_manager()
            data = request.json
            target_folder_id = data.get('folder_id')

            if not target_folder_id:
                return jsonify({'error': 'Target folder_id required'}), 400

            # 타겟 폴더 찾기
            target_folder = pm.find_folder_by_id(target_folder_id)
            if not target_folder:
                return jsonify({'error': 'Target folder not found'}), 404

            # 요청 찾기 및 제거
            req = pm.find_request_by_id(request_id)
            if not req:
                return jsonify({'error': 'Request not found'}), 404

            # 현재 폴더에서 제거
            if not pm.remove_request_recursive(request_id):
                return jsonify({'error': 'Failed to remove request from current folder'}), 500

            # 타겟 폴더에 추가
            target_folder.add_request(req)

            return jsonify({
                'success': True,
                'request': req.to_dict()
            })

        # API: 폴더를 다른 폴더로 이동
        @self.app.route('/api/folders/<folder_id>/move', methods=['PUT'])
        def move_folder(folder_id):
            pm = self.get_session_project_manager()
            data = request.json
            parent_id = data.get('parent_id')

            if not parent_id:
                return jsonify({'error': 'Parent folder_id required'}), 400

            # 이동할 폴더 찾기
            folder = pm.find_folder_by_id(folder_id)
            if not folder:
                return jsonify({'error': 'Folder not found'}), 404

            # 타겟 부모 폴더 찾기
            parent_folder = pm.find_folder_by_id(parent_id)
            if not parent_folder:
                return jsonify({'error': 'Parent folder not found'}), 404

            # 자기 자신의 하위로 이동 방지 (순환 참조)
            if pm.is_descendant(parent_id, folder_id):
                return jsonify({'error': 'Cannot move folder into its own descendant'}), 400

            # 현재 위치에서 제거
            if not pm.remove_folder_recursive(folder_id):
                return jsonify({'error': 'Failed to remove folder from current location'}), 500

            # 새 위치에 추가
            parent_folder.add_folder(folder)

            return jsonify({
                'success': True,
                'folder': folder.to_dict()
            })

        # ======================
        # 프로젝트 공유 API
        # ======================

        # API: 프로젝트 공유 생성
        @self.app.route('/api/share/create', methods=['POST'])
        def create_share():
            pm = self.get_session_project_manager()
            data = request.json

            # 옵션 파라미터
            expires_hours = data.get('expires_hours', None)
            read_only = data.get('read_only', True)

            try:
                # 프로젝트 데이터를 공유 가능한 형태로 저장
                share_id = self.share_manager.create_share(
                    project_data=pm.to_dict(),
                    expires_hours=expires_hours,
                    read_only=read_only
                )

                # 공유 URL 생성
                share_url = f"{request.host_url}share/{share_id}"

                return jsonify({
                    'success': True,
                    'share_id': share_id,
                    'share_url': share_url,
                    'expires_hours': expires_hours,
                    'read_only': read_only
                }), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 공유 프로젝트 조회
        @self.app.route('/api/share/<share_id>', methods=['GET'])
        def get_share(share_id):
            try:
                share_data = self.share_manager.get_share(share_id)

                if not share_data:
                    return jsonify({'error': 'Share not found or expired'}), 404

                return jsonify({
                    'success': True,
                    'share_id': share_data['share_id'],
                    'created_at': share_data['created_at'],
                    'expires_at': share_data.get('expires_at'),
                    'read_only': share_data.get('read_only', True),
                    'project': share_data['project']
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 공유 프로젝트를 현재 세션에 불러오기
        @self.app.route('/api/share/<share_id>/import', methods=['POST'])
        def import_share(share_id):
            try:
                share_data = self.share_manager.get_share(share_id)

                if not share_data:
                    return jsonify({'error': 'Share not found or expired'}), 404

                # 프로젝트 복원
                pm = ProjectManager.from_dict(share_data['project'])

                # 세션에 추가
                if 'session_id' not in session:
                    session['session_id'] = str(uuid.uuid4())

                session_id = session['session_id']

                with self.sessions_lock:
                    # 새 프로젝트로 추가
                    project_id = str(uuid.uuid4())
                    if session_id not in self.sessions:
                        self.sessions[session_id] = {}
                    self.sessions[session_id][project_id] = pm
                    self.active_projects[session_id] = project_id

                return jsonify({
                    'success': True,
                    'project': {
                        'id': project_id,
                        'name': pm.project_name
                    },
                    'share_info': {
                        'share_id': share_id,
                        'read_only': share_data.get('read_only', True)
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 공유 삭제
        @self.app.route('/api/share/<share_id>', methods=['DELETE'])
        def delete_share(share_id):
            try:
                if self.share_manager.delete_share(share_id):
                    return jsonify({'success': True})
                return jsonify({'error': 'Share not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 모든 공유 목록 조회
        @self.app.route('/api/share/list', methods=['GET'])
        def list_shares():
            try:
                shares = self.share_manager.list_shares()
                return jsonify({
                    'success': True,
                    'shares': shares,
                    'count': len(shares)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # API: 만료된 공유 정리
        @self.app.route('/api/share/cleanup', methods=['POST'])
        def cleanup_shares():
            try:
                deleted_count = self.share_manager.cleanup_expired()
                return jsonify({
                    'success': True,
                    'deleted_count': deleted_count
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # 공유 페이지 (프론트엔드)
        @self.app.route('/share/<share_id>')
        def share_page(share_id):
            return render_template('share.html', share_id=share_id)

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
        print("Stopping Lumina Web Server...")
        self.is_running = False

        # 모든 세션 데이터 저장
        self.save_all_sessions()

        print("Lumina Web Server stopped")


def main():
    """웹 서버 단독 실행"""
    server = LuminaWebServer(host='0.0.0.0', port=15555)
    server.is_running = True  # 자동 저장/정리 스레드 활성화
    print(f"✨ Starting Lumina Web Server...")
    print(f"Access at: http://localhost:15555")
    try:
        server.app.run(host=server.host, port=server.port, debug=True)
    finally:
        server.stop()


if __name__ == '__main__':
    main()
