import os
import requests
import streamlit as st
from dotenv import load_dotenv, set_key
import yfinance as yf

load_dotenv()
API_KEY = os.getenv("JQUANTS_API_KEY")
BASE_URL = "https://api.jquants.com/v2"
ENV_PATH = ".env"

st.set_page_config(page_title="指数ダッシュボード", layout="wide")
st.title("📈 TOPIX / 日経225 ダッシュボード")

# --- サイドバー：手動値の更新 ---
with st.sidebar:
    st.header("📝 EPS・PER 手動更新")
    nikkei_eps = st.text_input("日経225 EPS", value=os.getenv("NIKKEI_EPS", ""))
    nikkei_per = st.text_input("日経225 PER", value=os.getenv("NIKKEI_PER", ""))
    topix_eps = st.text_input("TOPIX EPS", value=os.getenv("TOPIX_EPS", ""))
    topix_per = st.text_input("TOPIX PER", value=os.getenv("TOPIX_PER", ""))
    if st.button("保存"):
        set_key(ENV_PATH, "NIKKEI_EPS", nikkei_eps)
        set_key(ENV_PATH, "NIKKEI_PER", nikkei_per)
        set_key(ENV_PATH, "TOPIX_EPS", topix_eps)
        set_key(ENV_PATH, "TOPIX_PER", topix_per)
        load_dotenv(override=True)
        st.success("保存しました")

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
c1.metric("EPS", os.getenv("NIKKEI_EPS", "－"))
c2.metric("PER", os.getenv("NIKKEI_PER", "－"))
st.caption("※ サイドバーから更新できます")

st.divider()

st.subheader("📊 TOPIX EPS・PER")
c1, c2 = st.columns(2)
c1.metric("EPS", os.getenv("TOPIX_EPS", "－"))
c2.metric("PER", os.getenv("TOPIX_PER", "－"))
st.caption("※ サイドバーから更新できます")

st.divider()

st.subheader("🏭 個別銘柄EPS（J-Quants）")
eps = get_fin_summary("72030")
if eps:
    c1, c2, c3