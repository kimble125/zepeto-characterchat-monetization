"""정제 CSV와 SQLite DB를 생성하는 실행 스크립트.

사용 예:
    python3 scripts/build_database.py

면접 설명 포인트:
    1. 로컬 문서/공식 웹/논문/관찰값을 source_registry로 합친다.
    2. 가격과 플랜 구조를 정규화해 CSV와 SQLite에 적재한다.
    3. 대시보드는 이 DB와 동일한 정제 테이블을 읽어 분석한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    # 스크립트를 `python3 scripts/build_database.py`로 실행해도 src 패키지를 찾게 한다.
    sys.path.insert(0, str(ROOT_DIR))

from src.data import DB_PATH, PROCESSED_DIR, build_sqlite_database, export_processed_csvs


def main() -> None:
    export_processed_csvs(PROCESSED_DIR)
    db_path: Path = build_sqlite_database(DB_PATH)
    print(f"Processed CSVs written to: {PROCESSED_DIR}")
    print(f"SQLite database written to: {db_path}")


if __name__ == "__main__":
    main()
