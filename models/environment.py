"""
환경 변수를 관리하는 데이터 모델
"""
from typing import Dict, Any, List, Optional
import uuid


class Environment:
    """환경 변수 세트"""

    def __init__(self, name: str = "New Environment"):
        self.id = str(uuid.uuid4())
        self.name = name
        self.variables: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Environment':
        """딕셔너리에서 복원"""
        env = cls(data.get("name", "New Environment"))
        env.id = data.get("id", str(uuid.uuid4()))
        env.variables = data.get("variables", {})
        return env

    def get(self, key: str, default: str = "") -> str:
        """변수 값 가져오기"""
        return self.variables.get(key, default)

    def set(self, key: str, value: str):
        """변수 설정"""
        self.variables[key] = value

    def delete(self, key: str) -> bool:
        """변수 삭제"""
        if key in self.variables:
            del self.variables[key]
            return True
        return False

    def get_all_keys(self) -> List[str]:
        """모든 변수 키 목록"""
        return list(self.variables.keys())


class EnvironmentManager:
    """여러 환경을 관리하는 매니저"""

    def __init__(self):
        self.environments: List[Environment] = []
        self.active_environment: Optional[Environment] = None
        self.global_environment = Environment("Global")

    def add_environment(self, env: Environment):
        """환경 추가"""
        self.environments.append(env)

    def remove_environment(self, env_id: str) -> bool:
        """환경 삭제"""
        for i, env in enumerate(self.environments):
            if env.id == env_id:
                if self.active_environment and self.active_environment.id == env_id:
                    self.active_environment = None
                del self.environments[i]
                return True
        return False

    def get_environment(self, env_id: str) -> Optional[Environment]:
        """환경 가져오기"""
        for env in self.environments:
            if env.id == env_id:
                return env
        return None

    def set_active(self, env_id: str) -> bool:
        """활성 환경 설정"""
        env = self.get_environment(env_id)
        if env:
            self.active_environment = env
            return True
        return False

    def get_effective_value(self, key: str, default: str = "") -> str:
        """
        효과적인 변수 값 가져오기
        활성 환경 우선, 없으면 글로벌 환경에서 가져옴
        """
        if self.active_environment:
            value = self.active_environment.get(key)
            if value:
                return value
        return self.global_environment.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "environments": [env.to_dict() for env in self.environments],
            "active_environment_id": self.active_environment.id if self.active_environment else None,
            "global_environment": self.global_environment.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnvironmentManager':
        """딕셔너리에서 복원"""
        manager = cls()
        manager.environments = [Environment.from_dict(env) for env in data.get("environments", [])]
        manager.global_environment = Environment.from_dict(data.get("global_environment", {"name": "Global"}))

        active_id = data.get("active_environment_id")
        if active_id:
            manager.set_active(active_id)

        return manager
