"""
요청/응답 히스토리 모델
"""
from datetime import datetime
from typing import Dict, Any, List
from models.request_model import RequestModel
from models.response_model import ResponseModel


class HistoryEntry:
    """단일 히스토리 항목"""

    def __init__(self, request: RequestModel, response: ResponseModel):
        self.timestamp = datetime.now()
        self.request = request
        self.response = response
        self.request_snapshot = {
            'name': request.name,
            'method': request.method.value,
            'url': request.url,
            'headers': dict(request.headers),
            'params': dict(request.params),
            'body': request.body_raw if request.body_raw else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'request': self.request_snapshot,
            'response': {
                'status_code': self.response.status_code,
                'status_text': self.response.status_text,
                'elapsed_ms': self.response.elapsed_ms,
                'size_bytes': self.response.size_bytes,
                'headers': self.response.headers,
                'body': self.response.body[:1000] if self.response.body else None,  # 1KB 제한
                'error': self.response.error
            }
        }


class RequestHistory:
    """요청별 히스토리 관리"""

    def __init__(self, request_id: str, max_entries: int = 50):
        self.request_id = request_id
        self.max_entries = max_entries
        self.entries: List[HistoryEntry] = []

    def add_entry(self, request: RequestModel, response: ResponseModel):
        """히스토리 항목 추가"""
        entry = HistoryEntry(request, response)
        self.entries.insert(0, entry)  # 최신 항목이 앞에

        # 최대 개수 제한
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]

    def get_entries(self, limit: int = None) -> List[HistoryEntry]:
        """히스토리 항목 가져오기"""
        if limit:
            return self.entries[:limit]
        return self.entries

    def clear(self):
        """히스토리 초기화"""
        self.entries.clear()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'request_id': self.request_id,
            'count': len(self.entries),
            'entries': [entry.to_dict() for entry in self.entries]
        }


class HistoryManager:
    """전체 히스토리 관리자"""

    def __init__(self):
        self.histories: Dict[str, RequestHistory] = {}

    def add_entry(self, request: RequestModel, response: ResponseModel):
        """히스토리 항목 추가"""
        if request.id not in self.histories:
            self.histories[request.id] = RequestHistory(request.id)

        self.histories[request.id].add_entry(request, response)

    def get_history(self, request_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """특정 요청의 히스토리 가져오기"""
        if request_id not in self.histories:
            return []

        entries = self.histories[request_id].get_entries(limit)
        return [entry.to_dict() for entry in entries]

    def get_all_histories(self) -> Dict[str, Any]:
        """모든 히스토리 가져오기"""
        return {
            req_id: history.to_dict()
            for req_id, history in self.histories.items()
        }

    def clear_history(self, request_id: str = None):
        """히스토리 삭제"""
        if request_id:
            if request_id in self.histories:
                self.histories[request_id].clear()
        else:
            self.histories.clear()
