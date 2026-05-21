"""서비스별 수익화 유형 군집 분석."""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "entry_price_krw",
    "plan_count",
    "subscription_plan_count",
    "virtual_currency_plan_count",
    "has_ads_observed",
    "virtual_currency_dependency",
    "monetization_complexity_score",
    "metaverse_integration_score",
    "immersion_fit_score",
    "persona_language_fit",
]


CLUSTER_LABELS = {
    0: "분석 후 라벨링 필요",
    1: "분석 후 라벨링 필요",
    2: "분석 후 라벨링 필요",
}


def run_monetization_clustering(feature_matrix: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    """KMeans로 서비스별 수익화 포지션을 군집화한다.

    표본이 5개로 작으므로 예측 모델보다 해석형 segmentation 용도로만 사용한다.
    small-n benchmarking에서 유형화를 위한 비지도 학습으로 해석한다.
    """
    df = feature_matrix.copy()
    x = df[FEATURE_COLUMNS].fillna(0)
    scaled = StandardScaler().fit_transform(x)
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    df["cluster_id"] = model.fit_predict(scaled)

    # 군집 중심의 특징을 보고 사람이 이해하기 쉬운 라벨을 부여한다.
    cluster_summary = (
        df.groupby("cluster_id")
        .agg(
            avg_entry_price=("entry_price_krw", "mean"),
            avg_currency_dependency=("virtual_currency_dependency", "mean"),
            avg_metaverse=("metaverse_integration_score", "mean"),
            avg_immersion=("immersion_fit_score", "mean"),
            service_count=("service_id", "count"),
        )
        .reset_index()
    )

    label_map = {}
    for _, row in cluster_summary.iterrows():
        cluster_id = int(row["cluster_id"])
        if row["avg_metaverse"] >= 4.0 and row["avg_currency_dependency"] >= 3.0:
            label_map[cluster_id] = "Metaverse Commerce Hybrid"
        elif row["avg_immersion"] >= 4.1:
            label_map[cluster_id] = "Companion Immersion Premium"
        elif row["avg_currency_dependency"] >= 2.5:
            label_map[cluster_id] = "Currency/Pass Monetization"
        else:
            label_map[cluster_id] = "Subscription-first Character Chat"

    df["cluster_label"] = df["cluster_id"].map(label_map)
    return df
