"""
프로젝트 공유 관리자
URL을 통해 프로젝트를 공유하고 불러오는 기능
"""
import json
import os
import string
import random
import threading
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta


class ShareManager:
    """프로젝트 공유 관리자 - Thread-safe"""

    def __init__(self, storage_dir: str = "shared_projects"):
        """
        Args:
            storage_dir: 공유 프로젝트를 저장할 디렉토리
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self._lock = threading.RLock()

    def _generate_share_id(self, length: int = 8) -> str:
        """
        고유한 공유 ID 생성

        Args:
            length: ID 길이 (기본값: 8)

        Returns:
            생성된 공유 ID
        """
        chars = string.ascii_lowercase + string.digits
        while True:
            share_id = ''.join(random.choices(chars, k=length))
            # 중복 확인
            if not self._share_exists(share_id):
                return share_id

    def _share_exists(self, share_id: str) -> bool:
        """공유 ID가 이미 존재하는지 확인"""
        return (self.storage_dir / f"{share_id}.json").exists()

    def _get_share_path(self, share_id: str) -> Path:
        """공유 ID에 해당하는 파일 경로 반환"""
        return self.storage_dir / f"{share_id}.json"

    def create_share(
        self,
        project_data: Dict[str, Any],
        expires_hours: Optional[int] = None,
        read_only: bool = True
    ) -> str:
        """
        프로젝트를 공유 가능한 형태로 저장

        Args:
            project_data: 프로젝트 데이터 (ProjectManager.to_dict() 결과)
            expires_hours: 만료 시간 (시간 단위, None이면 무제한)
            read_only: 읽기 전용 여부

        Returns:
            생성된 공유 ID
        """
        with self._lock:
            share_id = self._generate_share_id()

            # 공유 메타데이터 생성
            share_data = {
                "share_id": share_id,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat() if expires_hours else None,
                "read_only": read_only,
                "project": project_data
            }

            # 저장
            share_path = self._get_share_path(share_id)
            with open(share_path, 'w', encoding='utf-8') as f:
                json.dump(share_data, f, indent=2, ensure_ascii=False)

            return share_id

    def get_share(self, share_id: str) -> Optional[Dict[str, Any]]:
        """
        공유 ID로 프로젝트 데이터 가져오기

        Args:
            share_id: 공유 ID

        Returns:
            공유 데이터 또는 None (존재하지 않거나 만료된 경우)
        """
        with self._lock:
            share_path = self._get_share_path(share_id)

            if not share_path.exists():
                return None

            # 데이터 로드
            with open(share_path, 'r', encoding='utf-8') as f:
                share_data = json.load(f)

            # 만료 확인
            if share_data.get("expires_at"):
                expires_at = datetime.fromisoformat(share_data["expires_at"])
                if datetime.now() > expires_at:
                    # 만료된 공유 삭제
                    share_path.unlink()
                    return None

            return share_data

    def delete_share(self, share_id: str) -> bool:
        """
        공유 삭제

        Args:
            share_id: 공유 ID

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            share_path = self._get_share_path(share_id)

            if share_path.exists():
                share_path.unlink()
                return True

            return False

    def cleanup_expired(self) -> int:
        """
        만료된 공유 정리

        Returns:
            삭제된 공유 개수
        """
        with self._lock:
            deleted_count = 0

            for share_file in self.storage_dir.glob("*.json"):
                try:
                    with open(share_file, 'r', encoding='utf-8') as f:
                        share_data = json.load(f)

                    # 만료 확인
                    if share_data.get("expires_at"):
                        expires_at = datetime.fromisoformat(share_data["expires_at"])
                        if datetime.now() > expires_at:
                            share_file.unlink()
                            deleted_count += 1
                except Exception:
                    # 손상된 파일 삭제
                    share_file.unlink()
                    deleted_count += 1

            return deleted_count

    def list_shares(self) -> list:
        """
        모든 공유 목록 조회

        Returns:
            공유 정보 리스트
        """
        with self._lock:
            shares = []

            for share_file in self.storage_dir.glob("*.json"):
                try:
                    with open(share_file, 'r', encoding='utf-8') as f:
                        share_data = json.load(f)

                    # 만료 확인
                    is_expired = False
                    if share_data.get("expires_at"):
                        expires_at = datetime.fromisoformat(share_data["expires_at"])
                        is_expired = datetime.now() > expires_at

                    shares.append({
                        "share_id": share_data["share_id"],
                        "created_at": share_data["created_at"],
                        "expires_at": share_data.get("expires_at"),
                        "is_expired": is_expired,
                        "read_only": share_data.get("read_only", True),
                        "project_name": share_data.get("project", {}).get("project_name", "Unknown")
                    })
                except Exception:
                    continue

            return shares
