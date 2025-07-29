"""
ETF 추천 엔진
- 사용자 레벨과 투자 유형에 맞는 ETF 추천
- 캐시 기반 고속 추천 시스템
- 투자자 유형별 가중치 적용
- 투자자 유형별 맞춤 점수 계산
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Optional

# 공통 유틸리티 임포트
from .config import Config
from .utils import (
    safe_float, filter_dataframe_by_keyword, 
    validate_user_profile, create_error_result
)

# 로깅 설정
logger = logging.getLogger(__name__)

class ETFRecommendationEngine:
    """ETF 추천 엔진 클래스"""
    
    def __init__(self):
        """추천 엔진 초기화"""
        self.config = Config()
        logger.info("ETF 추천 엔진 초기화 완료")

    def fast_recommend_etfs(
        self,
        user_profile: Dict[str, Any],
        cache_df: pd.DataFrame,
        category_keyword: str = "",
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        캐시 기반 고속 ETF 추천
        
        Args:
            user_profile: 사용자 프로필 {'level': int, 'investor_type': str}
            cache_df: 사전 계산된 ETF 캐시 데이터
            category_keyword: 카테고리 키워드 (예: "반도체")
            top_n: 추천할 ETF 개수
        
        Returns:
            추천 ETF 리스트 (Dict 형태)
        """
        try:
            # 1단계: 카테고리 필터링
            filtered = self._filter_by_category(cache_df, category_keyword)
            if filtered.empty:
                logger.warning(f"카테고리 '{category_keyword}'에 해당하는 ETF가 없습니다.")
                return [{
                    '안내': f"'{category_keyword}' 조건에 맞는 ETF를 찾을 수 없습니다. 다른 키워드로 다시 시도해보세요."
                }]

            # 2단계: 사용자 프로필 필터링
            filtered = self._filter_by_user_profile(filtered, user_profile)
            if filtered.empty:
                logger.warning(f"사용자 프로필에 맞는 ETF가 없습니다: {user_profile}")
                # 안내 메시지 반환
                user_level = user_profile.get('level', '알 수 없음')
                investor_type = user_profile.get('investor_type', '알 수 없음')
                return [{
                    '안내': f"현재 선택하신 투자 레벨(Level {user_level})과 투자자 유형({investor_type})에 적합한 ETF가 없습니다.\n\n- 투자 레벨이나 유형을 변경해서 다시 시도해보시거나,\n- 카테고리 키워드를 바꿔서 검색해보세요.\n\n(일부 테마/섹터 ETF는 초보자에게 추천되지 않을 수 있습니다.)"
                }]

            # 3단계: 점수 기반 정렬 및 상위 N개 선택
            top_etfs = self._select_top_etfs(filtered, top_n)
            
            logger.info(f"추천 완료: {len(top_etfs)}개 ETF")
            return top_etfs.to_dict('records')
        
        except Exception as e:
            logger.error(f"ETF 추천 중 오류 발생: {e}")
            return [{
                '안내': f"ETF 추천 중 오류가 발생했습니다: {e}"
            }]

    def _filter_by_category(self, cache_df: pd.DataFrame, category_keyword: str) -> pd.DataFrame:
        """
        카테고리 키워드로 ETF 필터링
        
        Args:
            cache_df: 캐시 데이터
            category_keyword: 카테고리 키워드
        
        Returns:
            필터링된 DataFrame
        """
        if not category_keyword.strip():
            return cache_df
        
        # ETF명, 분류체계, 기초지수에서 키워드 검색
        search_columns = ['ETF명', '분류체계', '기초지수']
        filtered = filter_dataframe_by_keyword(cache_df, category_keyword, search_columns)
        
        logger.info(f"카테고리 '{category_keyword}' 필터링: {len(cache_df)} → {len(filtered)}")
        return filtered

    def _filter_by_user_profile(self, cache_df: pd.DataFrame, user_profile: Dict[str, Any]) -> pd.DataFrame:
        """
        사용자 프로필로 ETF 필터링
        
        Args:
            cache_df: 카테고리 필터링된 데이터
            user_profile: 사용자 프로필
        
        Returns:
            사용자 프로필에 맞는 ETF DataFrame
        """
        user_level = self._normalize_user_level(user_profile.get('level'))
        investor_type = user_profile.get('investor_type', 'ARSB')

        # 타입 강제 변환
        cache_df = cache_df.copy()
        cache_df['level'] = cache_df['level'].astype(int)
        cache_df['investor_type'] = cache_df['investor_type'].astype(str)

        filtered = cache_df[
            (cache_df['level'] == user_level) &
            (cache_df['investor_type'] == investor_type)
        ]
        logger.info(f"사용자 프로필 필터링: Level {user_level}, {investor_type} → {len(filtered)}개")
        return filtered

    def _normalize_user_level(self, user_level: Any) -> int:
        """
        사용자 레벨 정규화 (기존 함수와의 호환성을 위해 유지)
        
        Args:
            user_level: 사용자 레벨 (int, str, 또는 기타)
        
        Returns:
            정규화된 레벨 (1, 2, 3)
        """
        validated_profile = validate_user_profile({'level': user_level})
        return validated_profile['level']

    def _select_top_etfs(self, filtered_df: pd.DataFrame, top_n: int) -> pd.DataFrame:
        """
        점수 기반으로 상위 N개 ETF 선택
        
        Args:
            filtered_df: 필터링된 ETF 데이터
            top_n: 선택할 ETF 개수
        
        Returns:
            상위 N개 ETF DataFrame
        """
        # final_score 컬럼 확인 및 대체 점수 생성
        if 'final_score' not in filtered_df.columns:
            filtered_df = self._generate_fallback_scores(filtered_df)
        
        # 점수 기준 내림차순 정렬 후 상위 N개 선택
        top_etfs = filtered_df.sort_values(
            'final_score', 
            ascending=False, 
            na_position='last'  
        ).head(top_n)
        
        logger.info(f"상위 {top_n}개 ETF 선택 완료")
        return top_etfs

    def _generate_fallback_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        final_score가 없는 경우 대체 점수 생성
        
        Args:
            df: ETF 데이터프레임
        
        Returns:
            점수가 추가된 DataFrame
        """
        df = df.copy()
        
        # base_score가 있으면 사용
        if 'base_score' in df.columns:
            df.loc[:, 'final_score'] = df['base_score']
            logger.info("base_score를 final_score로 사용")
            return df
        
        # Risk_Score가 있으면 역수로 변환 (낮은 위험 = 높은 점수)
        if 'Risk_Score' in df.columns:
            measurable = df[df['Risk_Score'].notna()]
            if not measurable.empty:
                max_risk = measurable['Risk_Score'].max()
                min_risk = measurable['Risk_Score'].min()
                
                if max_risk > min_risk:
                    # 위험도를 역수로 변환하여 점수 생성
                    df.loc[df['Risk_Score'].notna(), 'final_score'] = \
                        1 - (df.loc[df['Risk_Score'].notna(), 'Risk_Score'] - min_risk) / (max_risk - min_risk)
                    # 측정불가 ETF는 중간 점수 (보수적)
                    df.loc[df['Risk_Score'].isna(), 'final_score'] = 0.3
                else:
                    df.loc[:, 'final_score'] = 0.5
                
                logger.info("Risk_Score 기반 점수 생성")
                return df
        
        # 기본값: 모든 ETF에 동일한 점수
        df.loc[:, 'final_score'] = 0.5
        logger.warning("기본 점수(0.5) 적용")
        return df

    def generate_recommendation_explanation(
        self,
        recommendations: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        category_keyword: str,
        context_docs: Optional[List[str]] = None
    ) -> str:
        """
        추천 결과에 대한 설명 프롬프트 생성
        
        Args:
            recommendations: 추천된 ETF 리스트
            user_profile: 사용자 프로필
            category_keyword: 카테고리 키워드
            context_docs: 추가 참고 문서 (사용되지 않음)
        
        Returns:
            LLM용 설명 프롬프트
        """
        if not recommendations:
            return "해당 조건에 맞는 ETF를 찾을 수 없습니다. 다른 키워드로 다시 시도해보세요."
        
        # ETF 정보 포맷팅
        etf_info_list = []
        for i, rec in enumerate(recommendations, 1):
            etf_name = rec.get('ETF명', 'N/A')
            final_score = rec.get('final_score', 0)
            base_score = rec.get('base_score', final_score)
            type_weight = rec.get('type_weight', 1.0)
            classification = rec.get('분류체계', 'N/A')
            reference_index = rec.get('기초지수', 'N/A')
            risk_tier = rec.get('risk_tier', 'N/A')
            
            etf_info_list.append(f"""
{i}위: {etf_name}
- 최종점수: {final_score:.3f} (기본점수: {base_score:.3f}, 유형가중치: {type_weight:.3f})
- 위험등급: {risk_tier}
- 분류체계: {classification}
- 기초지수: {reference_index}
""")
        
        etf_info_text = "\n".join(etf_info_list)
        
        # 프롬프트 생성
        user_level = self._normalize_user_level(user_profile.get('level'))
        investor_type = user_profile.get('investor_type', 'ARSB')
        investor_description = self.config.get_investor_type_description(investor_type)
        
        prompt = f"""{self.config.get_recommendation_prompt(user_profile)}

사용자 정보:
- 요청 카테고리: {category_keyword if category_keyword else "ETF 추천"}
- 사용자 레벨: Level {user_level}
- 투자자 유형: {investor_type} ({investor_description})

추천 ETF 목록:
{etf_info_text}

위 추천 ETF들에 대해 다음을 포함하여 설명해주세요:
1. 각 ETF의 주요 특징과 장점
2. 사용자의 투자 레벨과 유형에 맞는 이유
3. 투자 시 고려사항과 주의점
4. 사용자 레벨에 맞는 실전 투자 팁
5. 분류체계와 참고지수를 고려한 정확한 분석
"""
        
        return prompt

    def calculate_type_weight_cache(self, row: pd.Series, investor_type: str) -> float:
        """
        투자자 유형별 가중치 계산 (캐시용)
        
        Args:
            row: ETF 정보 행
            investor_type: 투자자 유형 (ARSB, AETE 등)
        
        Returns:
            투자자 유형별 가중치 (0.1~1.0)
        """
        if investor_type not in self.config.INVESTOR_TYPE_WEIGHTS:
            logger.warning(f"알 수 없는 투자자 유형: {investor_type}")
            return 1.0
        
        type_weights = self.config.INVESTOR_TYPE_WEIGHTS[investor_type]
        total_weight = 0.0
        
        for dimension, weight in type_weights.items():
            dimension_score = self._calculate_dimension_score(row, dimension)
            total_weight += weight * dimension_score
        
        # 최소 0.1 보장
        return max(total_weight, 0.1)

    def _calculate_dimension_score(self, row: pd.Series, dimension: str) -> float:
        """
        개별 차원별 점수 계산
        
        Args:
            row: ETF 정보 행
            dimension: 투자 차원 (A, I, R, E, S, T, B, P)
        
        Returns:
            해당 차원의 점수 (0.0~1.0)
        """
        if dimension == 'A':  # Auto-driven: 자산규모 중시
            aum = safe_float(row.get('자산규모', 0))
            if aum >= 1000000:  # 1조원 이상
                return 1.0
            elif aum >= 500000:  # 5000억원 이상
                return 0.7
            elif aum >= 100000:  # 1000억원 이상
                return 0.4
            else:
                return 0.1
                
        elif dimension == 'I':  # Investigator: 중간 규모 선호
            aum = safe_float(row.get('자산규모', 0))
            if 100000 <= aum <= 500000:  # 1000억~5000억
                return 1.0
            elif aum >= 50000:  # 500억 이상
                return 0.6
            else:
                return 0.2
                
        elif dimension == 'R':  # Risk-averse: 낮은 변동성 선호
            volatility = row.get('변동성', '보통')
            volatility_scores = {
                '매우낮음': 1.0, '낮음': 0.8, '보통': 0.5, '높음': 0.2, '매우높음': 0.0
            }
            return volatility_scores.get(volatility, 0.5)
            
        elif dimension == 'E':  # Enterprising: 높은 변동성 선호
            volatility = row.get('변동성', '보통')
            volatility_scores = {
                '매우높음': 1.0, '높음': 0.8, '보통': 0.5, '낮음': 0.2, '매우낮음': 0.0
            }
            return volatility_scores.get(volatility, 0.5)
            
        elif dimension == 'S':  # Story: 테마/섹터 ETF 선호
            classification = row.get('분류체계', '')
            if any(keyword in classification for keyword in ['업종테마', '전략테마', '섹터']):
                return 1.0
            elif any(keyword in classification for keyword in ['업종', '테마']):
                return 0.6
            else:
                return 0.2
                
        elif dimension == 'T':  # Technical: 시장대표 ETF 선호
            classification = row.get('분류체계', '')
            if '시장대표' in classification:
                return 1.0
            elif any(keyword in classification for keyword in ['지수', '인덱스']):
                return 0.6
            else:
                return 0.3
                
        elif dimension == 'B':  # Buy&Hold: 낮은 거래량 선호 (장기보유)
            volume = safe_float(row.get('거래량', 0))
            if volume <= 10000:
                return 1.0
            elif volume <= 50000:
                return 0.7
            elif volume <= 100000:
                return 0.4
            else:
                return 0.1
                
        elif dimension == 'P':  # Portfolio Tuner: 높은 거래량 선호
            volume = safe_float(row.get('거래량', 0))
            if volume >= 100000:
                return 1.0
            elif volume >= 50000:
                return 0.7
            elif volume >= 10000:
                return 0.4
            else:
                return 0.1
        
        # 알 수 없는 차원
        return 0.5

    def calculate_base_score(self, etf_data: dict) -> float:
        """
        ETF 데이터에서 base_score를 반환 (없으면 0.5)
        """
        try:
            return float(etf_data.get('base_score', 0.5))
        except Exception:
            return 0.5
