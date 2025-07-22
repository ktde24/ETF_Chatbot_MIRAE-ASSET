import streamlit as st
import pandas as pd
import sys, os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbot.etf_analysis import analyze_etf, LEVEL_PROMPTS, extract_etf_name, plot_etf_bar, plot_etf_summary_bar
from chatbot.clova_client import ClovaClient
from chatbot.recommendation_engine import ETFRecommendationEngine
from chatbot.etf_comparison import ETFComparison
from chatbot.config import Config
# VectorSearcher 제거 - RAG 미사용
import numpy as np

# 데이터 로드
price_df = pd.read_csv("data/ETF_시세_데이터_20230101_20250721.csv")
info_df = pd.read_csv("data/상품검색.csv")
perf_df = pd.read_csv("data/수익률 및 총보수(기간).csv")
aum_df = pd.read_csv("data/자산규모 및 유동성(기간).csv")
ref_idx_df = pd.read_csv("data/참고지수(기간).csv")
risk_df = pd.read_csv("data/투자위험(기간).csv")

st.set_page_config(page_title="ETF RAG 챗봇", layout="wide")
st.title("💬 ETF RAG 챗봇")

# Clova API 키 입력
clova_api_key = st.sidebar.text_input("CLOVA API Key", type="password")
if clova_api_key:
    st.session_state.clova_api_key = clova_api_key

# 사용자 레벨 선택
level_map = {"Level 1": "level1", "Level 2": "level2", "Level 3": "level3"}
level_display = st.sidebar.selectbox(
    "레벨을 선택하세요",
    list(level_map.keys()),
    index=1
)
user_level = level_map[level_display]

# 투자자 유형 선택
investor_type_map = {
    "ARSB": "Auto-driven, Risk-averse, Story, Buy&Hold",
    "ARSE": "Auto-driven, Risk-averse, Story, Portfolio Tuner", 
    "ARTB": "Auto-driven, Risk-averse, Technical, Buy&Hold",
    "ARTE": "Auto-driven, Risk-averse, Technical, Portfolio Tuner",
    "AETB": "Auto-driven, Enterprising, Technical, Buy&Hold",
    "AETE": "Auto-driven, Enterprising, Technical, Portfolio Tuner",
    "AESB": "Auto-driven, Enterprising, Story, Buy&Hold",
    "AESE": "Auto-driven, Enterprising, Story, Portfolio Tuner",
    "IRSB": "Investigator, Risk-averse, Story, Buy&Hold",
    "IRSE": "Investigator, Risk-averse, Story, Portfolio Tuner",
    "IRTB": "Investigator, Risk-averse, Technical, Buy&Hold", 
    "IRTE": "Investigator, Risk-averse, Technical, Portfolio Tuner",
    "IETB": "Investigator, Enterprising, Technical, Buy&Hold",
    "IETE": "Investigator, Enterprising, Technical, Portfolio Tuner",
    "IESB": "Investigator, Enterprising, Story, Buy&Hold",
    "IESE": "Investigator, Enterprising, Story, Portfolio Tuner"
}

investor_type_display = st.sidebar.selectbox(
    "투자자 유형을 선택하세요",
    list(investor_type_map.keys()),
    format_func=lambda x: f"{x}: {investor_type_map[x]}",
    index=0
)
user_investor_type = investor_type_display

clova_client = ClovaClient()
recommendation_engine = ETFRecommendationEngine()
comparison_engine = ETFComparison()
    # vector_searcher = VectorSearcher()  # RAG 미사용  # RAG 검색 엔진 (선택적)

# 챗 UI
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown(
    """
    <style>
    .user-msg {background-color:#e1ffc7; border-radius:10px; padding:8px 12px; margin:4px 0; text-align:right;}
    .bot-msg {background-color:#f1f0f0; border-radius:10px; padding:8px 12px; margin:4px 0; text-align:left;}
    </style>
    """, unsafe_allow_html=True
)

user_input = st.text_input("질문을 입력하세요!", key="user_input")
if user_input:
    # 레벨 숫자 변환
    level_num = Config.get_level_number(user_level)
    user_profile = {"level": level_num, "investor_type": user_investor_type}
    
    # 요청 유형 확인
    recommend_keywords = ["추천", "추천해줘", "추천해주세요", "추천해주", "추천해"]
    compare_keywords = ["비교", "비교해줘", "비교해주세요", "vs", "대", "차이", "어떤게", "어느게"]
    
    is_recommendation = any(keyword in user_input for keyword in recommend_keywords)
    is_comparison = any(keyword in user_input for keyword in compare_keywords)
    
    if is_recommendation:
        # ETF 추천 처리
        # 개수 추출 (예: "반도체 ETF 5개 추천해줘" → 5)
        number_match = re.search(r'(\d+)개', user_input)
        top_n = int(number_match.group(1)) if number_match else 5
        
        # 카테고리 키워드 추출 (ETF 앞의 단어들)
        category_keyword = ""
        etf_match = re.search(r'(.+?)\s*ETF', user_input)
        if etf_match:
            category_keyword = etf_match.group(1).strip()
        
        # 추천 실행 (CSV 데이터만 사용, RAG 미사용)
        context_docs = None
        cache_df = pd.read_csv('data/etf_scores_cache.csv', encoding='utf-8-sig')
        recommendations = recommendation_engine.fast_recommend_etfs(
            user_profile, cache_df, category_keyword=category_keyword, top_n=top_n
        )
        
        if recommendations:
            # 추천 결과 설명 생성
            explanation_prompt = recommendation_engine.generate_recommendation_explanation(
                recommendations, user_profile, category_keyword, context_docs=context_docs
            )
            clova_answer = clova_client.generate_response(explanation_prompt)
        else:
            clova_answer = f"'{category_keyword}' 조건에 맞는 ETF를 찾을 수 없습니다. 다른 키워드로 다시 시도해보세요."
        
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", clova_answer))
        
    elif is_comparison:
        # ETF 비교 처리
        # ETF명들 추출 (쉼표, "vs", "대" 등으로 구분)
        etf_names = []
        
        separators = [',', ' vs ', ' 대 ', ' VS ', '랑', ' 랑 ', ' 와 ', ' 과 ', '/']
        text = user_input
        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                st.write(f"분리 결과: {parts}")
                etf_names = [part.strip() for part in parts if part.strip()]
    
                cleaned_etf_names = []
                for name in etf_names:
                    clean_name = name
                    for keyword in compare_keywords:
                        clean_name = clean_name.replace(keyword, '').strip()
                    if clean_name:  # 빈 문자열이 아니면 추가
                        cleaned_etf_names.append(clean_name)
                etf_names = cleaned_etf_names
                st.write(f"필터링 후: {etf_names}")
                break
        
        # 구분자가 없으면 키워드 기반으로 ETF명 추출
        if not etf_names:
            # 비교 키워드 제거
            clean_text = user_input
            for keyword in compare_keywords:
                clean_text = clean_text.replace(keyword, ' ')
            
            # ETF명 후보 추출 
            words = [w.strip() for w in clean_text.split() if len(w.strip()) > 2]
            etf_candidates = []
            
            # 각 단어로 ETF 검색
            for word in words:
                matches = info_df[info_df['종목명'].str.contains(word, case=False, na=False)]
                for _, match in matches.iterrows():
                    etf_name = match['종목명']
                    if etf_name not in etf_candidates:
                        etf_candidates.append(etf_name)
            
            etf_names = etf_candidates[:6]  # 최대 6개
        
        # 디버깅 정보 출력
        if etf_names:
            st.write(f"ETF: {etf_names}")
        
        if len(etf_names) >= 2:
            # ETF 비교 실행
            comparison_result = comparison_engine.compare_etfs(
                etf_names, user_profile, price_df, info_df, 
                perf_df, aum_df, ref_idx_df, risk_df
            )
            
            if 'error' in comparison_result:
                clova_answer = comparison_result['error']
                st.session_state.chat_history.append(("user", user_input))
                st.session_state.chat_history.append(("bot", clova_answer))
            else:
                # LLM 프롬프트 생성
                level_prompt = LEVEL_PROMPTS.get(level_num, "")
                
                comparison_prompt = f"""{level_prompt}
아래 ETF 비교 분석 결과를 바탕으로 사용자에게 맞춤형 분석과 추천사항을 제공해주세요.

{comparison_result['recommendations']}

다음 내용을 포함해서 설명해주세요:
1. 사용자 프로필에 맞는 최적의 ETF 선택 가이드
2. 각 ETF의 장단점 비교
3. 투자 시 주의사항과 실전 팁
4. 구체적인 투자 전략 제안

사용자의 레벨에 맞는 어투와 깊이로 작성하고, 데이터 기반 근거를 포함해주세요.
                """
                
                clova_answer = clova_client.generate_response(comparison_prompt)
                
                # 채팅 히스토리에 추가
                st.session_state.chat_history.append(("user", user_input))
                st.session_state.chat_history.append(("bot", clova_answer))
                
                # 비교 테이블과 시각화 출력
                st.subheader("상세 비교 테이블")
                st.dataframe(comparison_result['comparison_table'], use_container_width=True)
                
                # 시각화
                visualizations = comparison_result['visualizations']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(visualizations['score_bar'], use_container_width=True)
                with col2:
                    st.plotly_chart(visualizations['risk_return_scatter'], use_container_width=True)
                
                st.plotly_chart(visualizations['radar_chart'], use_container_width=True)
                
                col3, col4 = st.columns(2)
                with col3:
                    st.plotly_chart(visualizations['returns_comparison'], use_container_width=True)
                with col4:
                    st.plotly_chart(visualizations['cost_performance'], use_container_width=True)
                
                st.plotly_chart(visualizations['heatmap'], use_container_width=True)
        else:
            clova_answer = "비교할 ETF를 2개 이상 명확히 입력해주세요. (예: 'KODEX 200 vs TIGER 200 비교해줘')"
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("bot", clova_answer))
    
    else:
        # 일반 ETF 분석 처리
        etf_name = extract_etf_name(user_input.strip(), info_df)
        etf_info = analyze_etf(
            etf_name, user_profile,
            price_df, info_df, perf_df, aum_df, ref_idx_df, risk_df
        )
        
        # Clova 프롬프트 생성 및 답변
        level_prompt = LEVEL_PROMPTS.get(level_num, "")
        clova_prompt = f"""{level_prompt}
아래 ETF의 시세 데이터(수익률, 변동성, 최대낙폭), 공식 수익률/보수, 자산규모, 거래량, 위험 등 모든 정보를 종합적으로 분석해줘.
- 장점/단점, 투자자 유형별 적합성, 투자 전략, 리스크 요인 등도 포함해서 설명해줘.
- 수치와 근거를 반드시 포함해서, 투자 판단에 도움이 되게 해줘.
- 공식 데이터(수익률, 보수, 자산규모, 거래량 등)도 반드시 설명에 포함해줘.
- 설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성해줘.
- 예시, 비유, 실전 투자 팁도 포함해줘.
ETF 정보:
{etf_info}
"""
        clova_answer = clova_client.generate_response(clova_prompt)
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", clova_answer))

# 채팅 히스토리 출력
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f'<div class="user-msg">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg}</div>', unsafe_allow_html=True)

# 시각화: 값이 모두 None/N/A면 안내 (비교 모드가 아닐 때만)
if user_input and not is_comparison and not is_recommendation:
    # etf_info는 이미 위에서 생성되었으므로 재사용
    시세분석 = etf_info.get('시세분석', {})
    if not 시세분석 or all(v is None or (isinstance(v, float) and np.isnan(v)) for v in 시세분석.values()):
        st.warning("해당 ETF의 시세 데이터가 부족하거나, 수익률/변동성/최대낙폭을 계산할 수 없습니다.")
    else:
        st.plotly_chart(plot_etf_bar(etf_info), use_container_width=True)
    # 공식 데이터 바 차트는 항상 출력
    st.plotly_chart(plot_etf_summary_bar(etf_info), use_container_width=True)




