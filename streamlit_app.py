"""Streamlit Cloud 호환 진입점.

로컬에서는 `streamlit run app.py`를 권장하지만, 일부 배포 환경이
`streamlit_app.py`를 기본 파일로 찾기 때문에 같은 앱을 다시 호출한다.
"""

from app import main


if __name__ == "__main__":
    main()

