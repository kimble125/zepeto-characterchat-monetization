# ERD: ZEPETO CharacterChat Monetization Analytics

이 프로젝트의 DB는 실제 내부 매출 DB가 아니라 공개 자료, 논문, 직접 사용 관찰, 명시적 가정을 분석 가능한 형태로 정규화한 SQLite 데이터베이스입니다.

```mermaid
erDiagram
    sources ||--o{ services : supports
    sources ||--o{ pricing_plans : supports
    sources ||--o{ monetization_features : supports
    sources ||--o{ ux_research_factors : supports
    sources ||--o{ ad_observations : supports
    sources ||--o{ simulation_assumptions : supports

    services ||--o{ pricing_plans : has
    services ||--|| monetization_features : has
    services ||--|| kpi_results : scores
    services ||--o{ ad_observations : observed_in

    sources {
        string source_id PK
        string title
        string source_type
        string url
        string local_path
        string used_for
        string reliability_note
    }

    services {
        string service_id PK
        string service_name
        string company
        string service_positioning
        string primary_monetization
        string source_id FK
    }

    pricing_plans {
        string plan_id PK
        string service_id FK
        string plan_name
        string plan_type
        float price_krw
        float billing_cycle_months
        float monthly_equivalent_krw
        float unit_price_krw
    }

    monetization_features {
        string service_id PK
        int has_subscription
        int has_virtual_currency
        int has_ads_observed
        float monetization_complexity_score
        float metaverse_integration_score
        float immersion_fit_score
        float persona_language_fit
    }

    ux_research_factors {
        string factor_id PK
        string factor_name
        string source_id FK
        string dashboard_metric
        string operational_definition
    }

    ad_observations {
        string observation_id PK
        string service_id
        string observation_type
        float turn_number
        float value
        string source_id FK
    }

    simulation_assumptions {
        string assumption_id PK
        string assumption_name
        float value
        string unit
        string source_id FK
    }

    kpi_results {
        string service_id PK
        string service_name
        float entry_price_index
        float monetization_complexity_score_100
        float metaverse_integration_score_100
        float immersion_fit_score_100
        float ux_risk_index
        float balanced_opportunity_score
    }
```

## 설계 의도

- `sources`: 모든 수치와 가정의 근거를 추적하기 위한 출처 레지스트리입니다.
- `pricing_plans`: 구독, 재화, 단기 패스를 같은 구조로 표준화해 월 환산가와 단위 가격을 비교합니다.
- `monetization_features`: 가격 구조와 직접 관찰을 서비스 단위 피처로 변환합니다.
- `ux_research_factors`: 논문에서 도출한 개념을 대시보드 KPI로 연결합니다.
- `ad_observations` / `simulation_assumptions`: 광고 시점 시뮬레이션의 입력값과 한계를 명확히 남깁니다.
- `kpi_results`: SQL과 대시보드에서 바로 사용할 수 있는 요약 KPI입니다.

