"""Plotly 차트 생성 헬퍼."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLOR_SEQUENCE = ["#2563EB", "#059669", "#F59E0B", "#DC2626", "#7C3AED", "#0F766E"]


def price_bar_chart(pricing_summary: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        pricing_summary.sort_values("entry_price_krw"),
        x="service_name",
        y="entry_price_krw",
        color="service_name",
        color_discrete_sequence=COLOR_SEQUENCE,
        text="entry_price_krw",
        labels={"entry_price_krw": "최저 진입가(KRW)", "service_name": "서비스"},
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(showlegend=False, height=360, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def monetization_scatter(clustered: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        clustered,
        x="monetization_complexity_score",
        y="metaverse_integration_score",
        size="plan_count",
        color="cluster_label",
        text="service_name",
        hover_data=[
            "entry_price_krw",
            "virtual_currency_dependency",
            "immersion_fit_score",
            "persona_language_fit",
        ],
        color_discrete_sequence=COLOR_SEQUENCE,
        labels={
            "monetization_complexity_score": "수익화 복잡도(0~5)",
            "metaverse_integration_score": "메타버스 결합도(0~5)",
            "cluster_label": "군집",
        },
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(height=430, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def kpi_radar(kpi_row: pd.Series) -> go.Figure:
    categories = [
        "Entry Price",
        "Monetization",
        "Metaverse",
        "Immersion",
        "Persona",
        "Balanced",
    ]
    values = [
        kpi_row["entry_price_index"],
        kpi_row["monetization_complexity_score_100"],
        kpi_row["metaverse_integration_score_100"],
        kpi_row["immersion_fit_score_100"],
        kpi_row["persona_language_fit_100"],
        kpi_row["balanced_opportunity_score"],
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=str(kpi_row["service_name"]),
            line_color="#2563EB",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=360,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return fig


def ad_policy_scatter(policy_grid: pd.DataFrame, current_policy: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        policy_grid,
        x="ux_risk_index",
        y="ad_revenue_potential",
        color="balanced_opportunity_score",
        size="avg_impressions_per_session",
        hover_data=["first_ad_turn", "second_ad_turn", "estimated_revenue_krw"],
        color_continuous_scale="Viridis",
        labels={
            "ux_risk_index": "UX Risk Index",
            "ad_revenue_potential": "Ad Revenue Potential",
            "balanced_opportunity_score": "Balanced Score",
        },
    )
    fig.add_trace(
        go.Scatter(
            x=current_policy["ux_risk_index"],
            y=[
                policy_grid.loc[
                    (policy_grid["first_ad_turn"] == int(current_policy.iloc[0]["first_ad_turn"]))
                    & (policy_grid["second_ad_turn"] == int(current_policy.iloc[0]["second_ad_turn"])),
                    "ad_revenue_potential",
                ].mean()
            ],
            mode="markers+text",
            marker=dict(size=18, color="#DC2626", symbol="x"),
            text=["현재 관찰"],
            textposition="top center",
            name="현재 관찰",
        )
    )
    fig.update_layout(height=440, margin=dict(l=20, r=20, t=40, b=20))
    return fig

