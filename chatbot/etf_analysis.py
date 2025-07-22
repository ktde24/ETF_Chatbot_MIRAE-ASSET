import pandas as pd
import re
import numpy as np

# 레벨별 프롬프트
LEVEL_PROMPTS = {
    1: "- Level 1: 유치원/초1 스타일로 아주 쉽게, 비유와 예시 위주로 3줄 이하로 요약하세요.",
    2: "- Level 2: 중고등학생도 이해 가능한 쉬운 말로, 핵심 개념과 이유를 포함해 3줄 이하로 요약하세요.",
    3: "- Level 3: 고급 분석과 실전 활용 관점으로, 데이터 기반·비교·수치 등을 포함해 3줄 이하로 요약하세요."
}

def normalize_etf_name(name):
    """ETF 종목명을 정규화"""
    return re.sub(r'\s+', '', str(name)).lower()

def extract_etf_name(user_input, info_df):
    candidates = list(info_df['종목명'])
    norm_input = normalize_etf_name(user_input)
    for name in candidates:
        if normalize_etf_name(name) == norm_input:
            return name
    for name in candidates:
        if normalize_etf_name(name) in norm_input:
            return name
    cleaned = re.sub(r'(분석|설명|추천|해줘|알려줘|비교|차트|정보|ETF)', '', user_input, flags=re.I).strip()
    norm_cleaned = normalize_etf_name(cleaned)
    for name in candidates:
        if normalize_etf_name(name) == norm_cleaned:
            return name
    for name in candidates:
        if normalize_etf_name(name) in norm_cleaned:
            return name
    return user_input.strip()  # fallback

def find_etf_row(df, etf_name):
    norm_input = normalize_etf_name(etf_name)
    # 1. 종목명에서 찾기
    for idx, row in df.iterrows():
        if normalize_etf_name(row.get('종목명', '')) == norm_input:
            return row
    # 2. 종목코드에서 찾기
    for idx, row in df.iterrows():
        if normalize_etf_name(row.get('종목코드', '')) == norm_input:
            return row
    # 3. 부분일치(포함)도 허용
    for idx, row in df.iterrows():
        if norm_input in normalize_etf_name(row.get('종목명', '')):
            return row
    return None

def safe_fmt(val, suffix=""):
    """
    None-safe 포맷팅 함수. None이면 N/A, 아니면 소수점 2자리로 포맷
    """
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        return f"{float(val):.2f}{suffix}"
    except (ValueError, TypeError):
        return str(val)

def safe_float(val):
    """
    문자열, None, NaN 등 robust하게 float 변환. 변환 불가시 None 반환.
    """
    try:
        if val is None or str(val).strip() == '' or str(val).lower() == 'nan':
            return None
        return float(str(val).replace(',', '').strip())
    except Exception:
        return None

def get_exact_etf_info(user_input, info_df):
    norm_input = normalize_etf_name(user_input)
    for idx, row in info_df.iterrows():
        if normalize_etf_name(row['종목명']) == norm_input:
            return row['종목명'], str(row['종목코드'])
    # 부분일치 fallback
    for idx, row in info_df.iterrows():
        if norm_input in normalize_etf_name(row['종목명']):
            return row['종목명'], str(row['종목코드'])
    return None, None

def analyze_etf(etf_name, user_profile, price_df, info_df, perf_df, aum_df, ref_idx_df, risk_df):
    """
    입력 ETF명 → 상품검색.csv에서 종목명/코드 찾기 → 시세 데이터는 종목코드로만 조회
    """
    # 1. 상품검색.csv에서 정확한 종목명/코드 찾기
    exact_name, code = get_exact_etf_info(etf_name, info_df)
    if not exact_name or not code:
        return {
            'ETF명': etf_name, '기본정보': {}, '수익률/보수': {}, '자산규모/유동성': {},
            '참고지수': {}, '위험': {}, '시세분석': {},
            '설명': f"'{etf_name}'에 해당하는 ETF를 찾을 수 없습니다. ETF명을 다시 확인해 주세요."
        }
    # 2. 시세 데이터는 종목코드로만 조회
    etf_price = price_df[price_df['srtnCd'].astype(str) == str(code)].copy()
    if etf_price.empty:
        return {
            'ETF명': exact_name, '기본정보': {}, '수익률/보수': {}, '자산규모/유동성': {},
            '참고지수': {}, '위험': {}, '시세분석': {},
            '설명': f"'{exact_name}'에 대한 시세 데이터가 없습니다. ETF 시세 파일을 확인해 주세요."
        }
    # 날짜/중복/결측치 처리
    etf_price['date'] = pd.to_datetime(etf_price['basDt'], format='%Y%m%d', errors='coerce')
    # 종가를 숫자형으로 변환 (문자열 → float)
    etf_price['clpr'] = pd.to_numeric(etf_price['clpr'], errors='coerce')
    etf_price = etf_price.dropna(subset=['date', 'clpr'])
    etf_price = etf_price.drop_duplicates(subset=['date'])
    etf_price = etf_price.sort_values('date').reset_index(drop=True)

    returns, volatility, max_drawdown = {}, None, None
    시세분석_불가 = False
    if not etf_price.empty:
        def get_return(days):
            if len(etf_price) < days + 1: return None
            return (etf_price.iloc[-1]['clpr'] / etf_price.iloc[-days-1]['clpr'] - 1) * 100
        returns = {'3개월': get_return(63), '1년': get_return(252)}
        volatility = etf_price['clpr'].pct_change().std() * 100 if len(etf_price) > 1 else None
        roll_max = etf_price['clpr'].cummax()
        roll_max_safe = roll_max.replace(0, np.nan)
        drawdown = (etf_price['clpr'] - roll_max_safe) / roll_max_safe
        min_drawdown = drawdown.min() if not drawdown.empty else None
        if min_drawdown is not None and not pd.isna(min_drawdown):
            max_drawdown = min_drawdown * 100
        else:
            max_drawdown = None
        # 시세분석이 모두 None이면 안내 플래그
        if all(x is None for x in [returns.get('3개월'), returns.get('1년'), volatility, max_drawdown]):
            시세분석_불가 = True
    else:
        시세분석_불가 = True

    # 기타 정보는 항상 반환
    info_row = find_etf_row(info_df, exact_name)
    basic_info = dict(info_row) if info_row is not None else {}
    perf_row = find_etf_row(perf_df, exact_name)
    perf_info = dict(perf_row) if perf_row is not None else {}
    aum_row = find_etf_row(aum_df, exact_name)
    aum_info = dict(aum_row) if aum_row is not None else {}
    ref_row = find_etf_row(ref_idx_df, exact_name)
    ref_info = dict(ref_row) if ref_row is not None else {}
    risk_row = find_etf_row(risk_df, exact_name)
    risk_info = dict(risk_row) if risk_row is not None else {}

    result = {
        'ETF명': exact_name,
        '기본정보': basic_info,
        '수익률/보수': perf_info,
        '자산규모/유동성': aum_info,
        '참고지수': ref_info,
        '위험': risk_info,
        '시세분석': {
            '3개월 수익률': returns.get('3개월'),
            '1년 수익률': returns.get('1년'),
            '변동성': volatility,
            '최대낙폭': max_drawdown
        }
    }
    if 시세분석_불가:
        result['시세분석_안내'] = "시세 데이터가 부족하거나, 수익률/변동성/최대낙폭을 계산할 수 없습니다."
    return result

def plot_etf_bar(etf_info):
    # 바 차트: 수익률, 변동성, 최대낙폭, 자산규모 등
    bar_metrics = ['3개월 수익률', '1년 수익률', '변동성', '최대낙폭']
    bar_labels = ['3개월 수익률(%)', '1년 수익률(%)', '변동성(%)', '최대낙폭(%)']
    y = [etf_info['시세분석'].get(m) if etf_info['시세분석'].get(m) is not None else 0 for m in bar_metrics]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bar_labels,
        y=y,
        marker_color=['#636EFA', '#EF553B', '#00CC96', '#AB63FA'],
        text=[f"{v:.2f}" if v is not None else "N/A" for v in y],
        textposition='auto',
    ))
    fig.update_layout(
        title="ETF 주요 지표 바 차트",
        xaxis_title="지표",
        yaxis_title="값",
        template="plotly_white",
        font=dict(size=14),
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9"
    )
    return fig

def plot_etf_summary_bar(etf_info):
    """
    공식 수익률/보수/자산규모/거래량 등 바 차트로 시각화
    데이터가 일부만 있어도 있는 것만 시각화
    """
    labels = []
    values = []
    colors = ['#636EFA', '#00BFFF', '#00CC96', '#FFD700']  
    perf = etf_info.get('수익률/보수', {})
    aum = etf_info.get('자산규모/유동성', {})
    v = safe_float(perf.get('수익률'))
    if v is not None:
        labels.append('공식 1년 수익률(%)')
        values.append(v)
    v = safe_float(perf.get('총 보수'))
    if v is not None:
        labels.append('총보수(%)')
        values.append(v)
    v = safe_float(aum.get('평균 순자산총액'))
    if v is not None:
        labels.append('평균 순자산총액(백만원)')
        values.append(v)
    v = safe_float(aum.get('평균 거래량'))
    if v is not None:
        labels.append('평균 거래량')
        values.append(v)
    fig = go.Figure()
    if labels:
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker=dict(
                color=colors[:len(labels)],
                line=dict(color='#222', width=1.5),
            ),
            text=[f"<b>{safe_fmt(v)}</b>" for v in values],
            textposition='outside',
            width=0.5,
        ))
    else:
        fig.add_annotation(text="공식 지표 데이터 부족",
                           xref="paper", yref="paper",
                           showarrow=False, font=dict(size=16))
    fig.update_layout(
        title="ETF 공식 지표 요약 바 차트",
        xaxis_title="지표",
        yaxis_title="값",
        template="plotly_white",
        font=dict(size=15, family="Pretendard, NanumGothic, Arial"),
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        margin=dict(l=30, r=30, t=60, b=30),
        xaxis=dict(tickfont=dict(size=13)),
        yaxis=dict(tickfont=dict(size=13)),
    )
    fig.update_traces(
        hovertemplate='%{x}: <b>%{y:,.2f}</b>'
    )
    return fig
