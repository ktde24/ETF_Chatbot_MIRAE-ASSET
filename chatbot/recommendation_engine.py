"""
ETF 추천 엔진
: 사용자 레벨과 투자 유형에 맞는 ETF 추천 기능
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Any, Optional
from .config import Config
from .etf_analysis import analyze_etf, normalize_etf_name, find_etf_row, safe_float

class ETFRecommendationEngine:
    """ETF 추천 엔진 클래스"""
    def __init__(self):
        self.config = Config()
        self.investor_type_criteria = {
            'A': {'auto_driven': {'aum_threshold': 1000000, 'score': 1.0}, 'investigator': {'aum_threshold': 100000, 'score': 0.7}},
            'R': {'risk_averse': {'volatility_grades': ['매우낮음', '낮음'], 'score': 1.0}, 'enterprising': {'volatility_grades': ['높음', '매우높음'], 'score': 1.0}},
            'S': {'story': {'classifications': ['주식-업종섹터-업종테마', '주식-전략-전략테마'], 'score': 1.0}, 'technical': {'classifications': ['주식-시장대표'], 'score': 1.0}},
            'B': {'buy_hold': {'volume_threshold': 10000, 'score': 1.0}, 'portfolio_tuner': {'volume_threshold': 100000, 'score': 1.0}}
        }

    def normalize_return(self, return_value: float) -> float:
        """
        수익률 정규화: -100%~+100% → 0~1
        """
        if return_value is None or np.isnan(return_value):
            return 0.5  # 중간값
        return max(0, min(1, (return_value + 100) / 200))
    
    def normalize_fee(self, fee_value: float) -> float:
        """
        총보수 정규화: 0~10% → 1~0 (낮을수록 좋음)
        """
        if fee_value is None or np.isnan(fee_value):
            return 0.5  # 중간값
        return max(0, min(1, 1 - (fee_value / 10)))
    
    def normalize_volume(self, volume_value: float) -> float:
        """
        거래량 정규화: 0~100만주 → 0~1
        """
        if volume_value is None or np.isnan(volume_value):
            return 0.5  # 중간값
        return max(0, min(1, volume_value / 1000000))
    
    def normalize_volatility(self, volatility_grade: str) -> float:
        """
        변동성 등급 정규화: 등급별로 0.2~1.0로 매핑
        """
        grade_mapping = {'매우낮음': 0.2, '낮음': 0.4, '보통': 0.6, '높음': 0.8, '매우높음': 1.0}
        return grade_mapping.get(volatility_grade, 0.6)  # 기본값: 보통
    
    def calculate_base_score(self, etf_data: Dict[str, Any]) -> float:
        """
        ETF 기본 점수 계산
        수익률(40%), 총보수(20%), 거래량(20%), 변동성(20%) 가중합
        """
        # 수익률 (1년 수익률 우선, 없으면 3개월 수익률)
        returns = etf_data.get('시세분석', {})
        return_1y = returns.get('1년 수익률')
        return_3m = returns.get('3개월 수익률')
        return_value = return_1y if return_1y is not None else return_3m
        normalized_return = self.normalize_return(return_value)
        
        # 총보수
        perf_data = etf_data.get('수익률/보수', {})
        fee_value = safe_float(perf_data.get('총 보수'))
        normalized_fee = self.normalize_fee(fee_value)
        
        # 거래량
        aum_data = etf_data.get('자산규모/유동성', {})
        volume_value = safe_float(aum_data.get('평균 거래량'))
        normalized_volume = self.normalize_volume(volume_value)
        
        # 변동성
        risk_data = etf_data.get('위험', {})
        volatility_grade = risk_data.get('변동성', '보통')
        normalized_volatility = self.normalize_volatility(volatility_grade)
        
        # 가중합 계산
        base_score = (
            normalized_return * 0.4 +      # 수익률 40%
            normalized_fee * 0.2 +         # 총보수 20%
            normalized_volume * 0.2 +      # 거래량 20%
            normalized_volatility * 0.2    # 변동성 20%
        )
        
        return base_score
    
    def calculate_type_weight_cache(self, row: pd.Series, investor_type: str) -> float:
        """투자자 유형별 가중치 계산 """
        if investor_type not in self.config.INVESTOR_TYPE_WEIGHTS:
            return 1.0
        
        type_weights = self.config.INVESTOR_TYPE_WEIGHTS[investor_type]
        total_weight = 0.0
        
        for dimension, weight in type_weights.items():
            dimension_score = 0.0
            
            if dimension == 'A':  # Auto-driven: 자산규모 중시
                aum = safe_float(row.get('자산규모', 0))
                if aum >= 1000000:  # 1조원 이상
                    dimension_score = 1.0
                elif aum >= 500000:  # 5000억원 이상
                    dimension_score = 0.7
                elif aum >= 100000:  # 1000억원 이상
                    dimension_score = 0.4
                else:
                    dimension_score = 0.1
                    
            elif dimension == 'I':  # Investigator: 중간 규모 선호
                aum = safe_float(row.get('자산규모', 0))
                if 100000 <= aum <= 500000:  # 1000억~5000억
                    dimension_score = 1.0
                elif aum >= 50000:  # 500억 이상
                    dimension_score = 0.6
                else:
                    dimension_score = 0.2
                    
            elif dimension == 'R':  # Risk-averse: 낮은 변동성 선호
                volatility = row.get('변동성', '보통')
                if volatility == '매우낮음':
                    dimension_score = 1.0
                elif volatility == '낮음':
                    dimension_score = 0.8
                elif volatility == '보통':
                    dimension_score = 0.5
                elif volatility == '높음':
                    dimension_score = 0.2
                else:  # 매우높음
                    dimension_score = 0.0
                    
            elif dimension == 'E':  # Enterprising: 높은 변동성 선호
                volatility = row.get('변동성', '보통')
                if volatility == '매우높음':
                    dimension_score = 1.0
                elif volatility == '높음':
                    dimension_score = 0.8
                elif volatility == '보통':
                    dimension_score = 0.5
                elif volatility == '낮음':
                    dimension_score = 0.2
                else:  # 매우낮음
                    dimension_score = 0.0
                    
            elif dimension == 'S':  # Story: 테마/섹터 ETF 선호
                classification = row.get('분류체계', '')
                if any(keyword in classification for keyword in ['업종테마', '전략테마', '섹터']):
                    dimension_score = 1.0
                elif any(keyword in classification for keyword in ['업종', '테마']):
                    dimension_score = 0.6
                else:
                    dimension_score = 0.2
                    
            elif dimension == 'T':  # Technical: 시장대표 ETF 선호
                classification = row.get('분류체계', '')
                if '시장대표' in classification:
                    dimension_score = 1.0
                elif any(keyword in classification for keyword in ['지수', '인덱스']):
                    dimension_score = 0.6
                else:
                    dimension_score = 0.3
                    
            elif dimension == 'B':  # Buy&Hold: 낮은 거래량 선호 (장기보유)
                volume = safe_float(row.get('거래량', 0))
                if volume <= 10000:
                    dimension_score = 1.0
                elif volume <= 50000:
                    dimension_score = 0.7
                elif volume <= 100000:
                    dimension_score = 0.4
                else:
                    dimension_score = 0.1
                    
            elif dimension == 'P':  # Portfolio Tuner: 높은 거래량 선호
                volume = safe_float(row.get('거래량', 0))
                if volume >= 100000:
                    dimension_score = 1.0
                elif volume >= 50000:
                    dimension_score = 0.7
                elif volume >= 10000:
                    dimension_score = 0.4
                else:
                    dimension_score = 0.1
            
            total_weight += weight * dimension_score
        
        return max(total_weight, 0.1)  # 최소 0.1 보장

    def fast_recommend_etfs(
        self,
        user_profile: dict,
        cache_df: pd.DataFrame,
        category_keyword: str,
        top_n: int = 5
    ) -> List[Dict]:
        """
        캐시 기반 ETF 추천
        """
        # 카테고리 필터
        mask = cache_df['분류체계'].str.contains(category_keyword, na=False) | cache_df['기초지수'].str.contains(category_keyword, na=False)
        filtered = cache_df[mask]
        
        # 빈 DataFrame 체크
        if filtered.empty:
            return []
        
        # 프로필 필터 (레벨 타입 변환 처리)
        user_level = user_profile['level']
        if isinstance(user_level, str) and user_level.startswith('level'):
            user_level = int(user_level[-1])  # "level1" -> 1
        
        filtered = filtered[
            (filtered['level'] == user_level) &
            (filtered['investor_type'] == user_profile['investor_type'])
        ]
        
        # 필터링 후에도 빈 DataFrame 체크
        if filtered.empty:
            return []
        
        # 가중치 재계산(구간별)
        filtered = filtered.copy()
        
        # apply 함수의 결과를 명시적으로 처리
        try:
            type_weights = filtered.apply(
                lambda row: self.calculate_type_weight_cache(row, user_profile['investor_type']), 
                axis=1
            )
            # 결과가 Series인지 확인하고 DataFrame에 할당
            if isinstance(type_weights, pd.Series):
                filtered.loc[:, 'type_weight'] = type_weights
            else:
                filtered.loc[:, 'type_weight'] = 1.0
                
        except Exception as e:
            print(f"Type weight calculation error: {e}")
            filtered.loc[:, 'type_weight'] = 1.0
        
        filtered.loc[:, 'final_score'] = filtered['base_score'] * filtered['type_weight']
        top_etfs = filtered.sort_values('final_score', ascending=False).head(top_n)
        # Dict 리스트로 반환
        return top_etfs.to_dict('records')

    def generate_recommendation_explanation(
        self,
        recommendations: List[Dict],
        user_profile: dict,
        category_keyword: str,
        context_docs: Optional[List[str]] = None
    ) -> str:
        if not recommendations:
            return "해당 카테고리의 ETF를 찾을 수 없습니다."
        etf_info_list = []
        for i, rec in enumerate(recommendations, 1):
            etf_info_list.append(f"""
{i}위: {rec['ETF명']}
- 최종점수: {rec['final_score']:.3f} (기본점수: {rec['base_score']:.3f}, 유형가중치: {rec['type_weight']:.3f})
- 분류체계: {rec.get('분류체계', 'N/A')}
- 기초지수: {rec.get('기초지수', 'N/A')}
""")
        etf_info_text = "\n".join(etf_info_list)
        config = Config()
        prompt = f"""
{config.get_recommend_prompt(user_profile)}

사용자 요청: {category_keyword if category_keyword else "ETF 추천"}
사용자 레벨: {user_profile.get('level', 1)}
투자자 유형: {user_profile.get('investor_type', 'ARSB')}

추천 ETF 목록:
{etf_info_text}
"""
        if context_docs:
            prompt += "\n[참고 문서]\n" + "\n".join(context_docs)
        prompt += "\n위 추천 ETF들에 대해 다음을 포함하여 설명해주세요:\n1. 각 ETF의 주요 특징과 장점\n2. 사용자의 투자 유형에 맞는 이유\n3. 투자 시 고려사항과 주의점\n4. 사용자 레벨에 맞는 실전 투자 팁\n5. 분류체계와 참고지수를 고려한 정확한 분석\n"
        return prompt
