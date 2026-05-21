"""광고 노출 시점별 수익 가능성과 UX 위험 시뮬레이션."""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_sessions(
    n_sessions: int = 20_000,
    zipf_shape: float = 1.85,
    max_turns: int = 80,
    seed: int = 42,
) -> pd.DataFrame:
    """멱법칙 기반 세션 길이 샘플을 생성한다.

    실제 제페토 로그가 없으므로 XiaoIce 연구에서 강조한 세션당 대화 턴 KPI를
    참고해, 짧은 세션이 많고 긴 세션이 적은 분포를 가정한다.
    """
    rng = np.random.default_rng(seed)
    raw_turns = rng.zipf(zipf_shape, size=n_sessions)
    turns = np.clip(raw_turns, 1, max_turns)
    return pd.DataFrame(
        {
            "session_id": np.arange(1, n_sessions + 1),
            "turns": turns,
            "is_long_session": turns >= 20,
        }
    )


def evaluate_ad_policy(
    sessions: pd.DataFrame,
    first_ad_turn: int,
    second_ad_turn: int | None,
    completion_rate: float = 0.97,
    cpm_krw: float = 2500,
) -> dict:
    """광고 노출 정책 하나를 평가한다.

    산출값은 실제 매출이 아니라 CPM 가정과 completion rate를 넣은 상대 비교용
    수익 가능성이다. UX Risk는 광고가 너무 이른 시점에 나오거나 빈도가 높을 때
    증가하도록 설계했다.
    """
    first_impression = sessions["turns"] >= first_ad_turn
    impressions = first_impression.astype(int)

    if second_ad_turn is not None:
        second_impression = sessions["turns"] >= second_ad_turn
        impressions = impressions + second_impression.astype(int)
    else:
        second_impression = pd.Series(False, index=sessions.index)

    completed_impressions = impressions * completion_rate
    estimated_revenue_krw = completed_impressions.sum() / 1000 * cpm_krw

    avg_impressions = impressions.mean()
    reach_rate = (impressions > 0).mean()
    second_reach_rate = second_impression.mean()
    long_session_reach = sessions.loc[sessions["is_long_session"], "turns"].ge(first_ad_turn).mean()

    # 첫 광고가 8턴보다 빠르면 대화 몰입 전 interrupt로 간주한다.
    early_penalty = max(0, (8 - first_ad_turn) / 7) * 45
    frequency_penalty = min(avg_impressions / 2, 1) * 35
    second_gap = (second_ad_turn - first_ad_turn) if second_ad_turn else 99
    spacing_penalty = max(0, (12 - second_gap) / 12) * 20
    ux_risk_index = round(min(100, early_penalty + frequency_penalty + spacing_penalty), 1)

    return {
        "first_ad_turn": first_ad_turn,
        "second_ad_turn": second_ad_turn if second_ad_turn is not None else 0,
        "completion_rate": completion_rate,
        "cpm_krw": cpm_krw,
        "reach_rate": round(reach_rate, 4),
        "second_reach_rate": round(second_reach_rate, 4),
        "avg_impressions_per_session": round(avg_impressions, 4),
        "estimated_revenue_krw": round(estimated_revenue_krw, 0),
        "long_session_reach_rate": round(float(long_session_reach), 4),
        "ux_risk_index": ux_risk_index,
    }


def build_policy_grid(
    sessions: pd.DataFrame,
    completion_rate: float = 0.97,
    cpm_krw: float = 2500,
) -> pd.DataFrame:
    """광고 노출 후보 정책을 그리드로 평가한다."""
    rows = []
    for first_turn in range(3, 16):
        for second_turn in range(first_turn + 8, first_turn + 26):
            rows.append(
                evaluate_ad_policy(
                    sessions=sessions,
                    first_ad_turn=first_turn,
                    second_ad_turn=second_turn,
                    completion_rate=completion_rate,
                    cpm_krw=cpm_krw,
                )
            )
    df = pd.DataFrame(rows)
    revenue_min = df["estimated_revenue_krw"].min()
    revenue_max = df["estimated_revenue_krw"].max()
    df["ad_revenue_potential"] = (
        100
        * (df["estimated_revenue_krw"] - revenue_min)
        / (revenue_max - revenue_min)
    ).round(1)
    df["balanced_opportunity_score"] = (
        df["ad_revenue_potential"] * 0.55 + (100 - df["ux_risk_index"]) * 0.45
    ).round(1)
    return df.sort_values("balanced_opportunity_score", ascending=False).reset_index(drop=True)


def get_current_policy_result(
    n_sessions: int = 20_000,
    first_ad_turn: int = 4,
    second_ad_turn: int = 19,
    completion_rate: float = 0.97,
    cpm_krw: float = 2500,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """현재 관찰 정책과 후보 정책 결과를 함께 반환한다."""
    sessions = simulate_sessions(n_sessions=n_sessions)
    current = pd.DataFrame(
        [
            evaluate_ad_policy(
                sessions,
                first_ad_turn=first_ad_turn,
                second_ad_turn=second_ad_turn,
                completion_rate=completion_rate,
                cpm_krw=cpm_krw,
            )
        ]
    )
    grid = build_policy_grid(sessions, completion_rate=completion_rate, cpm_krw=cpm_krw)
    return sessions, current, grid

