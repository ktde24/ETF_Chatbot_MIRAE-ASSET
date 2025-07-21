"""
RAG ETF 챗봇 설정 파일
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """설정 클래스"""

    # CLOVA API 설정
    CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "")
    CLOVA_API_URL = "https://clovax-api.ncloud.com/v1/chat/completions"
    CLOVA_MAX_TOKENS = 1500
    CLOVA_TEMPERATURE = 0.7

    @classmethod
    def get_analysis_prompt(cls, user_profile=None):
        base_prompt = """당신은 ETF 투자 전문 상담사입니다.
        사용자의 투자 레벨에 맞춰 맞춤형 답변을 제공하세요.
        답변에는 반드시 공식 데이터(수익률, 보수, 자산규모, 거래량 등)와 시세 데이터(수익률, 변동성, 최대낙폭)를 모두 활용하세요.
        설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성하고, 예시, 비유, 실전 투자 팁도 포함하세요.
        """
        if user_profile:
            level_info = cls.LEVEL_STYLES.get(user_profile.get('level', 'level2'), {})
            level_prompt = f"""
            사용자 레벨: {level_info.get('name', '투자 초보자')}
            설명 스타일: {level_info.get('description', '기본 용어 설명과 함께 단계별 안내')}
            (설명에는 반드시 공식 데이터와 시세 데이터 모두를 활용하고, 예시, 비유, 실전 투자 팁을 포함하세요.)
            """
            return base_prompt + level_prompt
        return base_prompt

    @classmethod
    def get_recommend_prompt(cls, user_profile=None):
        base_prompt = """당신은 ETF 투자 전문 상담사입니다. 
        사용자의 투자 레벨과 유형에 맞춰 맞춤형 답변을 제공하세요.
        답변에는 반드시 공식 데이터(수익률, 보수, 자산규모, 거래량 등)와 시세 데이터(수익률, 변동성, 최대낙폭)를 모두 활용하세요.
        설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성하고, 예시, 비유, 실전 투자 팁도 포함하세요.
        16가지 투자자 유형:
        - ARSB: Auto-driven, Risk-averse, Story, Buy&Hold (자동추천, 안전추구, 스토리, 장기보유)
        - ARSE: Auto-driven, Risk-averse, Story, Portfolio Tuner (자동추천, 안전추구, 스토리, 포트폴리오 조정)
        - ARTB: Auto-driven, Risk-averse, Technical, Buy&Hold (자동추천, 안전추구, 기술적분석, 장기보유)
        - ARTE: Auto-driven, Risk-averse, Technical, Portfolio Tuner (자동추천, 안전추구, 기술적분석, 포트폴리오 조정)
        - AETB: Auto-driven, Enterprising, Technical, Buy&Hold (자동추천, 공격적, 기술적분석, 장기보유)
        - AETE: Auto-driven, Enterprising, Technical, Portfolio Tuner (자동추천, 공격적, 기술적분석, 포트폴리오 조정)
        - AESB: Auto-driven, Enterprising, Story, Buy&Hold (자동추천, 공격적, 스토리, 장기보유)
        - AESE: Auto-driven, Enterprising, Story, Portfolio Tuner (자동추천, 공격적, 스토리, 포트폴리오 조정)
        - IRSB: Investigator, Risk-averse, Story, Buy&Hold (직접분석, 안전추구, 스토리, 장기보유)
        - IRSE: Investigator, Risk-averse, Story, Portfolio Tuner (직접분석, 안전추구, 스토리, 포트폴리오 조정)
        - IRTB: Investigator, Risk-averse, Technical, Buy&Hold (직접분석, 안전추구, 기술적분석, 장기보유)
        - IRTE: Investigator, Risk-averse, Technical, Portfolio Tuner (직접분석, 안전추구, 기술적분석, 포트폴리오 조정)
        - IETB: Investigator, Enterprising, Technical, Buy&Hold (직접분석, 공격적, 기술적분석, 장기보유)
        - IETE: Investigator, Enterprising, Technical, Portfolio Tuner (직접분석, 공격적, 기술적분석, 포트폴리오 조정)
        - IESB: Investigator, Enterprising, Story, Buy&Hold (직접분석, 공격적, 스토리, 장기보유)
        - IESE: Investigator, Enterprising, Story, Portfolio Tuner (직접분석, 공격적, 스토리, 포트폴리오 조정)
        """
        if user_profile:
            level_info = cls.LEVEL_STYLES.get(user_profile.get('level', 'level2'), {})
            level_prompt = f"""
            사용자 레벨: {level_info.get('name', '투자 초보자')}
            설명 스타일: {level_info.get('description', '기본 용어 설명과 함께 단계별 안내')}
            (설명에는 반드시 공식 데이터와 시세 데이터 모두를 활용하고, 예시, 비유, 실전 투자 팁을 포함하세요.)
            """
            type_prompt = "투자자 유형:\n"
            for category, value in user_profile.get('types', {}).items():
                if value in cls.INVESTOR_TYPES.get(category, {}):
                    type_info = cls.INVESTOR_TYPES[category][value]
                    type_prompt += f"- {category}: {type_info['name']} ({type_info['description']})\n"
            return base_prompt + level_prompt + type_prompt
        return base_prompt
