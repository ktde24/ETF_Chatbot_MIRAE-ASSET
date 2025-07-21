"""
CLOVA API 클라이언트 모듈
"""

import requests
import streamlit as st
from typing import Dict, Any, List
try:
    from langchain_community.chat_models import ChatClovaX
except ImportError:
    ChatClovaX = None

from .config import Config

class ClovaClient:
    """CLOVA API 클라이언트"""

    def __init__(self):
        self.api_key = st.session_state.get("clova_api_key", "")
        self.model = "HCX-003"
        self.max_tokens = 1500
        self.llm = None
        self.config = Config()
        if self.api_key and ChatClovaX:
            self.llm = ChatClovaX(model=self.model, api_key=self.api_key, max_tokens=self.max_tokens)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_response(self, prompt: str, max_tokens: int = None) -> str:
        if not self.llm:
            return "CLOVA LLM 라이브러리가 설치되어 있지 않거나, API 키가 입력되지 않았습니다."
        try:
            response = self.llm.invoke(prompt, max_tokens=max_tokens or self.max_tokens)
            if isinstance(response, dict) and 'content' in response:
                return response['content']
            if hasattr(response, 'content'):
                return response.content
            import re
            match = re.search(r"content='([^']*)'", str(response))
            if match:
                return match.group(1)
            return str(response)
        except Exception as e:
            return f"CLOVA LLM 호출 중 오류: {e}"

    def generate_analysis(self, etf_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        if not self.is_configured():
            return "CLOVA API 키가 설정되지 않았습니다."
        try:
            system_prompt = self.config.get_system_prompt(user_profile)
            # etf_info는 분석 함수에서 반환된 dict 전체를 넘기면 됨
            analysis_context = f"분석 대상 ETF 정보:\n{etf_info}\n"
            user_request = (
                f"아래 ETF의 시세 데이터(수익률, 변동성, 최대낙폭), 공식 수익률/보수, 자산규모, 거래량, 위험 등 모든 정보를 종합적으로 분석해줘.\n"
                f"- 장점/단점, 투자자 유형별 적합성, 투자 전략, 리스크 요인 등도 포함해서 설명해줘.\n"
                f"- 수치와 근거를 반드시 포함해서, 투자 판단에 도움이 되게 해줘.\n"
                f"- 공식 데이터(수익률, 보수, 자산규모, 거래량 등)도 반드시 설명에 포함해줘.\n"
                f"- 설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성해줘.\n"
                f"- 예시, 비유, 실전 투자 팁도 포함해줘.\n"
                f"ETF 정보:\n{etf_info}\n"
            )
            prompt = system_prompt + "\n" + analysis_context + "\n" + user_request
            return self.generate_response(prompt)
        except Exception as e:
            return f"CLOVA 분석 생성 오류: {e}"
