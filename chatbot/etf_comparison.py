"""
ETF 비교 분석 모듈
: 사용자 레벨/투자 유형에 맞는 여러 ETF 비교
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from typing import List, Dict, Any, Optional, Tuple
from .etf_analysis import analyze_etf, normalize_etf_name, extract_etf_name, LEVEL_PROMPTS
from .recommendation_engine import ETFRecommendationEngine
from .config import Config

class ETFComparison:
    """ETF 비교 분석 클래스"""
    
    def __init__(self):
        self.engine = ETFRecommendationEngine()
        self.config = Config()
    
    def compare_etfs(self, etf_names: List[str], user_profile: Dict[str, Any], 
                    price_df: pd.DataFrame, info_df: pd.DataFrame, 
                    perf_df: pd.DataFrame, aum_df: pd.DataFrame, 
                    ref_idx_df: pd.DataFrame, risk_df: pd.DataFrame) -> Dict[str, Any]:
        """
        여러 ETF를 사용자 프로필에 맞게 비교 분석
        """
        if len(etf_names) < 2:
            return {'error': 'ETF 비교를 위해서는 최소 2개 이상의 ETF가 필요합니다.'}
        
        if len(etf_names) > 6:
            return {'error': 'ETF 비교는 최대 6개까지만 가능합니다.'}
        
        # 1. 각 ETF 개별 분석
        etf_data_list = []
        valid_etfs = []
        
        for etf_name in etf_names:
            # ETF명 정규화
            clean_name = extract_etf_name(etf_name, info_df)
            etf_data = analyze_etf(clean_name, user_profile, price_df, info_df, 
                                 perf_df, aum_df, ref_idx_df, risk_df)
            
            if '설명' in etf_data and '찾을 수 없습니다' in etf_data['설명']:
                continue
                
            etf_data_list.append(etf_data)
            valid_etfs.append(etf_data['ETF명'])
        
        if len(valid_etfs) < 2:
            return {'error': f'비교 가능한 ETF가 {len(valid_etfs)}개뿐입니다. 최소 2개 이상 필요합니다.'}
        
        # 2. 점수 계산 및 순위
        scored_etfs = []
        for etf_data in etf_data_list:
            base_score = self.engine.calculate_base_score(etf_data)
            # info_df에서 해당 ETF 정보 찾기
            etf_matches = info_df[info_df['종목명'] == etf_data['ETF명']]
            if etf_matches.empty:
                continue
            etf_row = etf_matches.iloc[0]
            type_weight = self.engine.calculate_type_weight_cache(etf_row, user_profile['investor_type'])
            final_score = base_score * type_weight
            
            scored_etfs.append({
                'etf_data': etf_data,
                'base_score': base_score,
                'type_weight': type_weight,
                'final_score': final_score,
                'rank': 0  # 나중에 설정
            })
        
        # 점수순 정렬 및 순위 부여
        scored_etfs.sort(key=lambda x: x['final_score'], reverse=True)
        for i, etf in enumerate(scored_etfs):
            etf['rank'] = i + 1
        
        # 3. 비교 분석 결과 생성
        comparison_result = {
            'user_profile': user_profile,
            'etf_count': len(scored_etfs),
            'etfs': scored_etfs,
            'comparison_table': self._create_comparison_table(scored_etfs),
            'visualizations': self._create_visualizations(scored_etfs, user_profile),
            'summary': self._create_summary(scored_etfs, user_profile),
            'recommendations': self._create_recommendations(scored_etfs, user_profile)
        }
        
        return comparison_result
    
    def _create_comparison_table(self, scored_etfs: List[Dict]) -> pd.DataFrame:
        """비교 테이블 생성"""
        table_data = []
        
        for etf in scored_etfs:
            etf_data = etf['etf_data']
            시세분석 = etf_data.get('시세분석', {})
            수익률보수 = etf_data.get('수익률/보수', {})
            자산규모 = etf_data.get('자산규모/유동성', {})
            위험 = etf_data.get('위험', {})
            
            row = {
                'ETF명': etf_data['ETF명'],
                '순위': etf['rank'],
                '종합점수': f"{etf['final_score']:.3f}",
                '1년수익률(%)': f"{시세분석.get('1년 수익률', 0):.2f}" if 시세분석.get('1년 수익률') else 'N/A',
                '3개월수익률(%)': f"{시세분석.get('3개월 수익률', 0):.2f}" if 시세분석.get('3개월 수익률') else 'N/A',
                '총보수(%)': f"{float(수익률보수.get('총 보수', 0)):.3f}" if 수익률보수.get('총 보수') else 'N/A',
                '자산규모(억원)': f"{float(자산규모.get('평균 순자산총액', 0))/100:.0f}" if 자산규모.get('평균 순자산총액') else 'N/A',
                '거래량': f"{float(자산규모.get('평균 거래량', 0)):,.0f}" if 자산규모.get('평균 거래량') else 'N/A',
                '변동성': 위험.get('변동성', 'N/A'),
                '최대낙폭(%)': f"{시세분석.get('최대낙폭', 0):.2f}" if 시세분석.get('최대낙폭') else 'N/A'
            }
            table_data.append(row)
        
        return pd.DataFrame(table_data)
    
    def _create_visualizations(self, scored_etfs: List[Dict], user_profile: Dict) -> Dict[str, go.Figure]:
        """시각화 생성"""
        visualizations = {}
        
        # 1. 종합 점수 바 차트
        visualizations['score_bar'] = self._create_score_bar_chart(scored_etfs)
        
        # 2. 수익률 vs 위험 산점도
        visualizations['risk_return_scatter'] = self._create_risk_return_scatter(scored_etfs)
        
        # 3. 레이더 차트 (다차원 비교)
        visualizations['radar_chart'] = self._create_radar_chart(scored_etfs)
        
        # 4. 히트맵 (상관관계)
        visualizations['heatmap'] = self._create_correlation_heatmap(scored_etfs)
        
        # 5. 수익률 시계열 비교 
        visualizations['returns_comparison'] = self._create_returns_comparison(scored_etfs)
        
        # 6. 비용 vs 성과 분석
        visualizations['cost_performance'] = self._create_cost_performance_chart(scored_etfs)
        
        return visualizations
    
    def _create_score_bar_chart(self, scored_etfs: List[Dict]) -> go.Figure:
        """종합 점수 바 차트"""
        etf_names = [etf['etf_data']['ETF명'] for etf in scored_etfs]
        scores = [etf['final_score'] for etf in scored_etfs]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'][:len(etf_names)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=etf_names,
            y=scores,
            marker_color=colors,
            text=[f"{score:.3f}" for score in scores],
            textposition='auto',
            name='종합점수'
        ))
        
        fig.update_layout(
            title="🏆 ETF 종합 점수 비교",
            xaxis_title="ETF",
            yaxis_title="종합 점수",
            template="plotly_white",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            showlegend=False,
            height=400
        )
        
        return fig
    
    def _create_risk_return_scatter(self, scored_etfs: List[Dict]) -> go.Figure:
        """수익률 vs 위험 산점도"""
        fig = go.Figure()
        
        for i, etf in enumerate(scored_etfs):
            etf_data = etf['etf_data']
            시세분석 = etf_data.get('시세분석', {})
            위험 = etf_data.get('위험', {})
            
            # 수익률 (1년 우선, 없으면 3개월)
            return_val = 시세분석.get('1년 수익률') or 시세분석.get('3개월 수익률') or 0
            
            # 변동성을 숫자로 변환
            volatility_map = {'매우낮음': 1, '낮음': 2, '보통': 3, '높음': 4, '매우높음': 5}
            risk_val = volatility_map.get(위험.get('변동성', '보통'), 3)
            
            fig.add_trace(go.Scatter(
                x=[risk_val],
                y=[return_val],
                mode='markers+text',
                marker=dict(size=15, opacity=0.7),
                text=[etf_data['ETF명'][:10] + '...'],
                textposition="top center",
                name=etf_data['ETF명'],
                hovertemplate=f"<b>{etf_data['ETF명']}</b><br>" +
                             f"수익률: {return_val:.2f}%<br>" +
                             f"위험도: {위험.get('변동성', 'N/A')}<br>" +
                             f"점수: {etf['final_score']:.3f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="📈 수익률 vs 위험도 분석",
            xaxis_title="위험도 (1:매우낮음 ~ 5:매우높음)",
            yaxis_title="수익률 (%)",
            template="plotly_white",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            showlegend=False,
            height=500
        )
        
        return fig
    
    def _create_radar_chart(self, scored_etfs: List[Dict]) -> go.Figure:
        """레이더 차트 (다차원 비교)"""
        fig = go.Figure()
        
        categories = ['수익률', '비용효율성', '유동성', '안정성', '규모']
        
        for etf in scored_etfs:
            etf_data = etf['etf_data']
            시세분석 = etf_data.get('시세분석', {})
            수익률보수 = etf_data.get('수익률/보수', {})
            자산규모 = etf_data.get('자산규모/유동성', {})
            위험 = etf_data.get('위험', {})
            
            # 각 지표를 0-100 스케일로 정규화 (None 값 처리)
            return_val = 시세분석.get('1년 수익률') or 시세분석.get('3개월 수익률') or 0
            if return_val is None or return_val == '':
                return_val = 0
            try:
                return_val = float(return_val)
            except (ValueError, TypeError):
                return_val = 0
            return_score = max(0, min(100, (return_val + 50) * 2))  # -50%~50% → 0~100
            
            fee_val = 수익률보수.get('총 보수')
            if fee_val is None or fee_val == '':
                fee_val = 1.0
            else:
                try:
                    fee_val = float(fee_val)
                except (ValueError, TypeError):
                    fee_val = 1.0
            cost_score = max(0, min(100, (2 - fee_val) * 50))  # 2%~0% → 0~100
            
            volume_val = 자산규모.get('평균 거래량')
            if volume_val is None or volume_val == '':
                volume_val = 0
            else:
                try:
                    volume_val = float(volume_val)
                except (ValueError, TypeError):
                    volume_val = 0
            liquidity_score = max(0, min(100, volume_val / 10000))  # 0~1M → 0~100
            
            volatility_map = {'매우높음': 20, '높음': 40, '보통': 60, '낮음': 80, '매우낮음': 100}
            stability_score = volatility_map.get(위험.get('변동성', '보통'), 60)
            
            aum_val = 자산규모.get('평균 순자산총액')
            if aum_val is None or aum_val == '':
                aum_val = 0
            else:
                try:
                    aum_val = float(aum_val)
                except (ValueError, TypeError):
                    aum_val = 0
            size_score = max(0, min(100, aum_val / 10000))  # 0~1조원 → 0~100
            
            values = [return_score, cost_score, liquidity_score, stability_score, size_score]
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # 닫힌 도형을 위해 첫 값 반복
                theta=categories + [categories[0]],
                fill='toself',
                name=etf_data['ETF명'],
                opacity=0.6
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            title="🕸️ ETF 다차원 비교 (레이더 차트)",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            height=600
        )
        
        return fig
    
    def _create_correlation_heatmap(self, scored_etfs: List[Dict]) -> go.Figure:
        """상관관계 히트맵"""
        # 주요 지표들 추출
        data_matrix = []
        etf_names = []
        
        for etf in scored_etfs:
            etf_data = etf['etf_data']
            etf_names.append(etf_data['ETF명'][:15])
            
            시세분석 = etf_data.get('시세분석', {})
            수익률보수 = etf_data.get('수익률/보수', {})
            자산규모 = etf_data.get('자산규모/유동성', {})
            
            row = [
                시세분석.get('1년 수익률', 0) or 0,
                float(수익률보수.get('총 보수', 1)) if 수익률보수.get('총 보수') else 1,
                float(자산규모.get('평균 거래량', 0)) if 자산규모.get('평균 거래량') else 0,
                시세분석.get('변동성', 0) or 0,
                etf['final_score']
            ]
            data_matrix.append(row)
        
        df = pd.DataFrame(data_matrix, 
                         columns=['수익률', '총보수', '거래량', '변동성', '종합점수'],
                         index=etf_names)
        
        # 상관계수 계산
        corr_matrix = df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdYlBu',
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="🔥 지표 간 상관관계 히트맵",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            height=500
        )
        
        return fig
    
    def _create_returns_comparison(self, scored_etfs: List[Dict]) -> go.Figure:
        """수익률 비교 차트"""
        fig = go.Figure()
        
        periods = ['3개월', '1년']
        etf_names = [etf['etf_data']['ETF명'] for etf in scored_etfs]
        
        for period in periods:
            returns = []
            for etf in scored_etfs:
                시세분석 = etf['etf_data'].get('시세분석', {})
                return_val = 시세분석.get(f'{period} 수익률', 0) or 0
                returns.append(return_val)
            
            fig.add_trace(go.Bar(
                name=f'{period} 수익률',
                x=etf_names,
                y=returns,
                text=[f"{r:.1f}%" for r in returns],
                textposition='auto'
            ))
        
        fig.update_layout(
            title="📊 기간별 수익률 비교",
            xaxis_title="ETF",
            yaxis_title="수익률 (%)",
            barmode='group',
            template="plotly_white",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            height=400
        )
        
        return fig
    
    def _create_cost_performance_chart(self, scored_etfs: List[Dict]) -> go.Figure:
        """비용 vs 성과 분석"""
        fig = go.Figure()
        
        for i, etf in enumerate(scored_etfs):
            etf_data = etf['etf_data']
            시세분석 = etf_data.get('시세분석', {})
            수익률보수 = etf_data.get('수익률/보수', {})
            
            return_val = 시세분석.get('1년 수익률') or 시세분석.get('3개월 수익률') or 0
            if return_val is None:
                return_val = 0
                
            fee_val = 수익률보수.get('총 보수')
            if fee_val is None or fee_val == '':
                fee_val = 1.0
            else:
                try:
                    fee_val = float(fee_val)
                except (ValueError, TypeError):
                    fee_val = 1.0
            
            # 비용 대비 성과 비율
            cost_efficiency = return_val / fee_val if fee_val > 0 else 0
            
            fig.add_trace(go.Scatter(
                x=[fee_val],
                y=[return_val],
                mode='markers+text',
                marker=dict(
                    size=max(10, min(30, cost_efficiency * 2)),
                    opacity=0.7,
                    color=cost_efficiency,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="비용효율성")
                ),
                text=[etf_data['ETF명'][:8]],
                textposition="top center",
                name=etf_data['ETF명'],
                hovertemplate=f"<b>{etf_data['ETF명']}</b><br>" +
                             f"수익률: {return_val:.2f}%<br>" +
                             f"총보수: {fee_val:.3f}%<br>" +
                             f"비용효율성: {cost_efficiency:.1f}<extra></extra>"
            ))
        
        fig.update_layout(
            title="💰 비용 vs 성과 효율성 분석",
            xaxis_title="총보수 (%)",
            yaxis_title="1년 수익률 (%)",
            template="plotly_white",
            font=dict(size=12, family="Pretendard, NanumGothic"),
            showlegend=False,
            height=500
        )
        
        return fig
    
    def _create_summary(self, scored_etfs: List[Dict], user_profile: Dict) -> str:
        """기본 데이터 요약 (LLM이 해석할 원시 데이터)"""
        best_etf = scored_etfs[0]['etf_data']['ETF명']
        best_score = scored_etfs[0]['final_score']
        worst_etf = scored_etfs[-1]['etf_data']['ETF명']
        worst_score = scored_etfs[-1]['final_score']
        
        # ETF별 주요 지표 정리
        etf_summary = []
        for i, etf in enumerate(scored_etfs):
            etf_data = etf['etf_data']
            시세분석 = etf_data.get('시세분석', {})
            수익률보수 = etf_data.get('수익률/보수', {})
            자산규모 = etf_data.get('자산규모/유동성', {})
            위험 = etf_data.get('위험', {})
            
            summary_text = f"""
{i+1}위: {etf_data['ETF명']} (점수: {etf['final_score']:.3f})
- 1년 수익률: {시세분석.get('1년 수익률', 'N/A')}%
- 총보수: {수익률보수.get('총 보수', 'N/A')}%
- 자산규모: {자산규모.get('평균 순자산총액', 'N/A')}백만원
- 거래량: {자산규모.get('평균 거래량', 'N/A')}주
- 변동성: {위험.get('변동성', 'N/A')}
            """.strip()
            etf_summary.append(summary_text)
        
        return "\n\n".join(etf_summary)
    
    def _create_recommendations(self, scored_etfs: List[Dict], user_profile: Dict) -> str:
        """프롬프트용 데이터 정리"""
        level = user_profile.get('level', 2)
        investor_type = user_profile.get('investor_type', 'ARSB')
        
        # 투자자 유형 특성 정리
        type_characteristics = []
        if 'A' in investor_type:
            type_characteristics.append("자동화된 투자 선호")
        if 'I' in investor_type:
            type_characteristics.append("직접 조사/분석 선호")
        if 'R' in investor_type and investor_type[1] == 'R':
            type_characteristics.append("위험 회피 성향")
        elif 'E' in investor_type:
            type_characteristics.append("적극적 위험 감수")
        if 'S' in investor_type:
            type_characteristics.append("스토리/테마 중심 투자")
        elif 'T' in investor_type:
            type_characteristics.append("기술적 분석 중심")
        if 'B' in investor_type:
            type_characteristics.append("장기 보유 전략")
        elif investor_type[-1] == 'E':
            type_characteristics.append("포트폴리오 튜닝 선호")
        
        return f"""
사용자 프로필:
- 레벨: {level} ({'초급' if level == 1 else '중급' if level == 2 else '고급'})
- 투자자 유형: {investor_type} ({', '.join(type_characteristics)})

비교 결과:
{self._create_summary(scored_etfs, user_profile)}
        """.strip() 