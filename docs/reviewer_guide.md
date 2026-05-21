# Reviewer Guide

## Fastest Way to Inspect

1. Open the GitHub repository README and review the dashboard screenshot.
2. Read `docs/methodology.md` for the analysis assumptions and limitations.
3. Inspect `sql/analysis_queries.sql` for reproducible SQL outputs.
4. Run the Streamlit app locally if an interactive review is needed.

## Local Run

```bash
pip install -r requirements.txt
python3 scripts/build_database.py
python3 -m streamlit run app.py
```

Open:

```text
http://localhost:8501
```

`localhost` is only available on the machine running Streamlit. For resume or application submission, attach the GitHub URL and, when possible, a Streamlit Cloud deployment URL.

## What to Look For

- `Overview`: analysis question, public-data disclaimer, and core findings
- `Data Pipeline`: source registry, ERD, and SQLite tables
- `EDA & SQL`: query-based analysis results
- `ML Segmentation`: KMeans service positioning
- `Ad Simulator`: ad-timing scenario comparison
- `Strategy`: UX-safe monetization hypotheses and experiment design

## Known Limitations

- No internal ZEPETO revenue, ARPU, churn, or user-log data is used.
- Observed ad timing is based on direct-use observation and should be treated as exploratory.
- CPM and completion rate are scenario assumptions, not actual ZEPETO ad economics.
- KMeans is used for interpretable small-sample segmentation, not prediction.

