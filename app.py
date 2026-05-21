"""ZEPETO CharacterChat Monetization Analytics Dashboard.

실제 내부 매출/로그가 아니라 공개 자료, 직접 관찰, 논문, 명시적 가정을 기반으로
제페토 캐릭터챗 수익화 전략을 탐색하는 포트폴리오용 Streamlit 대시보드다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.charts import ad_policy_scatter, kpi_radar, monetization_scatter, price_bar_chart
from src.clustering import run_monetization_clustering
from src.data import DB_PATH, build_sqlite_database, load_table, prepare_processed_tables, run_sql_query
from src.simulation import get_current_policy_result


ROOT_DIR = Path(__file__).resolve().parent


SQL_QUERIES = {
    "최저 진입가와 월 환산 구독가": """
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
    """,
    "수익화 복잡도": """
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
    """,
    "논문 기반 UX KPI": """
        SELECT
            service_name,
            metaverse_integration_score_100,
            immersion_fit_score_100,
            persona_language_fit_100,
            ux_strength,
            ux_risk_index,
            balanced_opportunity_score
        FROM kpi_results
        ORDER BY balanced_opportunity_score DESC;
    """,
    "제페토 플랜 상세": """
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
    """,
}


def configure_page() -> None:
    st.set_page_config(
        page_title="ZEPETO CharacterChat Monetization & UX",
        page_icon="Z",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --text-main: #111827;
            --text-muted: #4B5563;
            --line-soft: #E5E7EB;
            --brand-blue: #2563EB;
            --brand-green: #059669;
            --brand-red: #DC2626;
        }
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1380px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        .disclaimer {
            border-left: 4px solid var(--brand-blue);
            background: #F8FAFC;
            padding: 0.85rem 1rem;
            color: var(--text-main);
            margin: 0.6rem 0 1.1rem 0;
        }
        .section-note {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.55;
        }
        .metric-label {
            color: var(--text-muted);
            font-size: 0.8rem;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            color: var(--text-main);
            font-size: 1.8rem;
            font-weight: 700;
        }
        .small-source {
            color: #6B7280;
            font-size: 0.82rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_dashboard_data() -> dict[str, pd.DataFrame]:
    """대시보드 전체에서 사용할 테이블을 캐싱한다."""
    if not DB_PATH.exists():
        build_sqlite_database(DB_PATH)
    tables = {
        "sources": load_table("sources"),
        "services": load_table("services"),
        "pricing_plans": load_table("pricing_plans"),
        "monetization_features": load_table("monetization_features"),
        "ux_research_factors": load_table("ux_research_factors"),
        "ad_observations": load_table("ad_observations"),
        "simulation_assumptions": load_table("simulation_assumptions"),
        "service_feature_matrix": load_table("service_feature_matrix"),
        "kpi_results": load_table("kpi_results"),
    }
    tables["clustered_services"] = run_monetization_clustering(tables["service_feature_matrix"])
    return tables


@st.cache_data(show_spinner=False)
def load_simulation(
    n_sessions: int,
    first_ad_turn: int,
    second_ad_turn: int,
    completion_rate: float,
    cpm_krw: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """광고 시뮬레이션은 계산량이 있어 입력값별로 캐싱한다."""
    return get_current_policy_result(
        n_sessions=n_sessions,
        first_ad_turn=first_ad_turn,
        second_ad_turn=second_ad_turn,
        completion_rate=completion_rate,
        cpm_krw=cpm_krw,
    )


def format_krw(value: float) -> str:
    return f"{value:,.0f}원"


def show_overview(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Overview")
    st.markdown(
        """
        <div class="disclaimer">
        이 대시보드는 <b>실제 제페토 내부 매출, ARPU, 이탈률, 유저 로그가 아닌</b>
        공개 자료, 로컬 관찰 정리, 논문 근거, 명시적 가정 기반 추정 분석입니다.
        목적은 AI 캐릭터챗 수익화 전략을 사용자 경험 관점에서 탐색하는 것입니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    kpi = tables["kpi_results"]
    zepeto = kpi.loc[kpi["service_id"] == "zepeto"].iloc[0]
    pricing = tables["service_feature_matrix"]
    zepeto_feature = pricing.loc[pricing["service_id"] == "zepeto"].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("분석 서비스", f"{len(tables['services'])}개")
    col2.metric("출처 레지스트리", f"{len(tables['sources'])}건")
    col3.metric("제페토 최저 진입가", format_krw(zepeto_feature["entry_price_krw"]))
    col4.metric("제페토 Balanced Score", f"{zepeto['balanced_opportunity_score']:.1f}/100")

    st.subheader("분석 질문")
    st.markdown(
        "제페토 캐릭터챗은 어떤 수익화 레버로 사용자 경험을 덜 해치면서 매출 가능성을 높일 수 있는가?"
    )

    st.subheader("분석 구성")
    analysis_modules = pd.DataFrame(
        [
            {
                "module": "Data Foundation",
                "evidence": "가격 관찰값, 공식 웹 자료, 논문, 직접 사용 관찰을 source registry로 통합",
                "output": "정제 CSV, SQLite DB",
            },
            {
                "module": "SQL & EDA",
                "evidence": "서비스별 최저 진입가, 월 환산가, 플랜 수, 재화 의존도 분석",
                "output": "SQL query set, KPI table",
            },
            {
                "module": "UX Research Operationalization",
                "evidence": "외형/언어 스타일, 3D 캐릭터 AI, 실시간 입력 인식 연구를 변수화",
                "output": "Immersion, Persona, Metaverse scores",
            },
            {
                "module": "ML Segmentation",
                "evidence": "가격·구독·재화·광고·UX 피처 기반 KMeans 유형화",
                "output": "Monetization position map",
            },
            {
                "module": "Ad Timing Simulation",
                "evidence": "4번째/19번째 발화 관찰값과 completion-rate 가정 기반 시뮬레이션",
                "output": "Ad Revenue Potential, UX Risk Index",
            },
            {
                "module": "Strategy",
                "evidence": "수익화 레버와 UX 리스크를 함께 본 실험 후보 도출",
                "output": "월드/아바타 보상형 광고, 기억 패키지, 단기 패스 가설",
            },
        ]
    )
    st.dataframe(
        analysis_modules,
        width="stretch",
        hide_index=True,
    )

    st.subheader("핵심 결과 요약")
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.plotly_chart(kpi_radar(zepeto), use_container_width=True)
    with c2:
        st.markdown(
            """
            - 제페토는 `저가 진입가 + 재화 + 광고 + 메타버스 자산`을 결합할 수 있어 수익화 레버가 많습니다.
            - 다만 캐릭터챗은 몰입이 끊기기 쉬우므로 광고 시점과 페르소나 일관성이 핵심 리스크입니다.
            - 논문 근거상 외형, 언어 스타일, 입력 리듬, 3D 행동 로직은 모두 UX KPI로 연결할 수 있습니다.
            - 결론적으로 단순 광고 증량보다 `월드/아바타 보상형 광고`, `캐릭터별 프리미엄 슬롯`, `짧은 체험 패스`가 더 자연스러운 실험 후보입니다.
            """
        )


def show_pipeline(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Data Pipeline")
    st.markdown(
        '<p class="section-note">수집 자료를 source registry로 통합하고, 가격/UX/광고 관찰값을 SQLite 분석 테이블로 정규화했습니다.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("정제 테이블", f"{len(prepare_processed_tables())}개")
    c2.metric("가격 플랜", f"{len(tables['pricing_plans'])}개")
    c3.metric("논문 기반 UX factor", f"{len(tables['ux_research_factors'])}개")

    st.subheader("Source Registry")
    source_filter = st.multiselect(
        "출처 유형 필터",
        sorted(tables["sources"]["source_type"].unique()),
        default=sorted(tables["sources"]["source_type"].unique()),
    )
    st.dataframe(
        tables["sources"].loc[tables["sources"]["source_type"].isin(source_filter)],
        width="stretch",
        hide_index=True,
    )

    st.subheader("ERD")
    st.markdown(
        """
        ```mermaid
        erDiagram
            sources ||--o{ services : supports
            sources ||--o{ pricing_plans : supports
            sources ||--o{ monetization_features : supports
            sources ||--o{ ux_research_factors : supports
            services ||--o{ pricing_plans : has
            services ||--|| monetization_features : has
            services ||--|| kpi_results : scores
            services ||--o{ ad_observations : observed_in
        ```
        """
    )

    st.subheader("SQLite DB")
    st.code(str(DB_PATH), language="text")
    with sqlite3.connect(DB_PATH) as conn:
        table_counts = pd.read_sql_query(
            """
            SELECT name AS table_name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """,
            conn,
        )
        table_counts["row_count"] = table_counts["table_name"].apply(
            lambda name: pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {name}", conn)["n"].iloc[0]
        )
    st.dataframe(table_counts, width="stretch", hide_index=True)


def show_pricing(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Pricing & Monetization")
    st.markdown(
        '<p class="section-note">가격 문자열과 결제 주기를 월 환산가로 표준화하고, 구독·재화·광고·단기 패스 여부를 비교했습니다.</p>',
        unsafe_allow_html=True,
    )

    feature_matrix = tables["service_feature_matrix"]
    pricing = tables["pricing_plans"].merge(
        tables["services"][["service_id", "service_name"]], on="service_id", how="left"
    )

    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.plotly_chart(price_bar_chart(feature_matrix), use_container_width=True)
    with c2:
        st.dataframe(
            feature_matrix[
                [
                    "service_name",
                    "entry_price_krw",
                    "plan_count",
                    "plan_type_count",
                    "virtual_currency_dependency",
                    "monetization_complexity_score",
                ]
            ].sort_values("entry_price_krw"),
            width="stretch",
            hide_index=True,
        )

    st.subheader("정제 가격 테이블")
    selected_services = st.multiselect(
        "서비스 선택",
        sorted(pricing["service_name"].unique()),
        default=sorted(pricing["service_name"].unique()),
    )
    st.dataframe(
        pricing.loc[pricing["service_name"].isin(selected_services)].sort_values(
            ["service_name", "plan_type", "price_krw"]
        ),
        width="stretch",
        hide_index=True,
    )


def show_sql_and_kpi(tables: dict[str, pd.DataFrame]) -> None:
    st.header("EDA & SQL")
    st.markdown(
        '<p class="section-note">SQLite 쿼리로 EDA 결과를 재현하고, 논문 기반 UX 변수와 수익화 변수를 KPI로 결합했습니다.</p>',
        unsafe_allow_html=True,
    )

    query_name = st.selectbox("SQL 분석 쿼리", list(SQL_QUERIES.keys()))
    query = SQL_QUERIES[query_name]
    st.code(query.strip(), language="sql")
    st.dataframe(run_sql_query(query), width="stretch", hide_index=True)

    st.subheader("KPI 정의")
    kpi_definition = pd.DataFrame(
        [
            {
                "KPI": "Entry Price Index",
                "definition": "최저 진입가가 낮을수록 100점에 가까운 접근성 지표",
                "why_it_matters": "캐릭터챗의 첫 결제 장벽을 비교",
            },
            {
                "KPI": "Monetization Complexity Score",
                "definition": "구독, 재화, 광고, 단기 패스 등 결제 구조의 복합성",
                "why_it_matters": "수익화 레버가 많을수록 실험 여지가 크지만 UX 리스크도 증가",
            },
            {
                "KPI": "Metaverse Integration Score",
                "definition": "Path Search, Action Logic, NPC Response, Technology Improvement 평균",
                "why_it_matters": "제페토가 3D/월드 자산으로 차별화할 수 있는 정도",
            },
            {
                "KPI": "Immersion Fit Score",
                "definition": "외형/세계관/캐릭터 몰입 적합도",
                "why_it_matters": "광고와 결제가 몰입을 해치지 않는지 판단",
            },
            {
                "KPI": "UX Risk Index",
                "definition": "복잡한 과금과 광고가 사용자 몰입을 방해할 위험",
                "why_it_matters": "수익화 실험의 guardrail",
            },
            {
                "KPI": "Balanced Opportunity Score",
                "definition": "수익화 레버, UX 강점, UX 리스크를 합친 우선순위 점수",
                "why_it_matters": "제페토 적용 가설의 우선순위 판단",
            },
        ]
    )
    st.dataframe(kpi_definition, width="stretch", hide_index=True)

    st.subheader("논문 기반 UX 변수")
    st.dataframe(tables["ux_research_factors"], width="stretch", hide_index=True)


def show_ml(tables: dict[str, pd.DataFrame]) -> None:
    st.header("ML Segmentation")
    st.markdown(
        '<p class="section-note">표본이 작아 예측 회귀보다 KMeans 기반 유형화가 적합합니다. 목표는 정답 예측이 아니라 포지셔닝 해석입니다.</p>',
        unsafe_allow_html=True,
    )

    clustered = tables["clustered_services"]
    st.plotly_chart(monetization_scatter(clustered), use_container_width=True)
    st.dataframe(
        clustered[
            [
                "service_name",
                "cluster_label",
                "entry_price_krw",
                "plan_count",
                "virtual_currency_dependency",
                "monetization_complexity_score",
                "metaverse_integration_score",
                "immersion_fit_score",
                "persona_language_fit",
            ]
        ].sort_values(["cluster_label", "service_name"]),
        width="stretch",
        hide_index=True,
    )

    st.subheader("해석")
    st.markdown(
        """
        - `Metaverse Commerce Hybrid`: 제페토처럼 3D/월드/재화/광고를 연결할 수 있는 유형입니다.
        - `Companion Immersion Premium`: Zeta처럼 관계 몰입, 세계관 설정, 패스/재화 결합이 강한 유형입니다.
        - `Subscription-first Character Chat`: Character.AI, Talkie, Replika처럼 결제 구조가 구독 중심으로 해석되는 유형입니다.
        - Replika는 몰입 점수가 높지만, 현재 피처셋에서는 재화/광고보다 구독 플랜 구조의 영향이 커 subscription-first에 배치됩니다.
        """
    )


def show_ad_simulator() -> None:
    st.header("Ad Simulator")
    st.markdown(
        '<p class="section-note">직접 관찰한 4번째/19번째 발화 광고 시점을 기준으로, 노출 시점을 조정했을 때 수익 가능성과 UX 위험이 어떻게 바뀌는지 비교합니다.</p>',
        unsafe_allow_html=True,
    )

    st.subheader("시뮬레이션 입력값")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        n_sessions = st.slider("세션 수", 5_000, 50_000, 20_000, step=5_000)
    with c2:
        first_ad_turn = st.slider("첫 광고 턴", 3, 15, 4)
    with c3:
        second_ad_turn = st.slider("두 번째 광고 턴", first_ad_turn + 8, 40, 19)
    with c4:
        completion_rate = st.slider("완료율 가정", 0.50, 0.99, 0.97, step=0.01)
    with c5:
        cpm_krw = st.slider("CPM(KRW)", 500, 6000, 2500, step=250)

    sessions, current, grid = load_simulation(
        n_sessions=n_sessions,
        first_ad_turn=first_ad_turn,
        second_ad_turn=second_ad_turn,
        completion_rate=completion_rate,
        cpm_krw=cpm_krw,
    )

    best = grid.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("현재 추정 수익", format_krw(current.iloc[0]["estimated_revenue_krw"]))
    c2.metric("현재 UX Risk", f"{current.iloc[0]['ux_risk_index']:.1f}/100")
    c3.metric("추천 첫 광고", f"{int(best['first_ad_turn'])}턴")
    c4.metric("추천 두 번째 광고", f"{int(best['second_ad_turn'])}턴")

    st.plotly_chart(ad_policy_scatter(grid, current), use_container_width=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("세션 길이 분포")
        hist = px.histogram(
            sessions,
            x="turns",
            nbins=40,
            labels={"turns": "세션당 발화 수", "count": "세션 수"},
            color_discrete_sequence=["#2563EB"],
        )
        hist.update_layout(height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(hist, use_container_width=True)
    with c2:
        st.subheader("상위 정책 후보")
        st.dataframe(
            grid.head(10)[
                [
                    "first_ad_turn",
                    "second_ad_turn",
                    "ad_revenue_potential",
                    "ux_risk_index",
                    "balanced_opportunity_score",
                    "estimated_revenue_krw",
                ]
            ],
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "주의: 수익은 실제 제페토 매출이 아니라 CPM과 completion rate 가정에 따른 상대 비교용 추정값입니다."
    )


def show_strategy(tables: dict[str, pd.DataFrame]) -> None:
    st.header("Strategy")
    st.markdown(
        '<p class="section-note">분석 결과를 제페토 캐릭터챗에 적용할 수 있는 실험 가설로 번역했습니다.</p>',
        unsafe_allow_html=True,
    )

    strategy = pd.DataFrame(
        [
            {
                "hypothesis": "월드/아바타 보상형 광고",
                "expected_effect": "광고를 단순 interrupt가 아니라 캐릭터 꾸미기/월드 행동 보상과 연결",
                "success_kpi": "광고 완료율, 광고 후 다음 발화율, 보상 사용률",
                "risk": "너무 이른 노출은 몰입 저하",
                "experiment": "첫 광고 4턴 vs 8턴 vs 12턴 A/B 테스트",
            },
            {
                "hypothesis": "캐릭터별 프리미엄 슬롯/기억 패키지",
                "expected_effect": "페르소나 일관성과 장기 대화 기억을 유료 가치로 전환",
                "success_kpi": "유료 전환율, 7일 재방문, 세션당 발화 수",
                "risk": "기본 무료 경험 품질 저하로 인식될 수 있음",
                "experiment": "인기 캐릭터군에 memory preview 제공 후 전환 측정",
            },
            {
                "hypothesis": "1일/3일 캐릭터챗 체험 패스",
                "expected_effect": "월 구독보다 낮은 심리적 장벽으로 고몰입 세션을 monetization funnel에 연결",
                "success_kpi": "패스 구매율, 월 구독 전환율, 패스 만료 후 재방문",
                "risk": "기존 Premium Lite와 포지션 충돌",
                "experiment": "Zeta식 단기 패스 벤치마크를 제페토 캐릭터챗 전용으로 제한 실험",
            },
        ]
    )
    st.dataframe(strategy, width="stretch", hide_index=True)

    st.subheader("다음 실험 설계")
    st.markdown(
        """
        - 광고 노출 시점은 첫 광고 4턴, 8턴, 12턴 조건으로 A/B 테스트한다.
        - 핵심 guardrail은 광고 후 다음 발화율, 세션당 발화 수, 24시간 재방문율로 둔다.
        - 캐릭터별 기억 패키지와 단기 패스는 기존 Premium 플랜과 충돌하지 않도록 캐릭터챗 전용 실험군으로 제한한다.
        """
    )

    with st.expander("출처 링크 보기"):
        sources = tables["sources"].copy()
        sources = sources.loc[sources["url"].fillna("") != "", ["title", "source_type", "url", "used_for"]]
        st.dataframe(sources, width="stretch", hide_index=True)


def main() -> None:
    configure_page()
    tables = load_dashboard_data()

    st.title("ZEPETO CharacterChat Monetization & UX Analytics")
    st.caption("Public-data portfolio dashboard for UX-safe monetization strategy")

    tabs = st.tabs(
        [
            "Overview",
            "Data Pipeline",
            "Pricing & Monetization",
            "EDA & SQL",
            "ML Segmentation",
            "Ad Simulator",
            "Strategy",
        ]
    )

    with tabs[0]:
        show_overview(tables)
    with tabs[1]:
        show_pipeline(tables)
    with tabs[2]:
        show_pricing(tables)
    with tabs[3]:
        show_sql_and_kpi(tables)
    with tabs[4]:
        show_ml(tables)
    with tabs[5]:
        show_ad_simulator()
    with tabs[6]:
        show_strategy(tables)


if __name__ == "__main__":
    main()
