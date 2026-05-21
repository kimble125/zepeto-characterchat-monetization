-- ZEPETO CharacterChat Monetization Analytics SQLite Schema
-- 실제 매출/내부 로그가 아니라 공개 자료와 가정 기반 분석 테이블이다.

DROP TABLE IF EXISTS sources;
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL,
    url TEXT,
    local_path TEXT,
    used_for TEXT,
    reliability_note TEXT
);

DROP TABLE IF EXISTS services;
CREATE TABLE services (
    service_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL,
    company TEXT,
    home_market TEXT,
    service_positioning TEXT,
    primary_monetization TEXT,
    zepeto_relevance TEXT,
    source_id TEXT REFERENCES sources(source_id)
);

DROP TABLE IF EXISTS pricing_plans;
CREATE TABLE pricing_plans (
    plan_id TEXT PRIMARY KEY,
    service_id TEXT NOT NULL REFERENCES services(service_id),
    plan_name TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    price_krw REAL NOT NULL,
    billing_cycle_months REAL NOT NULL,
    currency_unit TEXT,
    currency_amount REAL,
    benefit_summary TEXT,
    source_id TEXT REFERENCES sources(source_id),
    monthly_equivalent_krw REAL,
    unit_price_krw REAL
);

DROP TABLE IF EXISTS monetization_features;
CREATE TABLE monetization_features (
    service_id TEXT PRIMARY KEY REFERENCES services(service_id),
    has_subscription INTEGER,
    has_virtual_currency INTEGER,
    has_ads_observed INTEGER,
    has_ad_removal_plan INTEGER,
    has_short_pass INTEGER,
    virtual_currency_dependency REAL,
    monetization_complexity_score REAL,
    path_search REAL,
    action_logic REAL,
    npc_response REAL,
    technology_improvement REAL,
    immersion_fit_score REAL,
    persona_language_fit REAL,
    interaction_awareness_score REAL,
    source_id TEXT REFERENCES sources(source_id),
    feature_note TEXT,
    metaverse_integration_score REAL
);

DROP TABLE IF EXISTS ux_research_factors;
CREATE TABLE ux_research_factors (
    factor_id TEXT PRIMARY KEY,
    factor_name TEXT NOT NULL,
    source_id TEXT REFERENCES sources(source_id),
    research_signal TEXT,
    dashboard_metric TEXT,
    operational_definition TEXT
);

DROP TABLE IF EXISTS ad_observations;
CREATE TABLE ad_observations (
    observation_id TEXT PRIMARY KEY,
    service_id TEXT,
    observation_type TEXT,
    turn_number REAL,
    minutes_from_start REAL,
    value REAL,
    unit TEXT,
    source_id TEXT REFERENCES sources(source_id),
    note TEXT
);

DROP TABLE IF EXISTS simulation_assumptions;
CREATE TABLE simulation_assumptions (
    assumption_id TEXT PRIMARY KEY,
    assumption_name TEXT,
    value REAL,
    unit TEXT,
    description TEXT,
    source_id TEXT REFERENCES sources(source_id)
);

DROP TABLE IF EXISTS kpi_results;
CREATE TABLE kpi_results (
    service_id TEXT PRIMARY KEY REFERENCES services(service_id),
    service_name TEXT,
    entry_price_index REAL,
    monetization_complexity_score_100 REAL,
    metaverse_integration_score_100 REAL,
    immersion_fit_score_100 REAL,
    persona_language_fit_100 REAL,
    ux_strength REAL,
    monetization_leverage REAL,
    ux_risk_index REAL,
    balanced_opportunity_score REAL
);

