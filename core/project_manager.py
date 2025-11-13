"""
프로젝트를 관리하는 모듈 (JSON 저장/불러오기)
"""
import json
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
from models.request_model import RequestModel, RequestFolder, HttpMethod, BodyType
from models.environment import EnvironmentManager


class ProjectManager:
    """프로젝트 관리자 - Thread-safe"""

    def __init__(self):
        self.project_name = "Untitled Project"
        self.root_folder = RequestFolder("Root")
        self.env_manager = EnvironmentManager()
        self._lock = threading.RLock()  # Reentrant Lock for nested calls

    def to_dict(self) -> Dict[str, Any]:
        """프로젝트 전체를 딕셔너리로 변환"""
        with self._lock:
            return {
                "version": "1.0",
                "project_name": self.project_name,
                "root_folder": self.root_folder.to_dict(),
                "environment_manager": self.env_manager.to_dict(),
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectManager':
        """딕셔너리에서 프로젝트 복원"""
        manager = cls()
        manager.project_name = data.get("project_name", "Untitled Project")
        manager.root_folder = RequestFolder.from_dict(data.get("root_folder", {"name": "Root"}))
        manager.env_manager = EnvironmentManager.from_dict(data.get("environment_manager", {}))
        return manager

    def save_to_file(self, file_path: str):
        """
        프로젝트를 JSON 파일로 저장

        Args:
            file_path: 저장할 파일 경로
        """
        with self._lock:
            data = self.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'ProjectManager':
        """
        JSON 파일에서 프로젝트 불러오기

        Args:
            file_path: 불러올 파일 경로

        Returns:
            프로젝트 매니저 인스턴스
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def find_request_by_id(self, request_id: str, folder: Optional[RequestFolder] = None) -> Optional[RequestModel]:
        """
        ID로 요청 찾기 (재귀적 탐색)

        Args:
            request_id: 요청 ID
            folder: 검색할 폴더 (None이면 루트부터)

        Returns:
            찾은 요청 또는 None
        """
        with self._lock:
            if folder is None:
                folder = self.root_folder

            # 현재 폴더의 요청 검색
            for req in folder.requests:
                if req.id == request_id:
                    return req

            # 하위 폴더 재귀 검색
            for sub_folder in folder.folders:
                result = self.find_request_by_id(request_id, sub_folder)
                if result:
                    return result

            return None

    def find_folder_by_id(self, folder_id: str, folder: Optional[RequestFolder] = None) -> Optional[RequestFolder]:
        """
        ID로 폴더 찾기 (재귀적 탐색)

        Args:
            folder_id: 폴더 ID
            folder: 검색할 폴더 (None이면 루트부터)

        Returns:
            찾은 폴더 또는 None
        """
        with self._lock:
            if folder is None:
                folder = self.root_folder

            if folder.id == folder_id:
                return folder

            # 하위 폴더 재귀 검색
            for sub_folder in folder.folders:
                result = self.find_folder_by_id(folder_id, sub_folder)
                if result:
                    return result

            return None

    def get_all_requests(self, folder: Optional[RequestFolder] = None) -> List[RequestModel]:
        """
        모든 요청 가져오기 (재귀적)

        Args:
            folder: 검색할 폴더 (None이면 루트부터)

        Returns:
            모든 요청 리스트
        """
        with self._lock:
            if folder is None:
                folder = self.root_folder

            requests = list(folder.requests)

            # 하위 폴더의 요청들도 추가
            for sub_folder in folder.folders:
                requests.extend(self.get_all_requests(sub_folder))

            return requests

    def remove_folder_recursive(self, folder_id: str, parent: Optional[RequestFolder] = None) -> bool:
        """
        폴더를 재귀적으로 삭제

        Args:
            folder_id: 삭제할 폴더 ID
            parent: 부모 폴더 (None이면 루트부터)

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if parent is None:
                parent = self.root_folder

            # 직접 자식 폴더 검색 및 삭제
            if parent.remove_folder(folder_id):
                return True

            # 하위 폴더에서 재귀적으로 삭제
            for sub_folder in parent.folders:
                if self.remove_folder_recursive(folder_id, sub_folder):
                    return True

            return False

    def remove_request_recursive(self, request_id: str, folder: Optional[RequestFolder] = None) -> bool:
        """
        요청을 재귀적으로 삭제

        Args:
            request_id: 삭제할 요청 ID
            folder: 검색할 폴더 (None이면 루트부터)

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if folder is None:
                folder = self.root_folder

            # 현재 폴더에서 요청 삭제 시도
            if folder.remove_request(request_id):
                return True

            # 하위 폴더에서 재귀적으로 삭제
            for sub_folder in folder.folders:
                if self.remove_request_recursive(request_id, sub_folder):
                    return True

            return False

    def create_sample_project(self):
        """샘플 프로젝트 생성 (테스트용)"""
        with self._lock:
            self.project_name = "Sample API Project"

            # 샘플 요청 생성
            req1 = RequestModel("Get Users")
            req1.method = HttpMethod.GET
            req1.url = "https://jsonplaceholder.typicode.com/users"

            req2 = RequestModel("Get Single User")
            req2.method = HttpMethod.GET
            req2.url = "https://jsonplaceholder.typicode.com/users/1"

            req3 = RequestModel("Create Post")
            req3.method = HttpMethod.POST
            req3.url = "https://jsonplaceholder.typicode.com/posts"
            req3.body_type = BodyType.RAW
            req3.body_raw = json.dumps({
                "title": "Sample Post",
                "body": "This is a sample post",
                "userId": 1
            }, indent=2)
            req3.headers = {"Content-Type": "application/json"}

            # 루트 폴더에 추가
            self.root_folder.add_request(req1)
            self.root_folder.add_request(req2)

            # 하위 폴더 생성
            posts_folder = RequestFolder("Posts")
            posts_folder.add_request(req3)
            self.root_folder.add_folder(posts_folder)

            # 샘플 환경 변수 생성
            from models.environment import Environment
            dev_env = Environment("Development")
            dev_env.set("API_URL", "https://jsonplaceholder.typicode.com")
            dev_env.set("USER_ID", "1")
            self.env_manager.add_environment(dev_env)
            self.env_manager.set_active(dev_env.id)
