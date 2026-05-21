"""공개 자료 기반 제페토 캐릭터챗 수익화 분석 데이터 파이프라인.

이 모듈은 실제 내부 매출이나 유저 로그가 아니라, 사용자가 제공한 로컬 문서,
공개 웹 자료, 논문, 직접 사용 관찰값을 분석용 테이블로 표준화한다.
분석 흐름을 추적하기 쉽도록 원천 데이터 -> 정제 테이블 -> SQLite 적재 흐름을
명시적으로 분리했다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "zepeto_characterchat.db"


def _monthly_equivalent(price_krw: float, billing_cycle_months: float) -> float:
    """결제 주기가 다른 가격을 월 환산가로 맞춘다."""
    return round(price_krw / billing_cycle_months, 2)


def get_sources() -> pd.DataFrame:
    """분석에 사용한 출처 레지스트리.

    source_type은 데이터 신뢰도와 사용 목적을 설명하기 위한 구분값이다.
    - official: 서비스 공식 가격/도움말/회사 페이지
    - local_observation: 직접 사용 관찰 및 사용자가 제공한 캡처/문서
    - academic: 논문 또는 학술 자료
    - industry: 산업 리포트/측정 연구/외부 추정
    """
    rows = [
        {
            "source_id": "local_price_summary",
            "title": "AI 캐릭터 서비스들의 가격, 플랜 구조 요약 및 Zepeto 플랜 분석",
            "source_type": "local_observation",
            "url": "",
            "local_path": "AI 캐릭터 서비스들의 가격, 플랜 구조 요약 및 Zepeto 플랜 분석.md",
            "used_for": "서비스별 가격, 플랜 구조, 재화 패키지 정리",
            "reliability_note": "사용자 제공 관찰 정리본. 스크린샷 기반 수동 수집값",
        },
        {
            "source_id": "local_experience",
            "title": "캐릭터챗 경험 및 심화 분석",
            "source_type": "local_observation",
            "url": "",
            "local_path": "[네이버Z]캐릭터챗 경험 및 심화 분석.md",
            "used_for": "제페토 광고 노출 시점, UX 장단점, 서비스 비교 관찰",
            "reliability_note": "직접 사용 관찰값. 표본이 작아 가설 생성용으로만 사용",
        },
        {
            "source_id": "character_ai_subscribe",
            "title": "Character.AI c.ai+ subscription page",
            "source_type": "official",
            "url": "https://character.ai/subscribe",
            "local_path": "",
            "used_for": "Character.AI 구독 플랜 확인",
            "reliability_note": "공식 페이지이나 가격은 지역/시점에 따라 변동 가능",
        },
        {
            "source_id": "replika_subscription",
            "title": "Replika subscription guide",
            "source_type": "official",
            "url": "https://help.replika.com/hc/en-us/articles/39551043419149-Choosing-a-Subscription",
            "local_path": "",
            "used_for": "Replika 유료 플랜 구조 확인",
            "reliability_note": "공식 도움말. 실제 앱스토어 가격은 지역별로 다를 수 있음",
        },
        {
            "source_id": "zepeto_premium",
            "title": "ZEPETO Premium Regular Subscription Benefits",
            "source_type": "official",
            "url": "https://support.zepeto.me/hc/en-us/articles/4402066761369-What-are-Premium-Regular-Subscription-Benefits",
            "local_path": "",
            "used_for": "ZEPETO Premium 혜택 구조 확인",
            "reliability_note": "공식 도움말. 분석에는 로컬 가격 관찰값을 함께 사용",
        },
        {
            "source_id": "zeta_pass",
            "title": "Zeta Pass announcement",
            "source_type": "official",
            "url": "https://zeta-ai.io/en/Announcements/9343",
            "local_path": "",
            "used_for": "Zeta Pass 및 단기 패스 구조 확인",
            "reliability_note": "공식 공지. 앱/웹 가격 차이는 로컬 관찰값으로 보강",
        },
        {
            "source_id": "scatter_lab_intro",
            "title": "Scatter Lab introduction",
            "source_type": "official",
            "url": "https://www.scatterlab.co.kr/en/intro",
            "local_path": "",
            "used_for": "Zeta 운영사 및 AI companion 서비스 맥락",
            "reliability_note": "회사 소개 페이지",
        },
        {
            "source_id": "kci_character_design_2025",
            "title": "생성형 AI 기반 캐릭터 챗봇 디자인에 대한 사용자 반응 유형별 분석",
            "source_type": "academic",
            "url": "https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003229348",
            "local_path": "생성형 AI 기반 캐릭터 챗봇 디자인에 대한 사용자 반응 유형별 분석 -외형적 특징과 언어 스타일을 중심으로-.pdf",
            "used_for": "외형, 언어 스타일, 감정 반응, 몰입 관련 UX 변수화",
            "reliability_note": "KCI 등재 논문. DOI: https://doi.org/10.25111/jcd.2025.92.24",
        },
        {
            "source_id": "kci_3d_character_ai_2023",
            "title": "메타버스 콘텐츠를 위한 3D 캐릭터 AI 시스템분석",
            "source_type": "academic",
            "url": "https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003012083",
            "local_path": "메타버스 콘텐츠를 위한 3D 캐릭터 AI 시스템분석.pdf",
            "used_for": "3D/메타버스 AI 캐릭터의 Path Search, Action Logic, NPC Response, Technology Improvement 변수화",
            "reliability_note": "KCI 등재 논문. DOI: https://doi.org/10.25111/jcd.2023.85.36",
        },
        {
            "source_id": "hattori_interchat_2017",
            "title": "Display Methods of Text Input Awareness in Real Time for the Typing-Driven Embodied Entrainment Character Chat System",
            "source_type": "academic",
            "url": "https://www.jstage.jst.go.jp/article/his/19/2/19_141/_article/-char/en",
            "local_path": "Display Methods of Text Input Awareness in Real Time for the Typing-Driven Embodied Entrainment Character Chat System_Hattori, Kenji.pdf",
            "used_for": "실시간 입력 인식, 타이핑 리듬, embodied interaction 근거",
            "reliability_note": "J-STAGE 논문. 캐릭터챗 몰입 UX 변수화에 사용",
        },
        {
            "source_id": "xiaoice_2018",
            "title": "The Design and Implementation of XiaoIce, an Empathetic Social Chatbot",
            "source_type": "academic",
            "url": "https://arxiv.org/abs/1812.08989",
            "local_path": "",
            "used_for": "Conversation-turns Per Session을 참여 KPI로 사용하는 근거",
            "reliability_note": "대화형 AI 서비스의 장기 참여 KPI 참고",
        },
        {
            "source_id": "ai_companion_longitudinal_2025",
            "title": "Longitudinal study on AI companion engagement",
            "source_type": "academic",
            "url": "https://arxiv.org/abs/2510.10079",
            "local_path": "",
            "used_for": "AI companion 장기 관계와 engagement 논의 보조",
            "reliability_note": "최신 arXiv 연구. 대시보드에서는 보조 해석 근거로만 사용",
        },
        {
            "source_id": "persona_clr_2024",
            "title": "PersonaCLR: Persona Consistency Learning in Dialogue",
            "source_type": "academic",
            "url": "https://aclanthology.org/2024.sigdial-1.58/",
            "local_path": "",
            "used_for": "캐릭터 일관성 및 Persona/Language Fit 변수화",
            "reliability_note": "SIGDIAL 논문",
        },
        {
            "source_id": "persona_dialogue_2023",
            "title": "Persona-consistent dialogue research",
            "source_type": "academic",
            "url": "https://aclanthology.org/2023.emnlp-main.110/",
            "local_path": "",
            "used_for": "페르소나 일관성 평가 근거 보조",
            "reliability_note": "EMNLP 논문",
        },
        {
            "source_id": "appsflyer_midroll",
            "title": "AppsFlyer mid-roll ads guide",
            "source_type": "industry",
            "url": "https://www.appsflyer.com/blog/tips-strategy/mid-roll-ads/",
            "local_path": "",
            "used_for": "미드롤 광고 완료율 97%, 프리롤 74% 비교 근거",
            "reliability_note": "산업 블로그. 광고 시뮬레이션의 민감도 가정으로 사용",
        },
        {
            "source_id": "umass_video_ads",
            "title": "Understanding the effectiveness of video ads: a measurement study",
            "source_type": "academic",
            "url": "https://groups.cs.umass.edu/wp-content/uploads/sites/3/2019/12/Understanding-the-effectiveness-of-video-ads-a-measurement-study.pdf",
            "local_path": "",
            "used_for": "비디오 광고 효과와 completion 관찰의 보조 근거",
            "reliability_note": "측정 연구. 서비스 맥락이 달라 직접 추정에는 제한",
        },
        {
            "source_id": "naver_z_corp",
            "title": "NAVER Z corporate website",
            "source_type": "official",
            "url": "https://www.naverz-corp.com/",
            "local_path": "",
            "used_for": "제페토 글로벌/메타버스 서비스 맥락",
            "reliability_note": "공식 회사 사이트",
        },
        {
            "source_id": "prnewswire_naverz_true",
            "title": "NAVER Z joins hands with TRUE",
            "source_type": "industry",
            "url": "https://en.prnasia.com/releases/apac/naver-z-joins-hands-with-true-to-power-metaverse-ecosystem-in-thailand-373905.shtml",
            "local_path": "",
            "used_for": "ZEPETO 340M users, 90% overseas, 200+ countries 맥락",
            "reliability_note": "보도자료 기반 공개 지표",
        },
        {
            "source_id": "sacra_character_ai",
            "title": "Sacra Character.AI revenue estimate",
            "source_type": "industry",
            "url": "https://sacra.com/c/character-ai/",
            "local_path": "",
            "used_for": "AI character market monetization context",
            "reliability_note": "외부 추정치. 직접 비교 KPI에는 사용하지 않고 시장 맥락으로만 사용",
        },
    ]
    return pd.DataFrame(rows)


def get_services() -> pd.DataFrame:
    """서비스 단위 마스터 테이블."""
    rows = [
        {
            "service_id": "character_ai",
            "service_name": "Character.AI",
            "company": "Character Technologies",
            "home_market": "US/global",
            "service_positioning": "범용 캐릭터 대화와 팬덤형 챗봇",
            "primary_monetization": "subscription",
            "zepeto_relevance": "캐릭터챗 직접 경쟁 벤치마크",
            "source_id": "character_ai_subscribe",
        },
        {
            "service_id": "talkie",
            "service_name": "Talkie",
            "company": "SUBSUP / Talkie",
            "home_market": "global",
            "service_positioning": "음성/카드형 AI 캐릭터 대화",
            "primary_monetization": "subscription",
            "zepeto_relevance": "UX 완성도와 캐릭터 탐색 벤치마크",
            "source_id": "local_price_summary",
        },
        {
            "service_id": "replika",
            "service_name": "Replika",
            "company": "Luka",
            "home_market": "US/global",
            "service_positioning": "장기 관계형 AI companion",
            "primary_monetization": "subscription",
            "zepeto_relevance": "AI companion 장기 engagement 벤치마크",
            "source_id": "replika_subscription",
        },
        {
            "service_id": "zepeto",
            "service_name": "ZEPETO CharacterChat",
            "company": "NAVER Z",
            "home_market": "KR/global",
            "service_positioning": "3D 아바타·월드 기반 메타버스 캐릭터챗",
            "primary_monetization": "subscription_currency_ads",
            "zepeto_relevance": "분석 대상 서비스",
            "source_id": "zepeto_premium",
        },
        {
            "service_id": "zeta",
            "service_name": "Zeta",
            "company": "Scatter Lab",
            "home_market": "KR/global",
            "service_positioning": "몰입형 역할극과 AI companion",
            "primary_monetization": "subscription_currency",
            "zepeto_relevance": "국내 AI companion 및 패스형 수익화 벤치마크",
            "source_id": "zeta_pass",
        },
    ]
    return pd.DataFrame(rows)


def get_pricing_plans() -> pd.DataFrame:
    """가격·플랜 원천값을 월 환산가와 함께 정리한다.

    정확한 내부 매출 계산이 아니라 공개 가격 구조 비교가 목적이다.
    """
    rows = [
        {
            "plan_id": "cai_plus_monthly",
            "service_id": "character_ai",
            "plan_name": "c.ai+ Monthly",
            "plan_type": "subscription",
            "price_krw": 14000,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "우선 접속, 빠른 응답 등 유료 구독 혜택",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "cai_plus_annual",
            "service_id": "character_ai",
            "plan_name": "c.ai+ Annual",
            "plan_type": "subscription",
            "price_krw": 129000,
            "billing_cycle_months": 12,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "연간 결제 할인",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "talkie_standard_monthly",
            "service_id": "talkie",
            "plan_name": "Talkie+ Standard Monthly",
            "plan_type": "subscription",
            "price_krw": 14000,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Talkie+ Standard 월간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "talkie_standard_quarterly",
            "service_id": "talkie",
            "plan_name": "Talkie+ Standard Quarterly",
            "plan_type": "subscription",
            "price_krw": 44000,
            "billing_cycle_months": 3,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "분기 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "talkie_standard_annual",
            "service_id": "talkie",
            "plan_name": "Talkie+ Standard Annual",
            "plan_type": "subscription",
            "price_krw": 66000,
            "billing_cycle_months": 12,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "연간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "replika_pro_annual",
            "service_id": "replika",
            "plan_name": "Replika Pro Annual",
            "plan_type": "subscription",
            "price_krw": 71500,
            "billing_cycle_months": 12,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Pro 연간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "replika_ultra_annual",
            "service_id": "replika",
            "plan_name": "Replika Ultra Annual",
            "plan_type": "subscription",
            "price_krw": 81000,
            "billing_cycle_months": 12,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Ultra 연간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "replika_platinum_annual",
            "service_id": "replika",
            "plan_name": "Replika Platinum Annual",
            "plan_type": "subscription",
            "price_krw": 91000,
            "billing_cycle_months": 12,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Platinum 연간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_premium_lite",
            "service_id": "zepeto",
            "plan_name": "ZEPETO Premium Lite",
            "plan_type": "subscription",
            "price_krw": 1500,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "첫 구독 50% 할인 관찰가. 원가 3,000원",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_premium_basic",
            "service_id": "zepeto",
            "plan_name": "ZEPETO Premium Basic",
            "plan_type": "subscription",
            "price_krw": 6000,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Premium Basic 월간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_premium_plus",
            "service_id": "zepeto",
            "plan_name": "ZEPETO Premium Plus",
            "plan_type": "subscription",
            "price_krw": 15000,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "Premium Plus 월간 구독",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_15",
            "service_id": "zepeto",
            "plan_name": "15 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 1500,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 15,
            "benefit_summary": "소액 젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_30",
            "service_id": "zepeto",
            "plan_name": "30 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 3000,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 30,
            "benefit_summary": "젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_60",
            "service_id": "zepeto",
            "plan_name": "60 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 5800,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 60,
            "benefit_summary": "젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_150",
            "service_id": "zepeto",
            "plan_name": "150 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 14500,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 150,
            "benefit_summary": "젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_500",
            "service_id": "zepeto",
            "plan_name": "500 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 47500,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 500,
            "benefit_summary": "대용량 젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_gems_3000",
            "service_id": "zepeto",
            "plan_name": "3000 Gems",
            "plan_type": "virtual_currency",
            "price_krw": 279000,
            "billing_cycle_months": 1,
            "currency_unit": "gems",
            "currency_amount": 3000,
            "benefit_summary": "최대 젬 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_coins_5000",
            "service_id": "zepeto",
            "plan_name": "5,000 Coins",
            "plan_type": "virtual_currency",
            "price_krw": 1500,
            "billing_cycle_months": 1,
            "currency_unit": "coins",
            "currency_amount": 5000,
            "benefit_summary": "소액 코인 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_coins_10000",
            "service_id": "zepeto",
            "plan_name": "10,000 Coins",
            "plan_type": "virtual_currency",
            "price_krw": 3000,
            "billing_cycle_months": 1,
            "currency_unit": "coins",
            "currency_amount": 10000,
            "benefit_summary": "코인 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zepeto_coins_30000",
            "service_id": "zepeto",
            "plan_name": "30,000 Coins",
            "plan_type": "virtual_currency",
            "price_krw": 8500,
            "billing_cycle_months": 1,
            "currency_unit": "coins",
            "currency_amount": 30000,
            "benefit_summary": "대용량 코인 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_pass_1day",
            "service_id": "zeta",
            "plan_name": "Zeta 1-day Pass",
            "plan_type": "short_pass",
            "price_krw": 2800,
            "billing_cycle_months": 1 / 30,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "1일 패스. 단기 체험 패스형 과금",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_pass_web_monthly",
            "service_id": "zeta",
            "plan_name": "Zeta Pass Web Monthly",
            "plan_type": "subscription",
            "price_krw": 10900,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "웹 월간 패스",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_pass_app_monthly",
            "service_id": "zeta",
            "plan_name": "Zeta Pass App Monthly",
            "plan_type": "subscription",
            "price_krw": 14900,
            "billing_cycle_months": 1,
            "currency_unit": "",
            "currency_amount": np.nan,
            "benefit_summary": "앱 월간 패스",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_200",
            "service_id": "zeta",
            "plan_name": "200 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 2800,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 200,
            "benefit_summary": "소액 조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_500",
            "service_id": "zeta",
            "plan_name": "500 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 7000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 500,
            "benefit_summary": "조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_1000",
            "service_id": "zeta",
            "plan_name": "1,000 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 14000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 1000,
            "benefit_summary": "조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_2000",
            "service_id": "zeta",
            "plan_name": "2,000 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 28000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 2000,
            "benefit_summary": "조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_3000",
            "service_id": "zeta",
            "plan_name": "3,000 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 42000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 3000,
            "benefit_summary": "조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_5000",
            "service_id": "zeta",
            "plan_name": "5,000 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 70000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 5000,
            "benefit_summary": "대용량 조각 패키지",
            "source_id": "local_price_summary",
        },
        {
            "plan_id": "zeta_piece_10000",
            "service_id": "zeta",
            "plan_name": "10,000 Pieces",
            "plan_type": "virtual_currency",
            "price_krw": 140000,
            "billing_cycle_months": 1,
            "currency_unit": "pieces",
            "currency_amount": 10000,
            "benefit_summary": "최대 조각 패키지",
            "source_id": "local_price_summary",
        },
    ]
    df = pd.DataFrame(rows)
    df["monthly_equivalent_krw"] = df.apply(
        lambda row: _monthly_equivalent(row["price_krw"], row["billing_cycle_months"]),
        axis=1,
    )
    df["unit_price_krw"] = np.where(
        df["currency_amount"].notna() & (df["currency_amount"] > 0),
        (df["price_krw"] / df["currency_amount"]).round(4),
        np.nan,
    )
    return df


def get_monetization_features() -> pd.DataFrame:
    """서비스별 수익화/UX 피처를 0~5점 척도로 변수화한다.

    점수는 실제 내부 데이터가 아니라 가격 구조, 직접 관찰, 논문 근거를
    조합한 휴리스틱이다. 따라서 대시보드에서도 '가설 생성용 추정'이라고 표시한다.
    """
    rows = [
        {
            "service_id": "character_ai",
            "has_subscription": 1,
            "has_virtual_currency": 0,
            "has_ads_observed": 0,
            "has_ad_removal_plan": 1,
            "has_short_pass": 0,
            "virtual_currency_dependency": 0.0,
            "monetization_complexity_score": 1.7,
            "path_search": 1.0,
            "action_logic": 1.2,
            "npc_response": 3.8,
            "technology_improvement": 3.2,
            "immersion_fit_score": 3.8,
            "persona_language_fit": 4.2,
            "interaction_awareness_score": 3.4,
            "source_id": "local_experience",
            "feature_note": "강한 캐릭터 대화 자산이 있으나 3D/월드 연계는 약함",
        },
        {
            "service_id": "talkie",
            "has_subscription": 1,
            "has_virtual_currency": 0,
            "has_ads_observed": 0,
            "has_ad_removal_plan": 0,
            "has_short_pass": 0,
            "virtual_currency_dependency": 0.0,
            "monetization_complexity_score": 2.8,
            "path_search": 1.5,
            "action_logic": 2.0,
            "npc_response": 3.6,
            "technology_improvement": 3.5,
            "immersion_fit_score": 3.5,
            "persona_language_fit": 3.7,
            "interaction_awareness_score": 4.0,
            "source_id": "local_experience",
            "feature_note": "음성 재생, 챗 인스피레이션 등 채팅 UX 기능이 강함",
        },
        {
            "service_id": "replika",
            "has_subscription": 1,
            "has_virtual_currency": 0,
            "has_ads_observed": 0,
            "has_ad_removal_plan": 0,
            "has_short_pass": 0,
            "virtual_currency_dependency": 0.0,
            "monetization_complexity_score": 3.1,
            "path_search": 1.2,
            "action_logic": 2.2,
            "npc_response": 4.0,
            "technology_improvement": 3.8,
            "immersion_fit_score": 4.4,
            "persona_language_fit": 4.0,
            "interaction_awareness_score": 3.8,
            "source_id": "replika_subscription",
            "feature_note": "장기 관계형 AI companion 포지션",
        },
        {
            "service_id": "zepeto",
            "has_subscription": 1,
            "has_virtual_currency": 1,
            "has_ads_observed": 1,
            "has_ad_removal_plan": 0,
            "has_short_pass": 0,
            "virtual_currency_dependency": 5.0,
            "monetization_complexity_score": 5.0,
            "path_search": 4.5,
            "action_logic": 4.4,
            "npc_response": 3.4,
            "technology_improvement": 4.7,
            "immersion_fit_score": 3.6,
            "persona_language_fit": 3.2,
            "interaction_awareness_score": 3.2,
            "source_id": "local_experience",
            "feature_note": "아바타/월드/재화/광고를 결합할 수 있는 메타버스 수익화 레버 보유",
        },
        {
            "service_id": "zeta",
            "has_subscription": 1,
            "has_virtual_currency": 1,
            "has_ads_observed": 1,
            "has_ad_removal_plan": 1,
            "has_short_pass": 1,
            "virtual_currency_dependency": 4.0,
            "monetization_complexity_score": 4.2,
            "path_search": 1.8,
            "action_logic": 2.5,
            "npc_response": 4.3,
            "technology_improvement": 3.7,
            "immersion_fit_score": 4.5,
            "persona_language_fit": 4.3,
            "interaction_awareness_score": 3.8,
            "source_id": "zeta_pass",
            "feature_note": "세계관 설정과 단기 패스/재화 결합이 강점",
        },
    ]
    df = pd.DataFrame(rows)
    df["metaverse_integration_score"] = df[
        ["path_search", "action_logic", "npc_response", "technology_improvement"]
    ].mean(axis=1).round(2)
    return df


def get_ux_research_factors() -> pd.DataFrame:
    """논문 근거를 대시보드 변수로 변환한 테이블."""
    rows = [
        {
            "factor_id": "appearance_fit",
            "factor_name": "Appearance Fit",
            "source_id": "kci_character_design_2025",
            "research_signal": "캐릭터 외형적 특징은 감정 반응과 몰입에 영향을 준다.",
            "dashboard_metric": "Immersion Fit Score",
            "operational_definition": "아바타/캐릭터의 시각적 정체성이 대화 몰입을 돕는 정도",
        },
        {
            "factor_id": "language_style_fit",
            "factor_name": "Persona/Language Fit",
            "source_id": "kci_character_design_2025",
            "research_signal": "언어 스타일과 사용자 유형의 적합성이 캐릭터챗 반응을 가른다.",
            "dashboard_metric": "Persona/Language Fit",
            "operational_definition": "캐릭터 말투, 세계관, 응답 일관성이 사용자 기대와 맞는 정도",
        },
        {
            "factor_id": "path_search",
            "factor_name": "Path Search",
            "source_id": "kci_3d_character_ai_2023",
            "research_signal": "3D 캐릭터 AI 시스템은 이동 경로 탐색과 공간 인식이 중요하다.",
            "dashboard_metric": "Metaverse Integration Score",
            "operational_definition": "캐릭터챗이 월드/공간/위치 맥락과 결합될 가능성",
        },
        {
            "factor_id": "action_logic",
            "factor_name": "Action Logic",
            "source_id": "kci_3d_character_ai_2023",
            "research_signal": "캐릭터의 행동 논리는 메타버스 콘텐츠 몰입을 구성한다.",
            "dashboard_metric": "Metaverse Integration Score",
            "operational_definition": "대화 결과가 포즈, 애니메이션, 퀘스트 행동으로 이어질 가능성",
        },
        {
            "factor_id": "npc_response",
            "factor_name": "NPC Response",
            "source_id": "kci_3d_character_ai_2023",
            "research_signal": "NPC 반응 품질은 3D 캐릭터 AI의 핵심 평가 축이다.",
            "dashboard_metric": "Metaverse Integration Score",
            "operational_definition": "캐릭터 응답의 자연스러움과 상황 반응성",
        },
        {
            "factor_id": "typing_awareness",
            "factor_name": "Typing Input Awareness",
            "source_id": "hattori_interchat_2017",
            "research_signal": "실시간 입력 표시와 타이핑 리듬은 embodied interaction 경험을 강화한다.",
            "dashboard_metric": "Interaction Awareness Score",
            "operational_definition": "상대가 입력 중이라는 리듬감, 실시간성, 응답 대기 UX",
        },
        {
            "factor_id": "conversation_turns",
            "factor_name": "Conversation-turns Per Session",
            "source_id": "xiaoice_2018",
            "research_signal": "XiaoIce 연구는 세션당 대화 턴을 engagement KPI로 사용한다.",
            "dashboard_metric": "Ad Simulator",
            "operational_definition": "광고 노출 시점이 세션 길이와 충돌하는지 평가하는 기준",
        },
        {
            "factor_id": "persona_consistency",
            "factor_name": "Persona Consistency",
            "source_id": "persona_clr_2024",
            "research_signal": "페르소나 일관성은 캐릭터 대화 품질의 핵심 축이다.",
            "dashboard_metric": "Persona/Language Fit",
            "operational_definition": "대화가 길어져도 캐릭터 설정과 말투가 유지되는 정도",
        },
    ]
    return pd.DataFrame(rows)


def get_ad_observations() -> pd.DataFrame:
    """직접 사용 관찰과 산업 근거를 합친 광고 관련 입력값."""
    rows = [
        {
            "observation_id": "zepeto_ad_first_turn",
            "service_id": "zepeto",
            "observation_type": "direct_use",
            "turn_number": 4,
            "minutes_from_start": 5,
            "value": 1.0,
            "unit": "ad_impression",
            "source_id": "local_experience",
            "note": "제페토 캐릭터챗 직접 사용 중 약 4번째 발화 전후 광고 관찰",
        },
        {
            "observation_id": "zepeto_ad_second_turn",
            "service_id": "zepeto",
            "observation_type": "direct_use",
            "turn_number": 19,
            "minutes_from_start": 10,
            "value": 1.0,
            "unit": "ad_impression",
            "source_id": "local_experience",
            "note": "약 19번째 발화 이후 추가 광고 관찰",
        },
        {
            "observation_id": "midroll_completion_rate",
            "service_id": "industry",
            "observation_type": "benchmark",
            "turn_number": np.nan,
            "minutes_from_start": np.nan,
            "value": 0.97,
            "unit": "completion_rate",
            "source_id": "appsflyer_midroll",
            "note": "미드롤 광고 완료율 벤치마크",
        },
        {
            "observation_id": "preroll_completion_rate",
            "service_id": "industry",
            "observation_type": "benchmark",
            "turn_number": np.nan,
            "minutes_from_start": np.nan,
            "value": 0.74,
            "unit": "completion_rate",
            "source_id": "appsflyer_midroll",
            "note": "프리롤 광고 완료율 벤치마크",
        },
    ]
    return pd.DataFrame(rows)


def get_simulation_assumptions() -> pd.DataFrame:
    """광고 시뮬레이션에서 사용하는 명시적 가정."""
    rows = [
        {
            "assumption_id": "session_distribution",
            "assumption_name": "Power-law conversation length",
            "value": 1.85,
            "unit": "zipf_shape",
            "description": "대화 세션 길이는 짧은 세션이 많고 긴 세션이 적은 멱법칙 분포로 가정",
            "source_id": "xiaoice_2018",
        },
        {
            "assumption_id": "max_turn_clip",
            "assumption_name": "Max simulated turns",
            "value": 80,
            "unit": "turns",
            "description": "극단적으로 긴 세션이 평균을 왜곡하지 않도록 최대 발화 수를 80으로 절단",
            "source_id": "xiaoice_2018",
        },
        {
            "assumption_id": "ad_cpm",
            "assumption_name": "Rewarded/mid-roll CPM scenario",
            "value": 2500,
            "unit": "KRW per 1000 completed impressions",
            "description": "실제 제페토 광고 단가가 아닌 민감도 분석용 CPM 가정",
            "source_id": "appsflyer_midroll",
        },
        {
            "assumption_id": "current_first_ad_turn",
            "assumption_name": "Observed first ad timing",
            "value": 4,
            "unit": "turn",
            "description": "직접 관찰된 첫 광고 노출 시점",
            "source_id": "local_experience",
        },
        {
            "assumption_id": "current_second_ad_turn",
            "assumption_name": "Observed second ad timing",
            "value": 19,
            "unit": "turn",
            "description": "직접 관찰된 두 번째 광고 노출 시점",
            "source_id": "local_experience",
        },
    ]
    return pd.DataFrame(rows)


def get_service_feature_matrix() -> pd.DataFrame:
    """KMeans와 KPI 계산에 사용하는 서비스 단위 피처 테이블."""
    services = get_services()[["service_id", "service_name"]]
    pricing = get_pricing_plans()
    features = get_monetization_features()

    pricing_summary = (
        pricing.groupby("service_id")
        .agg(
            entry_price_krw=("price_krw", "min"),
            min_monthly_equivalent_krw=("monthly_equivalent_krw", "min"),
            max_price_krw=("price_krw", "max"),
            plan_count=("plan_id", "count"),
            subscription_plan_count=("plan_type", lambda x: int((x == "subscription").sum())),
            virtual_currency_plan_count=("plan_type", lambda x: int((x == "virtual_currency").sum())),
            plan_type_count=("plan_type", "nunique"),
        )
        .reset_index()
    )

    df = services.merge(pricing_summary, on="service_id", how="left").merge(
        features, on="service_id", how="left"
    )
    df["entry_price_index"] = (
        100 * (1 - (df["entry_price_krw"] - df["entry_price_krw"].min()) / (df["entry_price_krw"].max() - df["entry_price_krw"].min()))
    ).round(1)
    df["metaverse_integration_score_100"] = (df["metaverse_integration_score"] * 20).round(1)
    df["immersion_fit_score_100"] = (df["immersion_fit_score"] * 20).round(1)
    df["persona_language_fit_100"] = (df["persona_language_fit"] * 20).round(1)
    df["monetization_complexity_score_100"] = (
        df["monetization_complexity_score"] * 20
    ).round(1)
    return df


def get_kpi_results() -> pd.DataFrame:
    """대시보드에서 바로 보여줄 서비스별 KPI 결과."""
    df = get_service_feature_matrix()

    # 유저 경험을 덜 해치면서 수익화 기회가 큰지를 보는 균형 지표.
    # 실제 매출 예측이 아니라 후보 전략 우선순위화를 위한 점수다.
    df["ux_strength"] = (
        df["metaverse_integration_score_100"] * 0.35
        + df["immersion_fit_score_100"] * 0.35
        + df["persona_language_fit_100"] * 0.20
        + df["interaction_awareness_score"] * 20 * 0.10
    ).round(1)
    df["monetization_leverage"] = (
        df["entry_price_index"] * 0.25
        + df["monetization_complexity_score_100"] * 0.35
        + df["virtual_currency_dependency"] * 20 * 0.20
        + df["has_ads_observed"] * 100 * 0.20
    ).round(1)
    df["ux_risk_index"] = (
        0.45 * df["monetization_complexity_score_100"]
        + 0.35 * df["has_ads_observed"] * 100
        + 0.20 * (100 - df["immersion_fit_score_100"])
    ).round(1)
    df["balanced_opportunity_score"] = (
        df["monetization_leverage"] * 0.45
        + df["ux_strength"] * 0.45
        + (100 - df["ux_risk_index"]) * 0.10
    ).round(1)
    cols = [
        "service_id",
        "service_name",
        "entry_price_index",
        "monetization_complexity_score_100",
        "metaverse_integration_score_100",
        "immersion_fit_score_100",
        "persona_language_fit_100",
        "ux_strength",
        "monetization_leverage",
        "ux_risk_index",
        "balanced_opportunity_score",
    ]
    return df[cols]


def prepare_processed_tables() -> Dict[str, pd.DataFrame]:
    """원천 테이블과 파생 테이블을 한 번에 생성한다."""
    tables: Dict[str, pd.DataFrame] = {
        "sources": get_sources(),
        "services": get_services(),
        "pricing_plans": get_pricing_plans(),
        "monetization_features": get_monetization_features(),
        "ux_research_factors": get_ux_research_factors(),
        "ad_observations": get_ad_observations(),
        "simulation_assumptions": get_simulation_assumptions(),
        "service_feature_matrix": get_service_feature_matrix(),
        "kpi_results": get_kpi_results(),
    }
    return tables


def export_processed_csvs(output_dir: Path = PROCESSED_DIR) -> None:
    """정제 테이블을 CSV로 저장한다."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for table_name, df in prepare_processed_tables().items():
        df.to_csv(output_dir / f"{table_name}.csv", index=False)


def build_sqlite_database(db_path: Path = DB_PATH) -> Path:
    """정제 테이블을 SQLite 데이터베이스로 적재한다."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        # 스키마가 바뀌어도 오래된 테이블이 남지 않도록 DB 파일을 새로 만든다.
        db_path.unlink()
    tables = prepare_processed_tables()
    with sqlite3.connect(db_path) as conn:
        for table_name, df in tables.items():
            df.to_sql(table_name, conn, if_exists="replace", index=False)
    return db_path


def load_table(table_name: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """SQLite에서 테이블 하나를 읽는다. DB가 없으면 즉시 재생성한다."""
    if not db_path.exists():
        build_sqlite_database(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


def run_sql_query(query: str, db_path: Path = DB_PATH) -> pd.DataFrame:
    """대시보드에서 SQL 분석 결과를 보여주기 위한 헬퍼."""
    if not db_path.exists():
        build_sqlite_database(db_path)
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn)
