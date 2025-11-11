"""
환경 변수를 치환하는 유틸리티
"""
import re
from typing import Dict


class VariableResolver:
    """환경 변수 치환 도구"""

    # {{변수명}} 형태를 찾는 정규식
    PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    @classmethod
    def resolve(cls, text: str, variables: Dict[str, str]) -> str:
        """
        텍스트에서 {{변수명}} 형태를 실제 값으로 치환

        Args:
            text: 치환할 텍스트
            variables: 변수 딕셔너리

        Returns:
            치환된 텍스트
        """
        if not text:
            return text

        def replacer(match):
            var_name = match.group(1).strip()
            return variables.get(var_name, match.group(0))  # 값이 없으면 원본 유지

        return cls.PATTERN.sub(replacer, text)

    @classmethod
    def resolve_dict(cls, data: Dict[str, str], variables: Dict[str, str]) -> Dict[str, str]:
        """
        딕셔너리의 모든 값을 치환

        Args:
            data: 치환할 딕셔너리
            variables: 변수 딕셔너리

        Returns:
            치환된 딕셔너리
        """
        return {key: cls.resolve(value, variables) for key, value in data.items()}

    @classmethod
    def find_variables(cls, text: str) -> list:
        """
        텍스트에서 모든 변수명 추출

        Args:
            text: 검색할 텍스트

        Returns:
            변수명 리스트
        """
        if not text:
            return []

        matches = cls.PATTERN.findall(text)
        return [match.strip() for match in matches]
