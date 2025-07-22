import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 캐시 파일 로드
cache_df = pd.read_csv('data/etf_scores_cache.csv', encoding='utf-8-sig')

# 1. 자산규모 분포
plt.figure(figsize=(8,4))
sns.histplot(cache_df['자산규모'].dropna(), bins=30, kde=True)
plt.title('ETF 자산규모 분포')
plt.xlabel('자산규모(백만원)')
plt.ylabel('ETF 개수')
plt.tight_layout()
plt.show()

# 자산규모 구간별 빈도
print('자산규모 구간별 빈도:')
print(pd.cut(cache_df['자산규모'], bins=[0, 50000, 100000, 500000, 1000000, 5000000, 1e10]).value_counts().sort_index())

# 2. 거래량 분포
plt.figure(figsize=(8,4))
sns.histplot(cache_df['거래량'].dropna(), bins=30, kde=True)
plt.title('ETF 거래량 분포')
plt.xlabel('평균 거래량')
plt.ylabel('ETF 개수')
plt.tight_layout()
plt.show()

print('거래량 구간별 빈도:')
print(pd.cut(cache_df['거래량'], bins=[0, 10000, 50000, 100000, 500000, 1000000, 1e10]).value_counts().sort_index())

# 3. 변동성 등급 분포
plt.figure(figsize=(6,4))
cache_df['변동성'].value_counts().loc[['매우낮음','낮음','보통','높음','매우높음']].plot(kind='bar')
plt.title('ETF 변동성 등급 분포')
plt.xlabel('변동성 등급')
plt.ylabel('ETF 개수')
plt.tight_layout()
plt.show()

print('변동성 등급별 빈도:')
print(cache_df['변동성'].value_counts())

# 4. 분류체계 상위 10개
print('\n분류체계 상위 10개:')
print(cache_df['분류체계'].value_counts().head(10))

# 5. 기초지수 상위 10개
print('\n기초지수 상위 10개:')
print(cache_df['기초지수'].value_counts().head(10)) 