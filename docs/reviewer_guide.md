# 검토자 안내서

## 가장 빠르게 확인하는 방법

1. GitHub 저장소의 README와 대시보드 스크린샷을 먼저 확인합니다.
2. 분석 가정과 한계는 `docs/methodology.md`에서 확인합니다.
3. SQL 재현성은 `sql/analysis_queries.sql`에서 확인합니다.
4. 인터랙티브 대시보드가 필요하면 Streamlit 앱을 로컬에서 실행합니다.

## 로컬 실행 방법

```bash
pip install -r requirements.txt
python3 scripts/build_database.py
python3 -m streamlit run app.py
```

실행 후 아래 주소를 엽니다.

```text
http://localhost:8501
```

`localhost`는 Streamlit을 실행한 컴퓨터에서만 열립니다. 지원서나 포트폴리오 제출 시에는 GitHub URL을 기본으로 첨부하고, 가능하면 Streamlit Cloud 배포 URL을 함께 첨부하는 것이 좋습니다.

## 탭별 확인 포인트

- `개요`: 분석 질문, 공개 데이터 고지, 핵심 결과
- `데이터 파이프라인`: 출처 레지스트리, ERD, SQLite 테이블
- `EDA·SQL`: SQL 기반 분석 결과
- `군집분석`: KMeans 기반 서비스 포지셔닝
- `광고 시뮬레이터`: 광고 시점별 시나리오 비교
- `전략`: 사용자 경험을 고려한 수익화 가설과 실험 설계

## 한계

- 실제 제페토 내부 매출, ARPU, 이탈률, 유저 로그는 사용하지 않았습니다.
- 광고 노출 시점은 직접 사용 관찰값이므로 탐색적 근거로만 해석해야 합니다.
- CPM과 광고 완료율은 실제 제페토 광고 경제가 아니라 시나리오 분석용 가정입니다.
- KMeans는 예측 모델이 아니라 작은 표본의 벤치마크 서비스를 해석 가능한 유형으로 나누기 위한 도구입니다.
