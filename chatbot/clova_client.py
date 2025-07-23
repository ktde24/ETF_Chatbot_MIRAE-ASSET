"""
CLOVA API 클라이언트 모듈
- CLOVA LLM API 연동
- 응답 생성 및 파싱
- 에러 처리
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

try:
    from langchain_community.chat_models import ChatClovaX
except ImportError:
    ChatClovaX = None

from .config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClovaClient:
    """CLOVA API 클라이언트 클래스"""

    def __init__(self):
        """클라이언트 초기화"""
        self.api_key = st.session_state.get("clova_api_key", "")
        self.model = "HCX-003"
        self.max_tokens = 1500
        self.llm = None
        self.config = Config()
        
        if self.api_key and ChatClovaX:
            try:
                self.llm = ChatClovaX(
                    model=self.model, 
                    api_key=self.api_key, 
                    max_tokens=self.max_tokens
                )
                logger.info("CLOVA LLM 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"CLOVA LLM 클라이언트 초기화 실패: {e}")
                self.llm = None

    def is_configured(self) -> bool:
        """API 설정 여부 확인"""
        return bool(self.api_key and self.llm)

    def get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_response(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        CLOVA API를 통해 응답 생성
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수 (기본값: self.max_tokens)
        
        Returns:
            생성된 응답 텍스트
        """
        if not self.is_configured():
            return "⚠️ CLOVA API 키가 설정되지 않았거나 라이브러리가 설치되지 않았습니다."
        
        try:
            # API 호출
            response = self.llm.invoke(prompt, max_tokens=max_tokens or self.max_tokens)
            
            # 응답 파싱
            content = self._parse_response(response)
            logger.info(f"CLOVA API 호출 성공: {len(content)} 글자")
            return content
            
        except Exception as e:
            error_msg = f"CLOVA API 호출 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return f"{error_msg}"

    def _parse_response(self, response: Any) -> str:
        """
        CLOVA API 응답 파싱
        
        Args:
            response: CLOVA API 응답 객체
        
        Returns:
            파싱된 텍스트 내용
        """
        # Dict 형태 응답 처리
        if isinstance(response, dict) and 'content' in response:
            return response['content']
        
        # 객체 속성 접근
        if hasattr(response, 'content'):
            return response.content
        
        # 문자열 패턴 매칭으로 content 추출
        import re
        response_str = str(response)
        match = re.search(r"content='([^']*)'", response_str)
        if match:
            return match.group(1)
        
        # 기본값: 전체 응답을 문자열로 변환
        return response_str

    def generate_etf_analysis(self, etf_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """
        ETF 분석 응답 생성
        
        Args:
            etf_info: ETF 정보 딕셔너리
            user_profile: 사용자 프로필 (level, investor_type)
        
        Returns:
            ETF 분석 텍스트
        """
        if not self.is_configured():
            return "CLOVA API가 설정되지 않았습니다."
        
        try:
            # 시스템 프롬프트 생성
            system_prompt = self.config.get_system_prompt(user_profile)
            
            # 사용자 요청 프롬프트 생성
            user_request = self._create_analysis_request(etf_info, user_profile)
            
            # 최종 프롬프트 결합
            full_prompt = f"{system_prompt}\n\n{user_request}"
            
            return self.generate_response(full_prompt)
            
        except Exception as e:
            error_msg = f"ETF 분석 생성 중 오류: {str(e)}"
            logger.error(error_msg)
            return f" {error_msg}"

    def _create_analysis_request(self, etf_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """
        ETF 분석 요청 프롬프트 생성
        
        Args:
            etf_info: ETF 정보
            user_profile: 사용자 프로필
        
        Returns:
            분석 요청 프롬프트
        """
        etf_name = etf_info.get('ETF명', '알 수 없는 ETF')
        user_level = user_profile.get('level', 2)
        investor_type = user_profile.get('investor_type', 'ARSB')
        
        request_prompt = f"""
아래 ETF에 대한 종합적인 분석을 제공해주세요.

분석 대상: {etf_name}
사용자 정보: Level {user_level}, {self.config.get_investor_type_description(investor_type)}

ETF 상세 정보:
{self._format_etf_info(etf_info)}

분석 요청사항:
1. 시세 데이터 분석 (수익률, 변동성, 최대낙폭)
2. 공식 데이터 분석 (수익률, 보수, 자산규모, 거래량)
3. 장점과 단점 분석
4. 사용자 유형에 맞는 투자 적합성 평가
5. 구체적인 투자 전략 및 주의사항
6. 실전 투자 팁과 예시

답변은 사용자 레벨에 맞는 어투와 깊이로 작성해주세요.
"""
        return request_prompt

    def _format_etf_info(self, etf_info: Dict[str, Any]) -> str:
        """
        ETF 정보를 보기 좋게 포맷팅
        
        Args:
            etf_info: ETF 정보 딕셔너리
        
        Returns:
            포맷팅된 ETF 정보 문자열
        """
        formatted_parts = []
        
        # 기본 정보
        if '기본정보' in etf_info:
            basic_info = etf_info['기본정보']
            formatted_parts.append(f"기본정보: {basic_info}")
        
        # 시세 분석
        if '시세분석' in etf_info:
            market_data = etf_info['시세분석']
            formatted_parts.append(f"시세분석: {market_data}")
        
        # 수익률/보수
        if '수익률/보수' in etf_info:
            performance = etf_info['수익률/보수']
            formatted_parts.append(f"수익률/보수: {performance}")
        
        # 자산규모/유동성
        if '자산규모/유동성' in etf_info:
            aum_data = etf_info['자산규모/유동성']
            formatted_parts.append(f"자산규모/유동성: {aum_data}")
        
        # 위험 정보
        if '위험' in etf_info:
            risk_data = etf_info['위험']
            formatted_parts.append(f"위험정보: {risk_data}")
        
        return "\n".join(formatted_parts) if formatted_parts else "상세 정보를 확인할 수 없습니다."
