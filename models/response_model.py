"""
HTTP 응답을 표현하는 데이터 모델
"""
from typing import Dict, Optional
from datetime import datetime


class ResponseModel:
    """HTTP 응답 데이터 모델"""

    def __init__(self):
        self.status_code: int = 0
        self.status_text: str = ""
        self.headers: Dict[str, str] = {}
        self.body: str = ""
        self.body_bytes: Optional[bytes] = None
        self.elapsed_ms: float = 0.0
        self.size_bytes: int = 0
        self.timestamp: datetime = datetime.now()
        self.error: Optional[str] = None
        self.content_type: str = ""

    def is_json(self) -> bool:
        """응답이 JSON인지 확인"""
        return "application/json" in self.content_type.lower()

    def is_xml(self) -> bool:
        """응답이 XML인지 확인"""
        return "application/xml" in self.content_type.lower() or "text/xml" in self.content_type.lower()

    def is_html(self) -> bool:
        """응답이 HTML인지 확인"""
        return "text/html" in self.content_type.lower()

    def is_text(self) -> bool:
        """응답이 텍스트인지 확인"""
        return "text/" in self.content_type.lower() or self.is_json() or self.is_xml()

    def is_success(self) -> bool:
        """성공 응답인지 확인 (2xx)"""
        return 200 <= self.status_code < 300

    def is_error(self) -> bool:
        """에러가 있는지 확인"""
        return self.error is not None
