# ETF 챗봇

ETF 투자 전문 상담 챗봇으로, 사용자의 투자 레벨과 투자자 유형에 맞춘 맞춤형 ETF 분석, 추천, 비교 서비스를 제공합니다.

## 🚀 주요 기능

### 📊 ETF 분석
- **개별 ETF 종합 분석**: 시세 데이터와 공식 데이터 통합 분석
- **수익률 분석**: 3개월/1년 수익률, 변동성, 최대낙폭 계산
- **비용 분석**: 총보수, 거래비용 등 투자 비용 분석
- **유동성 분석**: 자산규모, 거래량 등 유동성 지표 분석
- **사용자 레벨별 맞춤 분석**: Level 1~3에 따른 차별화된 설명

### 🎯 ETF 추천
- **투자자 유형별 맞춤 추천**: 16가지 투자자 유형별 가중치 적용
- **카테고리별 추천**: 반도체, AI, 바이오, 금융 등 테마별 추천
- **캐시 기반 고속 추천**: 사전 계산된 점수 기반 빠른 추천
- **위험도 필터링**: 사용자 레벨에 따른 위험도 제한

### 🔍 ETF 비교
- **다중 ETF 비교**: 최대 6개 ETF 동시 비교
- **종합 점수 비교**: 위험-수익률, 비용 효율성 등 종합 평가
- **인터랙티브 시각화**: 바차트, 산점도, 레이더차트, 히트맵
- **실시간 데이터**: 캐시 + 실시간 데이터 하이브리드 분석

### 💬 AI 챗봇
- **CLOVA LLM 연동**: 자연어 기반 대화형 인터페이스
- **맞춤형 답변**: 투자자 유형별 특성 반영
- **실시간 분석**: 사용자 질의에 따른 즉시 분석 제공

## 🏗️ 프로젝트 구조

```
ETF_RAG_Chatbot/
├── app/
│   └── main_app.py              # Streamlit 메인 애플리케이션
├── chatbot/
│   ├── __init__.py
│   ├── config.py                # 설정 관리 (투자자 유형, 파일 경로 등)
│   ├── utils.py                 # 공통 유틸리티 함수
│   ├── etf_analysis.py          # ETF 개별 분석 모듈
│   ├── recommendation_engine.py # ETF 추천 엔진
│   ├── etf_comparison.py        # ETF 비교 분석 모듈
│   ├── clova_client.py          # CLOVA LLM API 클라이언트
├── data/                        # ETF 데이터 파일들
│   ├── 상품검색.csv
│   ├── ETF_시세_데이터_*.csv
│   ├── 수익률 및 총보수(기간).csv
│   ├── 자산규모 및 유동성(기간).csv
│   ├── 참고지수(기간).csv
│   ├── 투자위험(기간).csv
│   ├── etf_re_bp_simplified.csv
│   └── etf_scores_cache.csv
├── scripts/                     # 데이터 처리 스크립트
│   ├── calculate_risk_tier.py
│   ├── fetch_etf_daily.py
│   └── precompute_etf_scores.py
├── requirements.txt             # Python 의존성
└── README.md                   # 프로젝트 설명서
```

## 🎯 투자자 유형 시스템

### 투자자 유형 조합 (16가지)
각 투자자는 다음 4개 차원에서 유형이 결정됩니다:

1. **분석 방식**: A (Auto-driven) vs I (Investigator)
2. **위험 성향**: R (Risk-averse) vs E (Eager)
3. **정보 선호**: S (Story-driven) vs T (Technical)
4. **투자 전략**: B (Buy-and-hold) vs P (Portfolio)

### 사용자 레벨 (3단계)
- **Level 1**: 초보자 (유치원/초등학생 수준 설명)
- **Level 2**: 중급자 (중고등학생 수준 설명)
- **Level 3**: 고급자 (성인 수준, 전문적 분석)

## 🛠️ 설치 및 실행

### 1. 환경 설정
```bash
# Python 3.8+ 설치 필요
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 데이터 준비
```bash
# ETF 데이터 파일들을 data/ 디렉토리에 배치
# 캐시 데이터 생성 (선택)
python scripts/precompute_etf_scores.py
```

### 3. 애플리케이션 실행
```bash
# Streamlit 앱 실행
streamlit run app/main_app.py
```

### 4. CLOVA API 설정
- CLOVA LLM 서비스에서 API 키 발급
- Streamlit 앱의 사이드바에서 API 키 입력

## 📊 데이터 구조

### 주요 데이터 파일
- **상품검색.csv**: ETF 기본 정보 (종목명, 종목코드, 분류체계 등)
- **ETF_시세_데이터_*.csv**: 일별 시세 데이터 (수익률, 변동성 계산용)
- **수익률 및 총보수(기간).csv**: 공식 수익률 및 보수 데이터
- **자산규모 및 유동성(기간).csv**: AUM, 거래량 등 유동성 지표
- **참고지수(기간).csv**: ETF 기초지수 정보
- **투자위험(기간).csv**: 위험도 지표
- **etf_scores_cache.csv**: 사전 계산된 ETF 점수 

## 🔧 주요 모듈 설명

### utils.py
공통으로 사용되는 유틸리티 함수들을 모아놓은 모듈:
- **데이터 처리**: `safe_float()`, `clean_dataframe()`
- **문자열 처리**: `normalize_etf_name()`, `extract_etf_name_from_input()`
- **포맷팅**: `format_percentage()`, `format_aum()`, `format_volume()`
- **검증**: `validate_user_profile()`, `is_valid_etf_name()`
- **에러 처리**: `create_error_result()`, `handle_data_loading_error()`

### etf_analysis.py
개별 ETF 분석을 담당하는 모듈:
- **시세 분석**: 수익률, 변동성, 최대낙폭 계산
- **공식 데이터 통합**: 보수, 자산규모, 거래량 분석
- **시각화**: 바차트, 요약 차트 생성
- **사용자 레벨별 맞춤 분석**: Level 1~3에 따른 차별화

### recommendation_engine.py
ETF 추천 엔진:
- **투자자 유형별 가중치**: 16가지 유형별 맞춤 점수 계산
- **캐시 기반 고속 추천**: 사전 계산된 점수 활용
- **카테고리 필터링**: 테마별 ETF 검색
- **위험도 제한**: 사용자 레벨에 따른 위험도 필터링

### etf_comparison.py
다중 ETF 비교 분석:
- **하이브리드 분석**: 캐시 + 실시간 데이터 조합
- **종합 점수 계산**: 위험-수익률, 비용 효율성 등
- **다양한 시각화**: 바차트, 산점도, 레이더차트, 히트맵
- **실시간 비교**: 최대 6개 ETF 동시 비교

### config.py
설정 관리:
- **투자자 유형 가중치**: 16가지 조합별 가중치 설정
- **파일 경로 관리**: 데이터 파일 경로 중앙 관리
- **프롬프트 관리**: 시스템 프롬프트 및 추천 프롬프트
- **위험도 제한**: 레벨별 risk_tier 허용 범위

## 🎨 사용자 인터페이스

### Streamlit 웹 인터페이스
- **사이드바**: 사용자 프로필 설정, API 키 입력
- **채팅 인터페이스**: 자연어 기반 대화형 분석
- **시각화**: 인터랙티브 차트 및 비교 테이블

### 주요 기능
1. **ETF 분석**: "KODEX 반도체 ETF 분석해줘"
2. **ETF 추천**: "반도체 ETF 추천해줘"
3. **ETF 비교**: "KODEX 반도체 vs TIGER 반도체 비교해줘"
4. **카테고리 추천**: "AI 관련 ETF 추천해줘"


