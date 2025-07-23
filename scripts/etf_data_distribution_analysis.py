import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

import sys
import os

# 그래프 저장 여부 설정
SAVE_PLOTS = True  # True: 그래프를 파일로 저장(터미널용), False: 화면에 표시(Jupyter/IDE용)
PLOT_DIR = 'analysis_plots'

if SAVE_PLOTS:
    
    import matplotlib
    matplotlib.use('Agg')
    
    # 플롯 저장 디렉토리 생성
    os.makedirs(PLOT_DIR, exist_ok=True)
    print(f"그래프는 {PLOT_DIR}/ 폴더에 저장됩니다.")

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def save_or_show_plot(filename):
    """그래프를 저장하거나 화면에 표시"""
    if SAVE_PLOTS:
        plt.savefig(f'{PLOT_DIR}/{filename}', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"  → {filename} 저장 완료")
        plt.close()  # 메모리 절약
    else:
        plt.show()

print("ETF 캐시 데이터 분석 시작")

# 캐시 파일 로드
try:
    cache_df = pd.read_csv('data/etf_scores_cache.csv', encoding='utf-8-sig')
except FileNotFoundError:
    print("오류: data/etf_scores_cache.csv 파일을 찾을 수 없습니다.")
    print("먼저 python scripts/precompute_etf_scores.py를 실행해주세요.")
    sys.exit(1)
print(f"총 데이터: {len(cache_df):,}개")
print(f"컬럼: {list(cache_df.columns)}")

# 기본 통계
print(f"\n=== 기본 통계 ===")
print(f"고유 ETF 수: {cache_df['ETF명'].nunique()}개")
print(f"레벨별 분포: {cache_df['level'].value_counts().to_dict()}")
print(f"투자자 유형별 분포: {cache_df['investor_type'].nunique()}개 유형")

# 1. Risk Tier 분포 분석
if 'risk_tier' in cache_df.columns:
    plt.figure(figsize=(10, 6))
    
    # 레벨별 risk_tier 분포
    plt.subplot(1, 2, 1)
    risk_tier_counts = cache_df['risk_tier'].value_counts().sort_index()
    # -1(측정불가)를 별도 색상으로 표시
    colors = ['red' if x == -1 else 'skyblue' for x in risk_tier_counts.index]
    risk_tier_counts.plot(kind='bar', color=colors)
    plt.title('Risk Tier 전체 분포')
    plt.xlabel('Risk Tier (-1: 측정불가, 0: 매우안전 ~ 4: 매우위험)')
    plt.ylabel('개수')
    plt.xticks(rotation=0)
    
    # 레벨별 risk_tier 비율
    plt.subplot(1, 2, 2)
    level_risk_crosstab = pd.crosstab(cache_df['level'], cache_df['risk_tier'], normalize='index') * 100
    if not level_risk_crosstab.empty:
        level_risk_crosstab.plot(kind='bar', stacked=True)
    plt.title('레벨별 Risk Tier 비율 (%)')
    plt.xlabel('사용자 레벨')
    plt.ylabel('비율 (%)')
    plt.legend(title='Risk Tier', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)
    
    plt.tight_layout()
    save_or_show_plot('01_risk_tier_distribution.png')
    
    print(f"\n=== Risk Tier 분석 ===")
    print("Risk Tier별 개수:")
    print(risk_tier_counts)
    print("\n레벨별 Risk Tier 분포:")
    print(pd.crosstab(cache_df['level'], cache_df['risk_tier']))

# 2. Risk Score 분포
if 'Risk_Score' in cache_df.columns:
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    sns.histplot(cache_df['Risk_Score'].dropna(), bins=30, kde=True, color='coral')
    plt.title('Risk Score 분포')
    plt.xlabel('Risk Score (낮을수록 안전)')
    plt.ylabel('빈도')
    
    plt.subplot(1, 2, 2)
    cache_df.boxplot(column='Risk_Score', by='level', ax=plt.gca())
    plt.title('레벨별 Risk Score 분포')
    plt.suptitle('')  # 기본 제목 제거
    plt.xlabel('사용자 레벨')
    plt.ylabel('Risk Score')
    
    plt.tight_layout()
    save_or_show_plot('02_risk_score_distribution.png')
    
    print(f"\n=== Risk Score 분석 ===")
    print(f"평균: {cache_df['Risk_Score'].mean():.4f}")
    print(f"중앙값: {cache_df['Risk_Score'].median():.4f}")
    print(f"최솟값: {cache_df['Risk_Score'].min():.4f}")
    print(f"최댓값: {cache_df['Risk_Score'].max():.4f}")

# 3. Risk Bin (R/E) 및 Strategy Bin (B/P) 분포
if 'risk_bin' in cache_df.columns and 'strat_bin' in cache_df.columns:
    plt.figure(figsize=(10, 4))
    
    plt.subplot(1, 2, 1)
    cache_df['risk_bin'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
    plt.title('Risk Bin 분포 (R: 보수적, E: 공격적)')
    plt.ylabel('')
    
    plt.subplot(1, 2, 2)
    cache_df['strat_bin'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['lightblue', 'gold'])
    plt.title('Strategy Bin 분포 (B: 매수보유, P: 적극매매)')
    plt.ylabel('')
    
    plt.tight_layout()
    save_or_show_plot('03_risk_strategy_bins.png')
    
    print(f"\n=== Risk/Strategy Bin 분석 ===")
    print("Risk Bin 분포:")
    print(cache_df['risk_bin'].value_counts())
    print("\nStrategy Bin 분포:")
    print(cache_df['strat_bin'].value_counts())

# 4. 점수 분포 분석
plt.figure(figsize=(15, 4))

plt.subplot(1, 3, 1)
sns.histplot(cache_df['base_score'], bins=30, kde=True, color='lightblue')
plt.title('Base Score 분포')
plt.xlabel('Base Score')
plt.ylabel('빈도')

plt.subplot(1, 3, 2)
sns.histplot(cache_df['type_weight'], bins=30, kde=True, color='lightgreen')
plt.title('Type Weight 분포')
plt.xlabel('Type Weight')
plt.ylabel('빈도')

plt.subplot(1, 3, 3)
sns.histplot(cache_df['final_score'], bins=30, kde=True, color='salmon')
plt.title('Final Score 분포')
plt.xlabel('Final Score')
plt.ylabel('빈도')

plt.tight_layout()
save_or_show_plot('04_score_distributions.png')

print(f"\n=== 점수 분석 ===")
print("Base Score 통계:")
print(cache_df['base_score'].describe())
print("\nFinal Score 통계:")
print(cache_df['final_score'].describe())

# 5. 분류체계 및 기초지수 분석
print(f"\n=== 분류체계 상위 10개 ===")
top_categories = cache_df['분류체계'].value_counts().head(10)
print(top_categories)

print(f"\n=== 기초지수 상위 10개 ===")
top_indices = cache_df['기초지수'].value_counts().head(10)
print(top_indices)

# 6. 투자자 유형별 평균 점수 분석
print(f"\n=== 투자자 유형별 평균 Final Score ===")
investor_scores = cache_df.groupby('investor_type')['final_score'].mean().sort_values(ascending=False)
print(investor_scores)

# 7. ETF 분석 (반도체 관련)
print(f"\n=== 반도체 관련 ETF 분석 ===")
semiconductor_etfs = cache_df[cache_df['ETF명'].str.contains('반도체', na=False) | 
                             cache_df['분류체계'].str.contains('반도체', na=False)]

if not semiconductor_etfs.empty:
    print(f"반도체 ETF 개수: {semiconductor_etfs['ETF명'].nunique()}개")
    print("반도체 ETF 평균 점수:")
    print(f"- 평균 Base Score: {semiconductor_etfs['base_score'].mean():.3f}")
    print(f"- 평균 Final Score: {semiconductor_etfs['final_score'].mean():.3f}")
    
    # Risk Tier 분포
    if 'risk_tier' in semiconductor_etfs.columns:
        print("반도체 ETF Risk Tier 분포:")
        print(semiconductor_etfs['risk_tier'].value_counts().sort_index())
else:
    print("반도체 관련 ETF가 없습니다.")

# 8. 시각화 
print(f"\n=== Risk Tier 막대그래프 ===")
if 'risk_tier' in cache_df.columns:
    risk_counts = cache_df['risk_tier'].value_counts().sort_index()
    max_count = risk_counts.max()
    
    for tier, count in risk_counts.items():
        if pd.notna(tier):
            bar_length = int((count / max_count) * 50)  # 최대 50자
            bar = "█" * bar_length
            if tier == -1:
                print(f"측정불가: {bar} ({count:,}개)")
            else:
                print(f"Tier {int(tier)}: {bar} ({count:,}개)")

print(f"\n=== 레벨별 ETF 수 ===")
if 'risk_tier' in cache_df.columns:
    for level in [1, 2, 3]:
        risk_tier_max = {1: 2, 2: 3, 3: 4}[level]
        level_etfs = cache_df[cache_df['level'] == level]['ETF명'].nunique()
        
        # 실제 포함된 risk_tier 범위 확인
        actual_risk_tiers = cache_df[cache_df['level'] == level]['risk_tier'].dropna().unique()
        actual_risk_tiers = sorted([int(t) for t in actual_risk_tiers if pd.notna(t)])
        risk_range = f"{min(actual_risk_tiers)}~{max(actual_risk_tiers)}" if actual_risk_tiers else "N/A"
        
        print(f"Level {level}: {level_etfs:,}개 ETF [실제 Risk Tier: {risk_range}]")
        
        # 레벨별 risk_tier 상세 분포
        risk_dist = cache_df[cache_df['level'] == level]['risk_tier'].value_counts().sort_index()
        risk_detail = ", ".join([f"Tier{int(k)}:{v}개" for k, v in risk_dist.items() if pd.notna(k)])
        print(f"  └─ 상세: {risk_detail}")

# 레벨별 필터링 효과 검증
print(f"\n=== 레벨별 Risk Tier 필터링 검증 ===")
if 'risk_tier' in cache_df.columns:
    for level in [1, 2, 3]:
        risk_tier_max = {1: 2, 2: 3, 3: 4}[level]
        level_data = cache_df[cache_df['level'] == level]
        
        # 예상과 실제가 일치하는지 확인 (측정불가 ETF 제외)
        measurable_data = level_data[level_data['risk_tier'] != -1]
        over_limit = measurable_data[measurable_data['risk_tier'] > risk_tier_max]
        unknown_count = len(level_data[level_data['risk_tier'] == -1])
        
        if len(over_limit) > 0:
            print(f"Level {level}: 허용 범위 초과 ETF {len(over_limit)}개 발견!")
        else:
            status = f"필터링 정상 적용 (Risk Tier 0~{risk_tier_max})"
            if unknown_count > 0:
                status += f", 측정불가 {unknown_count}개"
            print(f"Level {level}: {status}")

if SAVE_PLOTS:
    print(f"\n모든 그래프가 '{PLOT_DIR}/' 폴더에 저장되었습니다!")
    print(f"생성된 파일들:")
    plot_files = [
        "01_risk_tier_distribution.png",
        "02_risk_score_distribution.png", 
        "03_risk_strategy_bins.png",
        "04_score_distributions.png"
    ]
    for file in plot_files:
        if os.path.exists(f"{PLOT_DIR}/{file}"):
            print(f"  ✓ {file}")

print("\n분석 완료!") 