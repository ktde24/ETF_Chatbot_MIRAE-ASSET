"""
ETF 챗봇 설정 파일
- 투자자 유형별 가중치 설정
- 시스템 프롬프트 관리
- 파일 경로 중앙 관리
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 레벨별 프롬프트 임포트
from .etf_analysis import LEVEL_PROMPTS

class Config:
    """ETF 챗봇 설정 클래스"""
    
    # =============================================================================
    # 파일 경로 설정
    # =============================================================================
    DATA_PATHS = {
        'etf_info': 'data/상품검색.csv',
        'etf_prices': 'data/ETF_시세_데이터_20240101_20250729.csv',
        'etf_performance': 'data/수익률 및 총보수(기간).csv',
        'etf_aum': 'data/자산규모 및 유동성(기간).csv',
        'etf_reference': 'data/참고지수(기간).csv',
        'etf_risk': 'data/투자위험(기간).csv',
        'risk_tier': 'data/etf_re_bp_simplified.csv',
        'cache': 'data/etf_scores_cache.csv'
    }
    
    # =============================================================================
    # 투자자 유형별 가중치 설정
    # =============================================================================
    INVESTOR_TYPE_WEIGHTS = {
        # Auto-driven (A) 계열
        'ARSB': {'A': 0.4, 'R': 0.3, 'S': 0.2, 'B': 0.1},  # 자동추천 + 안전추구 + 스토리 + 장기보유
        'ARSE': {'A': 0.4, 'R': 0.3, 'S': 0.1, 'P': 0.2},  # 자동추천 + 안전추구 + 스토리 + 포트폴리오조정
        'ARTB': {'A': 0.4, 'R': 0.3, 'T': 0.2, 'B': 0.1},  # 자동추천 + 안전추구 + 기술분석 + 장기보유
        'ARTE': {'A': 0.4, 'R': 0.3, 'T': 0.1, 'P': 0.2},  # 자동추천 + 안전추구 + 기술분석 + 포트폴리오조정
        'AETB': {'A': 0.4, 'E': 0.3, 'T': 0.2, 'B': 0.1},  # 자동추천 + 공격투자 + 기술분석 + 장기보유
        'AETE': {'A': 0.4, 'E': 0.3, 'T': 0.1, 'P': 0.2},  # 자동추천 + 공격투자 + 기술분석 + 포트폴리오조정
        'AESB': {'A': 0.4, 'E': 0.3, 'S': 0.2, 'B': 0.1},  # 자동추천 + 공격투자 + 스토리 + 장기보유
        'AESE': {'A': 0.4, 'E': 0.3, 'S': 0.1, 'P': 0.2},  # 자동추천 + 공격투자 + 스토리 + 포트폴리오조정
        
        # Investigator (I) 계열
        'IRSB': {'I': 0.4, 'R': 0.3, 'S': 0.2, 'B': 0.1},  # 직접분석 + 안전추구 + 스토리 + 장기보유
        'IRSE': {'I': 0.4, 'R': 0.3, 'S': 0.1, 'P': 0.2},  # 직접분석 + 안전추구 + 스토리 + 포트폴리오조정
        'IRTB': {'I': 0.4, 'R': 0.3, 'T': 0.2, 'B': 0.1},  # 직접분석 + 안전추구 + 기술분석 + 장기보유
        'IRTE': {'I': 0.4, 'R': 0.3, 'T': 0.1, 'P': 0.2},  # 직접분석 + 안전추구 + 기술분석 + 포트폴리오조정
        'IETB': {'I': 0.4, 'E': 0.3, 'T': 0.2, 'B': 0.1},  # 직접분석 + 공격투자 + 기술분석 + 장기보유
        'IETE': {'I': 0.4, 'E': 0.3, 'T': 0.1, 'P': 0.2},  # 직접분석 + 공격투자 + 기술분석 + 포트폴리오조정
        'IESB': {'I': 0.4, 'E': 0.3, 'S': 0.2, 'B': 0.1},  # 직접분석 + 공격투자 + 스토리 + 장기보유
        'IESE': {'I': 0.4, 'E': 0.3, 'S': 0.1, 'P': 0.2},  # 직접분석 + 공격투자 + 스토리 + 포트폴리오조정
    }
    
    # =============================================================================
    # 투자자 유형 설명
    # =============================================================================
    INVESTOR_TYPE_DESCRIPTIONS = {
        'ARSB': '자동추천형 + 안전추구형 + 스토리형 + 장기보유형',
        'ARSE': '자동추천형 + 안전추구형 + 스토리형 + 포트폴리오조정형',
        'ARTB': '자동추천형 + 안전추구형 + 기술분석형 + 장기보유형',
        'ARTE': '자동추천형 + 안전추구형 + 기술분석형 + 포트폴리오조정형',
        'AETB': '자동추천형 + 공격투자형 + 기술분석형 + 장기보유형',
        'AETE': '자동추천형 + 공격투자형 + 기술분석형 + 포트폴리오조정형',
        'AESB': '자동추천형 + 공격투자형 + 스토리형 + 장기보유형',
        'AESE': '자동추천형 + 공격투자형 + 스토리형 + 포트폴리오조정형',
        'IRSB': '직접분석형 + 안전추구형 + 스토리형 + 장기보유형',
        'IRSE': '직접분석형 + 안전추구형 + 스토리형 + 포트폴리오조정형',
        'IRTB': '직접분석형 + 안전추구형 + 기술분석형 + 장기보유형',
        'IRTE': '직접분석형 + 안전추구형 + 기술분석형 + 포트폴리오조정형',
        'IETB': '직접분석형 + 공격투자형 + 기술분석형 + 장기보유형',
        'IETE': '직접분석형 + 공격투자형 + 기술분석형 + 포트폴리오조정형',
        'IESB': '직접분석형 + 공격투자형 + 스토리형 + 장기보유형',
        'IESE': '직접분석형 + 공격투자형 + 스토리형 + 포트폴리오조정형',
    }
    
    # =============================================================================
    # 레벨별 Risk Tier 허용 범위
    # =============================================================================
    LEVEL_RISK_TIER_LIMITS = {
        1: 2,  # Level 1: risk_tier 0~2 (안전한 ETF만)
        2: 3,  # Level 2: risk_tier 0~3 (중간 위험까지)
        3: 4   # Level 3: risk_tier 0~4 (모든 위험 레벨)
    }
    
    # =============================================================================
    # 프롬프트 관리
    # =============================================================================
    @classmethod
    def get_system_prompt(cls, user_profile: Dict[str, Any] = None) -> str:
        """
        시스템 기본 프롬프트 생성
        
        Args:
            user_profile: 사용자 프로필 (level, investor_type)
        
        Returns:
            시스템 프롬프트 문자열
        """
        base_prompt = """당신은 ETF 투자 전문 상담사입니다.
사용자의 투자 레벨과 투자자 유형에 맞춰 맞춤형 답변을 제공하세요.

답변 요구사항:
- 공식 데이터(수익률, 보수, 자산규모, 거래량)와 시세 데이터(수익률, 변동성, 최대낙폭)를 모두 활용
- 사용자 레벨에 맞는 어투와 깊이로 작성
- 구체적인 수치와 근거 포함
- 실전 투자 팁과 예시, 비유 포함
- 투자 위험 고지 포함

투자자 유형별 특성:
- A (Auto-driven): 자동 추천 선호, 간단한 설명
- I (Investigator): 상세 분석 선호, 데이터 중심 설명
- R (Risk-averse): 안전성 중시, 위험 관리 강조
- E (Eager): 공격적 투자 선호, 성장성 중시
- S (Story-driven): 투자 스토리와 배경 설명 선호
- T (Technical): 기술적 분석과 차트 선호
- B (Buy-and-hold): 장기 보유 전략 선호
- P (Portfolio): 포트폴리오 조정과 분산 투자 선호

레벨별 답변 스타일:
- Level 1: 유치원/초등학생 수준, 비유와 예시 위주
- Level 2: 중고등학생 수준, 핵심 개념과 이유 포함
- Level 3: 투자 전문가 수준, 고급 분석과 실전 활용 관점"""
        
        if user_profile:
            level = user_profile.get('level', 1)
            investor_type = user_profile.get('investor_type', 'ARSB')
            
            level_prompt = LEVEL_PROMPTS.get(level, "")
            investor_desc = cls.get_investor_type_description(investor_type)
            
            base_prompt += f"\n\n현재 사용자: Level {level}, {investor_desc}\n{level_prompt}"
        
        return base_prompt
    
    @classmethod 
    def get_recommendation_prompt(cls, user_profile: Dict[str, Any] = None) -> str:
        """ETF 추천용 프롬프트 생성"""
        base_prompt = cls.get_system_prompt(user_profile)
        
        # 투자자 유형 설명 추가
        investor_types_desc = "\n".join([
            f"- {code}: {desc}" 
            for code, desc in cls.INVESTOR_TYPE_DESCRIPTIONS.items()
        ])
        
        recommendation_prompt = f"""{base_prompt}

투자자 유형별 특성:
{investor_types_desc}

추천 시 고려사항:
1. 사용자의 투자 레벨과 유형에 맞는 적절한 위험도
2. 각 ETF의 장단점과 특징
3. 투자 시 주의사항과 실전 팁
4. 구체적인 투자 전략 제안"""
        
        return recommendation_prompt
    
    # =============================================================================
    # 유틸리티 메서드
    # =============================================================================
    @staticmethod
    def get_level_number(user_level: str) -> int:
        """레벨 문자열을 숫자로 변환"""
        if isinstance(user_level, int):
            return user_level
        if isinstance(user_level, str) and user_level.startswith('level'):
            return int(user_level[-1])
        return 2  # 기본값: Level 2
    
    @classmethod
    def get_data_path(cls, data_type: str) -> str:
        """데이터 파일 경로 반환"""
        return cls.DATA_PATHS.get(data_type, '')
    
    @classmethod
    def get_investor_type_description(cls, investor_type: str) -> str:
        """투자자 유형 설명 반환"""
        return cls.INVESTOR_TYPE_DESCRIPTIONS.get(investor_type, '알 수 없는 유형')
    
    @classmethod
    def get_risk_tier_limit(cls, level: int) -> int:
        """레벨별 risk_tier 허용 한계 반환"""
        return cls.LEVEL_RISK_TIER_LIMITS.get(level, 4)
