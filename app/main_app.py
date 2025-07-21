import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbot.etf_analysis import analyze_etf, LEVEL_PROMPTS, extract_etf_name, plot_etf_bar, plot_etf_summary_bar
from chatbot.clova_client import ClovaClient
import numpy as np
import re

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

clova_client = ClovaClient()

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
    user_profile = {"level": user_level}
    etf_name = extract_etf_name(user_input.strip(), info_df)
    etf_info = analyze_etf(
        etf_name, user_profile,
        price_df, info_df, perf_df, aum_df, ref_idx_df, risk_df
    )
    # Clova 프롬프트 생성 및 답변
    level_num = int(user_level[-1]) if user_level.startswith('level') else 2
    level_prompt = LEVEL_PROMPTS.get(level_num, "")
    clova_prompt = f"""{level_prompt}\n아래 ETF의 시세 데이터(수익률, 변동성, 최대낙폭), 공식 수익률/보수, 자산규모, 거래량, 위험 등 모든 정보를 종합적으로 분석해줘.\n- 장점/단점, 투자자 유형별 적합성, 투자 전략, 리스크 요인 등도 포함해서 설명해줘.\n- 수치와 근거를 반드시 포함해서, 투자 판단에 도움이 되게 해줘.\n- 공식 데이터(수익률, 보수, 자산규모, 거래량 등)도 반드시 설명에 포함해줘.\n- 설명은 반드시 사용자의 레벨에 맞는 어투와 깊이로 작성해줘.\n- 예시, 비유, 실전 투자 팁도 포함해줘.\nETF 정보:\n{etf_info}\n"""
    clova_answer = clova_client.generate_response(clova_prompt)
    st.session_state.chat_history.append(("user", user_input))
    st.session_state.chat_history.append(("bot", clova_answer))

# 채팅 히스토리 출력
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f'<div class="user-msg">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg}</div>', unsafe_allow_html=True)

# 시각화: 값이 모두 None/N/A면 안내
시세분석 = etf_info.get('시세분석', {}) if user_input else {}
if user_input:
    if not 시세분석 or all(v is None or (isinstance(v, float) and np.isnan(v)) for v in 시세분석.values()):
        st.warning("해당 ETF의 시세 데이터가 부족하거나, 수익률/변동성/최대낙폭을 계산할 수 없습니다.")
    else:
        st.plotly_chart(plot_etf_bar(etf_info), use_container_width=True)
    # 공식 데이터 바 차트는 항상 출력
    st.plotly_chart(plot_etf_summary_bar(etf_info), use_container_width=True)




