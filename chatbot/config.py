"""
RAG ETF 챗봇 설정 파일
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """설정 클래스"""

    # 16가지 투자자 유형별 가중치 (추천 엔진에서 사용)
    INVESTOR_TYPE_WEIGHTS = {
        'ARSB': {'A': 0.4, 'R': 0.3, 'S': 0.2, 'B': 0.1},  # Auto-driven, Risk-averse, Story, Buy&Hold
        'ARSE': {'A': 0.4, 'R': 0.3, 'S': 0.1, 'E': 0.2},  # Auto-driven, Risk-averse, Story, Portfolio Tuner
        'ARTB': {'A': 0.4, 'R': 0.3, 'T': 0.2, 'B': 0.1},  # Auto-driven, Risk-averse, Technical, Buy&Hold
        'ARTE': {'A': 0.4, 'R': 0.3, 'T': 0.1, 'E': 0.2},  # Auto-driven, Risk-averse, Technical, Portfolio Tuner
        'AETB': {'A': 0.4, 'E': 0.3, 'T': 0.2, 'B': 0.1},  # Auto-driven, Enterprising, Technical, Buy&Hold
        'AETE': {'A': 0.4, 'E': 0.3, 'T': 0.1, 'P': 0.2},  # Auto-driven, Enterprising, Technical, Portfolio Tuner
        'AESB': {'A': 0.4, 'E': 0.3, 'S': 0.2, 'B': 0.1},  # Auto-driven, Enterprising, Story, Buy&Hold
        'AESE': {'A': 0.4, 'E': 0.3, 'S': 0.1, 'P': 0.2},  # Auto-driven, Enterprising, Story, Portfolio Tuner
        
        'IRSB': {'I': 0.4, 'R': 0.3, 'S': 0.2, 'B': 0.1},  # Investigator, Risk-averse, Story, Buy&Hold
        'IRSE': {'I': 0.4, 'R': 0.3, 'S': 0.1, 'E': 0.2},  # Investigator, Risk-averse, Story, Portfolio Tuner
        'IRTB': {'I': 0.4, 'R': 0.3, 'T': 0.2, 'B': 0.1},  # Investigator, Risk-averse, Technical, Buy&Hold
        'IRTE': {'I': 0.4, 'R': 0.3, 'T': 0.1, 'E': 0.2},  # Investigator, Risk-averse, Technical, Portfolio Tuner
        'IETB': {'I': 0.4, 'E': 0.3, 'T': 0.2, 'B': 0.1},  # Investigator, Enterprising, Technical, Buy&Hold
        'IETE': {'I': 0.4, 'E': 0.3, 'T': 0.1, 'P': 0.2},  # Investigator, Enterprising, Technical, Portfolio Tuner
        'IESB': {'I': 0.4, 'E': 0.3, 'S': 0.2, 'B': 0.1},  # Investigator, Enterprising, Story, Buy&Hold
        'IESE': {'I': 0.4, 'E': 0.3, 'S': 0.1, 'P': 0.2},  # Investigator, Enterprising, Story, Portfolio Tuner
    }

    @classmethod
    def get_analysis_prompt(cls, user_profile=None):
        """ETF 분석용 기본 프롬프트"""
        return """당신은 ETF 투자 전문 상담사입니다.
사용자의 투자 레벨에 맞춰 맞춤형 답변을 제공하세요.
답변에는 반드시 공식 데이터(수익률, 보수, 자산규모, 거래량 등)와 시세 데이터(수익률, 변동성, 최대낙폭)를 모두 활용하세요.
설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성하고, 예시, 비유, 실전 투자 팁도 포함하세요."""

    @classmethod
    def get_recommend_prompt(cls, user_profile=None):
        """ETF 추천용 프롬프트"""
        return """당신은 ETF 투자 전문 상담사입니다. 
사용자의 투자 레벨과 유형에 맞춰 맞춤형 답변을 제공하세요.
답변에는 반드시 공식 데이터(수익률, 보수, 자산규모, 거래량 등)와 시세 데이터(수익률, 변동성, 최대낙폭)를 모두 활용하세요.
설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성하고, 예시, 비유, 실전 투자 팁도 포함하세요.

16가지 투자자 유형:
- ARSB: 자동추천형 + 안전추구형 + 스토리형 + 장기보유형
- ARSE: 자동추천형 + 안전추구형 + 스토리형 + 포트폴리오조정형  
- ARTB: 자동추천형 + 안전추구형 + 기술분석형 + 장기보유형
- ARTE: 자동추천형 + 안전추구형 + 기술분석형 + 포트폴리오조정형
- AETB: 자동추천형 + 공격투자형 + 기술분석형 + 장기보유형
- AETE: 자동추천형 + 공격투자형 + 기술분석형 + 포트폴리오조정형
- AESB: 자동추천형 + 공격투자형 + 스토리형 + 장기보유형
- AESE: 자동추천형 + 공격투자형 + 스토리형 + 포트폴리오조정형
- IRSB: 직접분석형 + 안전추구형 + 스토리형 + 장기보유형
- IRSE: 직접분석형 + 안전추구형 + 스토리형 + 포트폴리오조정형
- IRTB: 직접분석형 + 안전추구형 + 기술분석형 + 장기보유형
- IRTE: 직접분석형 + 안전추구형 + 기술분석형 + 포트폴리오조정형
- IETB: 직접분석형 + 공격투자형 + 기술분석형 + 장기보유형
- IETE: 직접분석형 + 공격투자형 + 기술분석형 + 포트폴리오조정형
- IESB: 직접분석형 + 공격투자형 + 스토리형 + 장기보유형
- IESE: 직접분석형 + 공격투자형 + 스토리형 + 포트폴리오조정형"""

    @classmethod
    def get_system_prompt(cls, user_profile=None):
        """시스템 프롬프트 (clova_client에서 사용) - get_analysis_prompt와 동일"""
        return cls.get_analysis_prompt(user_profile)
    
    @staticmethod
    def get_level_number(user_level: str) -> int:
        """레벨 문자열을 숫자로 변환하는 유틸리티 함수"""
        return int(user_level[-1]) if user_level.startswith('level') else 2
