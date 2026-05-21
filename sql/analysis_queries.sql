-- 1. 서비스별 최저 진입가와 월 환산 구독가
SELECT
    s.service_name,
    MIN(p.price_krw) AS entry_price_krw,
    MIN(CASE WHEN p.plan_type = 'subscription' THEN p.monthly_equivalent_krw END) AS min_subscription_monthly_krw,
    COUNT(*) AS plan_count,
    COUNT(DISTINCT p.plan_type) AS plan_type_count
FROM services AS s
JOIN pricing_plans AS p ON s.service_id = p.service_id
GROUP BY s.service_id, s.service_name
ORDER BY entry_price_krw;

-- 2. 수익화 복잡도와 재화 의존도
SELECT
    s.service_name,
    mf.has_subscription,
    mf.has_virtual_currency,
    mf.has_ads_observed,
    mf.has_short_pass,
    mf.virtual_currency_dependency,
    mf.monetization_complexity_score
FROM services AS s
JOIN monetization_features AS mf ON s.service_id = mf.service_id
ORDER BY mf.monetization_complexity_score DESC;

-- 3. 논문 근거 기반 UX 변수와 KPI
SELECT
    kr.service_name,
    kr.metaverse_integration_score_100,
    kr.immersion_fit_score_100,
    kr.persona_language_fit_100,
    kr.ux_strength,
    kr.ux_risk_index,
    kr.balanced_opportunity_score
FROM kpi_results AS kr
ORDER BY kr.balanced_opportunity_score DESC;

-- 4. 제페토 가격 패키지 상세
SELECT
    plan_name,
    plan_type,
    price_krw,
    monthly_equivalent_krw,
    currency_unit,
    currency_amount,
    unit_price_krw
FROM pricing_plans
WHERE service_id = 'zepeto'
ORDER BY plan_type, price_krw;

-- 5. 출처 유형별 사용 개수
SELECT
    source_type,
    COUNT(*) AS source_count
FROM sources
GROUP BY source_type
ORDER BY source_count DESC;

