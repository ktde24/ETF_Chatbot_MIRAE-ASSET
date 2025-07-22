"""
🔄 ETF 데이터 변환 로직 상세 예시
- 5개 CSV 파일 → 검색 최적화된 텍스트로 변환하는 과정
"""

import pandas as pd

# 🎯 예시 데이터 (실제 CSV에서 가져온 것과 동일한 구조)
example_data = {
    # 기본 정보 (상품검색.csv)
    'etf_row': {
        '종목명': 'KODEX 반도체',
        '분류체계': '주식형>국내>업종테마',
        '종목코드': '069500'
    },
    
    # 성과 정보 (수익률 및 총보수.csv)
    'perf_row': {
        '종목명': 'KODEX 반도체',
        '수익률': 15.2,
        '총 보수': 0.49
    },
    
    # 규모 정보 (자산규모 및 유동성.csv)
    'aum_row': {
        '종목명': 'KODEX 반도체',
        '평균 순자산총액': 2500,  # 백만원
        '평균 거래량': 45000
    },
    
    # 지수 정보 (참고지수.csv)
    'ref_row': {
        '종목명': 'KODEX 반도체',
        '참고지수': 'KRX 반도체지수'
    },
    
    # 위험 정보 (투자위험.csv)
    'risk_row': {
        '종목명': 'KODEX 반도체',
        '변동성': '높음'
    }
}

def step1_extract_basic_info(etf_row, perf_row, aum_row, ref_row, risk_row):
    """
    🔍 1단계: 각 CSV에서 필요한 정보 추출
    """
    print("=" * 50)
    print("🔍 1단계: 기본 정보 추출")
    print("=" * 50)
    
    # 각 CSV에서 정보 추출
    extracted = {
        'etf_name': etf_row.get('종목명', ''),
        'classification': etf_row.get('분류체계', ''),
        'returns': perf_row.get('수익률', 'N/A') if perf_row else 'N/A',
        'fee': perf_row.get('총 보수', 'N/A') if perf_row else 'N/A',
        'aum': aum_row.get('평균 순자산총액', 'N/A') if aum_row else 'N/A',
        'volume': aum_row.get('평균 거래량', 'N/A') if aum_row else 'N/A',
        'reference_index': ref_row.get('참고지수', '') if ref_row else '',
        'volatility': risk_row.get('변동성', 'N/A') if risk_row else 'N/A'
    }
    
    print("추출된 정보:")
    for key, value in extracted.items():
        print(f"  {key}: {value}")
    
    return extracted

def step2_extract_strategy_keywords(etf_name, classification, reference_index):
    """
    🎯 2단계: 투자 전략 키워드 추출 (가장 중요한 단계!)
    
    이 단계가 왜 중요한가요?
    - 사용자가 "반도체 ETF"라고 검색했을 때
    - "칩", "메모리", "시스템반도체" 등 관련 키워드도 매칭되도록 함
    """
    print("\n" + "=" * 50)
    print("🎯 2단계: 투자 전략 키워드 추출")
    print("=" * 50)
    
    keywords = []
    name_lower = etf_name.lower()
    
    print(f"분석 대상 ETF명: '{etf_name}'")
    print(f"소문자 변환: '{name_lower}'")
    
    # 🏭 섹터/테마별 키워드 매핑 사전
    sector_keywords = {
        # 기술 섹터
        '반도체': ['반도체', '칩', '메모리', '시스템반도체', 'semiconductor'],
        'IT': ['IT', '정보기술', '소프트웨어', '인터넷', '클라우드'],
        'AI': ['AI', '인공지능', '머신러닝', '딥러닝', '빅데이터'],
        
        # 산업 섹터  
        '바이오': ['바이오', '제약', '헬스케어', '의료', '바이오텍'],
        '금융': ['금융', '은행', '보험', '증권', '핀테크'],
        '에너지': ['에너지', '전력', '신재생에너지', '태양광', '풍력'],
        '자동차': ['자동차', '전기차', '배터리', '모빌리티', '자율주행'],
        
        # 테마 투자
        '게임': ['게임', 'K-게임', '엔터테인먼트', '콘텐츠'],
        'ESG': ['ESG', '친환경', '지속가능', '그린', '탄소중립'],
        '배당': ['배당', '고배당', '인컴', '수익형'],
        
        # 투자 스타일
        '성장': ['성장', '그로스', '중소형', '벤처'],
        '가치': ['가치', '밸류', '저평가', '가치주'],
        '퀄리티': ['퀄리티', '우량', '품질'],
    }
    
    print("\n🔍 ETF명에서 키워드 매칭:")
    # ETF명에서 키워드 매칭
    for category, terms in sector_keywords.items():
        matched_terms = [term for term in terms if term in name_lower]
        if matched_terms:
            keywords.append(category)
            print(f"  ✅ '{category}' 매칭됨 - 찾은 단어: {matched_terms}")
    
    print(f"\n🔍 지수명에서 키워드 추출: '{reference_index}'")
    # 지수명에서 추가 키워드 추출
    if reference_index:
        ref_lower = reference_index.lower()
        if 'kospi' in ref_lower or 'krx200' in ref_lower:
            keywords.append('대형주')
            print("  ✅ '대형주' 키워드 추가")
        elif 'kosdaq' in ref_lower:
            keywords.append('중소형주')
            print("  ✅ '중소형주' 키워드 추가")
        elif 'dividend' in ref_lower or '배당' in ref_lower:
            keywords.append('배당')
            print("  ✅ '배당' 키워드 추가")
    
    print(f"\n🔍 분류에서 키워드 추출: '{classification}'")
    # 분류에서 추가 키워드 추출
    if classification:
        if '업종테마' in classification or '섹터' in classification:
            keywords.append('테마투자')
            print("  ✅ '테마투자' 키워드 추가")
        elif '시장대표' in classification:
            keywords.append('인덱스투자')
            print("  ✅ '인덱스투자' 키워드 추가")
        elif '전략' in classification:
            keywords.append('전략투자')
            print("  ✅ '전략투자' 키워드 추가")
    
    # 중복 제거 및 결합
    final_keywords = ', '.join(set(keywords)) if keywords else '일반투자'
    
    print(f"\n🎯 최종 추출된 키워드: '{final_keywords}'")
    
    return final_keywords

def step3_create_enhanced_text(extracted_info, strategy_keywords):
    """
    📝 3단계: 검색 최적화된 풍부한 텍스트 생성
    
    왜 이런 형태로 만드나요?
    - 단순한 "KODEX 반도체, 15.2%" 보다는
    - 자연어 문장으로 된 설명이 벡터 검색에 훨씬 유리함
    """
    print("\n" + "=" * 50)
    print("📝 3단계: 검색 최적화된 텍스트 생성")
    print("=" * 50)
    
    # 📊 구조화된 정보 부분
    structured_part = f"""
ETF명: {extracted_info['etf_name']}
투자전략: {strategy_keywords}
분류: {extracted_info['classification']}
참고지수: {extracted_info['reference_index']}
수익률: {extracted_info['returns']}%
총보수: {extracted_info['fee']}%
자산규모: {extracted_info['aum']}백만원
거래량: {extracted_info['volume']}주
위험도: {extracted_info['volatility']}
    """.strip()
    
    # 📖 자연어 설명 부분 (벡터 검색에 핵심적!)
    natural_language_part = f"""
{extracted_info['etf_name']}은 {strategy_keywords}에 투자하는 ETF입니다.
{extracted_info['classification']} 분야에 속하며, {extracted_info['reference_index']}를 추종합니다.
변동성은 {extracted_info['volatility']} 수준이고, 연간 총보수는 {extracted_info['fee']}%입니다.
이 상품은 {strategy_keywords} 투자를 원하는 투자자에게 적합합니다.
    """.strip()
    
    # 최종 텍스트 결합
    final_text = structured_part + "\n\n" + natural_language_part
    
    print("생성된 텍스트:")
    print("-" * 40)
    print(final_text)
    print("-" * 40)
    
    return final_text

def demonstrate_transformation():
    """전체 변환 과정 시연"""
    print("🚀 ETF 데이터 변환 과정 시연")
    print("입력: 5개 CSV 파일의 데이터")
    print("출력: 벡터 검색 최적화된 텍스트")
    
    # 1단계: 기본 정보 추출
    extracted = step1_extract_basic_info(
        example_data['etf_row'],
        example_data['perf_row'], 
        example_data['aum_row'],
        example_data['ref_row'],
        example_data['risk_row']
    )
    
    # 2단계: 투자 전략 키워드 추출
    keywords = step2_extract_strategy_keywords(
        extracted['etf_name'],
        extracted['classification'],
        extracted['reference_index']
    )
    
    # 3단계: 최종 텍스트 생성
    final_text = step3_create_enhanced_text(extracted, keywords)
    
    print("\n" + "=" * 60)
    print("🎉 변환 완료!")
    print("이 텍스트가 벡터로 임베딩되어 검색 가능해집니다.")
    print("=" * 60)
    
    return final_text

if __name__ == "__main__":
    demonstrate_transformation() 