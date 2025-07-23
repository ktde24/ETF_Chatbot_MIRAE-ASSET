import pandas as pd
import numpy as np

# 1) 설정
INPUT_CSV   = 'data/ETF_시세_데이터_20230101_20250721.csv'  # ETF시세데이터
OUTPUT_CSV  = 'data/etf_re_bp_simplified.csv'      
WINDOW      = 126                              # 롤링 윈도우 크기 (약 6개월, 126영업일 기준으로 함)

# 2) R/E 가중치 설정 (각 지표별로 얼만큼의 가중치를 둘지 임의값으로 지정)
W_RISK = {
    'vol':     0.25,
    'max_dd':  0.15,
    'VaR':     0.20,
    'beta':    0.10,
    'sharpe':  0.15,
    'sortino': 0.10,
    'down_dev':0.05
}
# B/P 단순 임계치 (MDD, 최대 낙폭으로 임의지정)
TH_MDD = 0.20  # MDD ≤ 20% -> B, 그 외 P

# 3) 데이터 로드 및 정렬
df = pd.read_csv(INPUT_CSV, parse_dates=['basDt'], dtype={'srtnCd':str})
df = df.sort_values(['srtnCd','basDt']).reset_index(drop=True)

# 4) 일간 수익률 및 기초지수 수익률 계산
df['r']     = df.groupby('srtnCd')['clpr'].pct_change()
df['mkt_r'] = df.groupby('srtnCd')['bssIdxClpr'].pct_change(fill_method=None)

# 5) 최대 낙폭 함수 정의
def max_drawdown(returns):
    cum = np.cumprod(1 + returns)
    return np.max(np.maximum.accumulate(cum) - cum)

# 6) R/E 보조 지표 롤링 계산
grp = df.groupby('srtnCd', group_keys=False)

df['vol']     = grp['r'].rolling(WINDOW, min_periods=WINDOW).std(ddof=1)\
                    .mul(np.sqrt(252)).reset_index(level=0, drop=True)
df['max_dd']  = grp['r'].rolling(WINDOW, min_periods=WINDOW)\
                    .apply(max_drawdown, raw=True).reset_index(level=0, drop=True)
df['VaR']     = grp['r'].rolling(WINDOW, min_periods=WINDOW).quantile(0.05)\
                    .reset_index(level=0, drop=True)

# β 계산: 그룹별 apply 로 중복 인덱스 문제 해결
beta = df.groupby('srtnCd').apply(
    lambda x: x['r']
        .rolling(WINDOW, min_periods=WINDOW)
        .cov(x['mkt_r'])
      / x['mkt_r']
        .rolling(WINDOW, min_periods=WINDOW)
        .var(ddof=1)
)
df['beta']   = beta.reset_index(level=0, drop=True)

mean_r        = grp['r'].rolling(WINDOW, min_periods=WINDOW).mean() \
                    .reset_index(level=0, drop=True)
std_r         = grp['r'].rolling(WINDOW, min_periods=WINDOW).std(ddof=1) \
                    .mul(np.sqrt(252)).reset_index(level=0, drop=True)
df['sharpe']  = mean_r.div(std_r).mul(np.sqrt(252))

df['down_dev']= grp['r'].rolling(WINDOW, min_periods=WINDOW)\
                    .apply(lambda x: np.sqrt(np.mean(np.minimum(x,0)**2)*252), raw=True)\
                    .reset_index(level=0, drop=True)
df['sortino'] = mean_r.div(df['down_dev']).mul(np.sqrt(252))

# 7) 유효 행 필터링 (리스크 지표 모두 계산된 구간)
risk_metrics = ['vol','max_dd','VaR','beta','sharpe','sortino','down_dev']
df = df.dropna(subset=risk_metrics)

# 8) 지표 정규화 (0~1)
max_vals = {m: df[m].abs().max() for m in risk_metrics}
for m in risk_metrics:
    df[f'n_{m}'] = df[m].abs() / max_vals[m]

# 9) Risk_Score 계산 및 R/E 분류
df['Risk_Score'] = sum(W_RISK[m] * df[f'n_{m}'] for m in risk_metrics)
df['risk_bin']   = np.where(df['Risk_Score'] <= 0.4, 'R', 'E')
if not df['Risk_Score'].empty:
    df['risk_tier']  = df.groupby('basDt')['Risk_Score']\
                          .transform(lambda x: pd.qcut(x, 5, labels=False, duplicates='drop'))

# 10) B/P 단순 분류 (MDD 기준)
df['strat_bin'] = np.where(df['max_dd'] <= TH_MDD, 'B', 'P')

# 11) 결과 저장 (R/E 및 B/P 정보만)
cols = [
    'basDt','srtnCd','itmsNm',
    'Risk_Score','risk_bin','risk_tier',
    'strat_bin'
]
df[cols].to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

print(f"[완료] {OUTPUT_CSV}에 R/E 및 B/P 분류 결과가 저장함") 