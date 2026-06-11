import os
import requests
import streamlit as st
from dotenv import load_dotenv, set_key
import yfinance as yf

# ローカルは.env、クラウドはStreamlit Secrets
load_dotenv()

def get_secret(key):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, "－")

API_KEY = get_secret("JQUANTS_API_KEY")
BASE_URL = "https://api.jquants.com/v2"
ENV_PATH = ".env"
IS_LOCAL = not hasattr(st, "secrets") or "JQUANTS_API_KEY" not in st.secrets

st.set_page_config(page_title="指数ダッシュボード", layout="wide")
st.title("📈 TOPIX / 日経225 ダッシュボード")

# --- サイドバー：手動値の更新 ---
with st.sidebar:
    st.header("📝 EPS・PER 手動更新")
    nikkei_eps = st.text_input("日経225 EPS", value=get_secret("NIKKEI_EPS"))
    nikkei_per = st.text_input("日経225 PER", value=get_secret("NIKKEI_PER"))
    topix_eps = st.text_input("TOPIX EPS", value=get_secret("TOPIX_EPS"))
    topix_per = st.text_input("TOPIX PER", value=get_secret("TOPIX_PER"))
    if st.button("保存"):
        if IS_LOCAL:
            set_key(ENV_PATH, "NIKKEI_EPS", nikkei_eps)
            set_key(ENV_PATH, "NIKKEI_PER", nikkei_per)
            set_key(ENV_PATH, "TOPIX_EPS", topix_eps)
            set_key(ENV_PATH, "TOPIX_PER", topix_per)
            load_dotenv(override=True)
            st.success("保存しました（ローカル）")
        else:
            st.warning("クラウドではStreamlit SecretsをWebから更新してください")

# --- yfinanceで日経225価格取得 ---
@st.cache_data(ttl=60)
def get_nikkei_price():
    nikkei = yf.Ticker("^N225")
    price = nikkei.fast_info.get("lastPrice") or nikkei.fast_info.get("regularMarketPrice")
    return price

# --- J-Quants V2で個別銘柄EPS取得 ---
@st.cache_data(ttl=3600)
def get_fin_summary(code):
    headers = {"x-api-key": API_KEY}
    res = requests.get(
        f"{BASE_URL}/fins/summary",
        headers=headers,
        params={"code": code}
    )
    if res.status_code != 200:
        st.error(f"J-Quants エラー: {res.status_code} / {res.text}")
        return None
    records = res.json().get("data", [])
    fy_records = [r for r in records if r.get("CurPerType") == "FY"]
    if not fy_records:
        return None
    latest = fy_records[-1]
    return {
        "開示日": latest.get("DiscDate"),
        "当期終了": latest.get("CurPerEn"),
        "実績EPS": latest.get("EPS"),
        "今期予想EPS": latest.get("FEPS"),
        "来期予想EPS": latest.get("NxFEPS"),
    }

# --- 描画 ---
n_price = get_nikkei_price()

st.subheader("📊 指数価格")
c1, c2 = st.columns(2)
c1.metric("TOPIX", "※Standardプラン必要")
c2.metric("日経225", f"{n_price:,.2f}" if n_price else "取得失敗")

st.divider()

st.subheader("📈 日経225 EPS・PER")
c1, c2 = st.columns(2)
c1.metric("EPS", get_secret("NIKKEI_EPS"))
c2.metric("PER", get_secret("NIKKEI_PER"))
st.caption("※ Streamlit Secretsから読み込み")

st.divider()

st.subheader("📊 TOPIX EPS・PER")
c1, c2 = st.columns(2)
c1.metric("EPS", get_secret("TOPIX_EPS"))
c2.metric("PER", get_secret("TOPIX_PER"))
st.caption("※ Streamlit Secretsから読み込み")

st.divider()

st.subheader("🏭 個別銘柄EPS（J-Quants）")
eps = get_fin_summary("72030")
if eps:
    c1, c2, c3 = st.columns(3)
    c1.metric("実績EPS", eps["実績EPS"] or "－")
    c2.metric("今期予想EPS", eps["今期予想EPS"] or "－")
    c3.metric("来期予想EPS", eps["来期予想EPS"] or "－")
    st.caption(f"トヨタ(7203) 開示日: {eps['開示日']} / 対象期間終了: {eps['当期終了']}")