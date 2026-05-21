# ZEPETO CharacterChat Monetization & UX Analytics

Public-data analytics dashboard for ZEPETO CharacterChat monetization, UX, SQL, clustering, and ad-timing simulation.

This project explores one question:

> How can ZEPETO CharacterChat increase monetization potential without damaging user immersion?

## Important Disclaimer

This repository does **not** use ZEPETO internal revenue, ARPU, churn, ad-rate, or user-log data. The analysis is based on public web sources, user-observed pricing and UX notes, academic research, and explicitly documented simulation assumptions.

The output should be read as a **public-data strategy analysis and hypothesis generator**, not as a real revenue forecast.

## Quick Review

```bash
pip install -r requirements.txt
python3 scripts/build_database.py
streamlit run app.py
```

If `streamlit` is not on PATH:

```bash
python3 -m streamlit run app.py
```

Streamlit Cloud can also use `streamlit_app.py` as the entrypoint. A static dashboard screenshot is included below for quick inspection.

![Dashboard overview](screenshots/dashboard_overview.png)

## What This Demonstrates

| Area | Evidence in this repository |
| --- | --- |
| Data collection and source tracking | Public and local-observation sources are normalized into a source registry. |
| Data cleaning | Pricing plans, billing cycles, monthly equivalents, and virtual-currency packages are standardized. |
| SQL and database modeling | SQLite database, ERD, and reusable SQL analysis queries are included. |
| EDA and KPI design | Entry price, monetization complexity, UX fit, metaverse integration, and risk scores are calculated. |
| Research-backed feature engineering | Character design, 3D character AI, typing-awareness, and persona-consistency research are converted into UX variables. |
| Machine learning | KMeans is used for small-sample service segmentation rather than overclaiming predictive accuracy. |
| Simulation | Ad timing scenarios compare estimated revenue potential against UX risk. |
| Dashboard communication | Streamlit tabs translate analysis outputs into product strategy hypotheses. |

## Project Structure

```text
.
├── app.py                         # Streamlit dashboard
├── streamlit_app.py               # Streamlit Cloud compatible entrypoint
├── src/
│   ├── data.py                    # source registry, pricing cleanup, SQLite builder
│   ├── clustering.py              # KMeans segmentation
│   ├── simulation.py              # ad timing simulation
│   └── charts.py                  # Plotly chart helpers
├── scripts/
│   └── build_database.py          # processed CSV + SQLite generation
├── sql/
│   ├── schema.sql                 # ERD-aligned schema
│   └── analysis_queries.sql       # SQL EDA queries
├── docs/
│   ├── erd.md
│   ├── methodology.md
│   └── reviewer_guide.md
├── data/
│   ├── processed/                 # generated CSV outputs
│   └── zepeto_characterchat.db    # generated SQLite DB
└── screenshots/
    └── dashboard_overview.png
```

## Analysis Pipeline

1. **Question framing**: Define UX-safe monetization as the core product question.
2. **Collection**: Combine public web sources, academic research, pricing observations, and direct-use observations.
3. **Cleaning**: Standardize price, billing cycle, monthly equivalent, currency unit, source type, and feature definitions.
4. **EDA**: Compare entry price, plan count, virtual-currency dependence, ad-removal benefits, and service positioning.
5. **ERD/DB**: Build a SQLite database with `services`, `pricing_plans`, `monetization_features`, `ux_research_factors`, `ad_observations`, `simulation_assumptions`, `kpi_results`, and `sources`.
6. **SQL**: Provide reusable queries for pricing, monetization complexity, UX metrics, and source coverage.
7. **ML segmentation**: Use KMeans to group services by pricing, monetization, and UX features.
8. **Simulation**: Use a power-law session-length assumption to compare ad-timing policies.
9. **Dashboard**: Present the analysis in Streamlit as a reviewer-friendly product analytics dashboard.

## Dashboard Tabs

- **Overview**: Analysis question, public-data disclaimer, module summary, core findings
- **Data Pipeline**: Source registry, ERD, SQLite table status
- **Pricing & Monetization**: 5-service pricing and monetization comparison
- **EDA & SQL**: SQL query outputs and KPI definitions
- **ML Segmentation**: KMeans clusters and monetization position map
- **Ad Simulator**: Ad timing scenarios based on observed 4th/19th turn ad exposure
- **Strategy**: ZEPETO application hypotheses, risks, and next experiments

## KPI

| KPI | Meaning |
| --- | --- |
| Entry Price Index | Accessibility score based on the lowest observed entry price |
| Monetization Complexity Score | Combined complexity of subscription, virtual currency, ads, and short-pass mechanics |
| Metaverse Integration Score | Average of Path Search, Action Logic, NPC Response, and Technology Improvement |
| Immersion Fit Score | Estimated fit between character appearance/worldview and chat immersion |
| Persona/Language Fit | Estimated consistency of character voice, persona, and response style |
| Ad Revenue Potential | Relative revenue potential under ad-timing assumptions |
| UX Risk Index | Risk that monetization interrupts user immersion |
| Balanced Opportunity Score | Combined prioritization score across monetization leverage, UX strength, and risk |

## Key Research Sources

- [Character.AI c.ai+](https://character.ai/subscribe)
- [Replika subscription guide](https://help.replika.com/hc/en-us/articles/39551043419149-Choosing-a-Subscription)
- [ZEPETO Premium benefits](https://support.zepeto.me/hc/en-us/articles/4402066761369-What-are-Premium-Regular-Subscription-Benefits)
- [Zeta Pass announcement](https://zeta-ai.io/en/Announcements/9343)
- [Generative AI-based character chatbot design study](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003229348)
- [3D character AI system analysis for metaverse content](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003012083)
- [Display Methods of Text Input Awareness in Real Time](https://www.jstage.jst.go.jp/article/his/19/2/19_141/_article/-char/en)
- [The Design and Implementation of XiaoIce](https://arxiv.org/abs/1812.08989)
- [PersonaCLR](https://aclanthology.org/2024.sigdial-1.58/)
- [Persona-consistent dialogue research](https://aclanthology.org/2023.emnlp-main.110/)
- [AppsFlyer mid-roll ads](https://www.appsflyer.com/blog/tips-strategy/mid-roll-ads/)
- [NAVER Z](https://www.naverz-corp.com/)

## Recommended Repository Metadata

**About**

Public-data analytics dashboard for ZEPETO CharacterChat monetization, UX, SQL, clustering, and ad-timing simulation.

**Topics**

`streamlit`, `python`, `sql`, `sqlite`, `data-analysis`, `eda`, `clustering`, `dashboard`, `zepeto`, `monetization`, `ai-character`, `simulation`, `public-data`

