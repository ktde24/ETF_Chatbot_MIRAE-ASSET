import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from chatbot.recommendation_engine import ETFRecommendationEngine
from chatbot.etf_analysis import analyze_etf
from chatbot.config import Config
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 60)
print("ETF 점수 캐시 생성 시작")
print("=" * 60)

start_time = time.time()

print("데이터 로딩 시작")
# 데이터 로드
info_df = pd.read_csv('data/상품검색.csv', encoding='utf-8-sig')
price_df = pd.read_csv('data/ETF_시세_데이터_20240722_20250722.csv', encoding='utf-8-sig', 
                      dtype={'srtnCd': str, 'basDt': str, 'clpr': float}, low_memory=False)
perf_df = pd.read_csv('data/수익률 및 총보수(기간).csv', encoding='utf-8-sig')
aum_df = pd.read_csv('data/자산규모 및 유동성(기간).csv', encoding='utf-8-sig')
ref_idx_df = pd.read_csv('data/참고지수(기간).csv', encoding='utf-8-sig')
risk_df = pd.read_csv('data/투자위험(기간).csv', encoding='utf-8-sig')

print(f"ETF 개수: {len(info_df)}")
print(f"시세 데이터: {len(price_df):,} 행")
print("데이터 로딩 완료")

# 전체 데이터 처리
INVESTOR_TYPES = list(Config.INVESTOR_TYPE_WEIGHTS.keys())
LEVELS = [1, 2, 3]
total_etfs = len(info_df)

print(f"\n처리 범위:")
print(f"- 투자자 유형: {len(INVESTOR_TYPES)}개 {INVESTOR_TYPES[:3]}...")
print(f"- 레벨: {len(LEVELS)}개 {LEVELS}")
print(f"- ETF 개수: {total_etfs}개")
print(f"- 총 조합: {len(INVESTOR_TYPES) * len(LEVELS) * total_etfs:,}개")

engine = ETFRecommendationEngine()

# ETF별 기본 데이터 미리 분석
print("\n1단계: ETF 기본 분석 캐시 생성")
etf_base_cache = {}
failed_etfs = []

for idx, row in info_df.iterrows():
    etf_name = row['종목명']
    if (idx + 1) % 50 == 0:
        print(f"  진행률: {idx + 1}/{total_etfs} ({(idx + 1) / total_etfs * 100:.1f}%)")
    
    try:
        # 모든 ETF 데이터(기본정보, 시세분석, 수익률/보수 등)는 레벨/유형과 무관하게 동일
        dummy_profile = {'level': 1, 'investor_type': 'ARSB'}
        etf_data = analyze_etf(etf_name, dummy_profile, price_df, info_df, perf_df, aum_df, ref_idx_df, risk_df)
        
        if '설명' in etf_data and '찾을 수 없습니다' in etf_data['설명']:
            failed_etfs.append(etf_name)
            continue
            
        etf_base_cache[etf_name] = etf_data
        
    except Exception as e:
        print(f"  {etf_name} 분석 실패: {str(e)[:50]}...")
        failed_etfs.append(etf_name)

print(f"기본 분석 완료: {len(etf_base_cache)}개 성공, {len(failed_etfs)}개 실패")

# 2단계: 전체 조합별 점수 계산
print("\n2단계: 투자자별 점수 계산")
results = []
total_combinations = len(INVESTOR_TYPES) * len(LEVELS) * len(etf_base_cache)
current_count = 0
batch_size = 100
batch_results = []

def process_combination(args):
    """단일 조합 처리 함수"""
    investor_type, level, etf_name, etf_data, row = args
    try:
        base_score = engine.calculate_base_score(etf_data)
        type_weight = engine.calculate_type_weight_cache(row, investor_type)
        final_score = base_score * type_weight
        
        return {
            'ETF명': etf_name,
            'level': level,
            'investor_type': investor_type,
            'base_score': base_score,
            'type_weight': type_weight,
            'final_score': final_score,
            '분류체계': row['분류체계'],
            '기초지수': row['기초지수'],
        }
    except Exception as e:
        return None

# 배치별 처리
for investor_type in INVESTOR_TYPES:
    for level in LEVELS:
        batch_args = []
        
        for idx, row in info_df.iterrows():
            etf_name = row['종목명']
            if etf_name not in etf_base_cache:
                continue
                
            etf_data = etf_base_cache[etf_name]
            batch_args.append((investor_type, level, etf_name, etf_data, row))
        
        # 병렬 처리로 성능 향상
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_combination, args) for args in batch_args]
            
            for future in as_completed(futures):
                current_count += 1
                result = future.result()
                if result:
                    batch_results.append(result)
                
                # 진행률 출력 (100개마다)
                if current_count % batch_size == 0:
                    elapsed = time.time() - start_time
                    progress = current_count / total_combinations * 100
                    eta = (elapsed / current_count) * (total_combinations - current_count)
                    print(f"  진행률: {current_count:,}/{total_combinations:,} ({progress:.1f}%) | "
                          f"경과: {elapsed:.1f}s | 예상 완료: {eta:.1f}s")

# 결과 정리
results = batch_results
print(f"\n✓ 점수 계산 완료: {len(results):,}개 결과 생성")

# 3단계: 결과 저장
print("\n3단계: 결과 저장")
if results:
    cache_df = pd.DataFrame(results)
    
    # 메모리 최적화: 데이터 타입 최적화
    cache_df['level'] = cache_df['level'].astype('int8')
    cache_df['base_score'] = cache_df['base_score'].astype('float32')
    cache_df['type_weight'] = cache_df['type_weight'].astype('float32')
    cache_df['final_score'] = cache_df['final_score'].astype('float32')
    
    # 상위 점수별 정렬
    cache_df = cache_df.sort_values(['investor_type', 'level', 'final_score'], ascending=[True, True, False])
    
    cache_df.to_csv('data/etf_scores_cache.csv', index=False, encoding='utf-8-sig')
    print(f"✓ 캐시 파일 저장 완료: data/etf_scores_cache.csv")
    
    # 통계 정보
    print(f"\n생성 통계:")
    print(f"- 총 결과: {len(cache_df):,}개")
    print(f"- 투자자 유형별: {cache_df.groupby('investor_type').size().to_dict()}")
    print(f"- 레벨별: {cache_df.groupby('level').size().to_dict()}")
    print(f"- 평균 점수: {cache_df['final_score'].mean():.3f}")
    print(f"- 최고 점수: {cache_df['final_score'].max():.3f}")
    
else:
    print("생성된 결과가 없습니다.")

total_time = time.time() - start_time
print(f"\n전체 완료! 총 소요시간: {total_time:.1f}초")
print("=" * 60) 