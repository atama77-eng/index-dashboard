import os
import requests
import streamlit as st
from dotenv import load_dotenv, set_key
import yfinance as yf

load_dotenv()

def get_secret(key, default="－"):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

API_KEY = get_secret("JQUANTS_API_KEY")
BASE_URL = "https://api.jquants.com/v2"
ENV_PATH = ".env"

def is_local():
    try:
        return "JQUANTS_API_KEY" not in st.secrets
    except Exception:
        return True

IS_LOCAL = is_local()

st.set_page_config(page_title="指数ダッシュボード", layout="wide", page_icon="◆")

# --- カスタムスタイル（ダーク・シャープテーマ） ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #EAF4F7;
    --bg-panel: #FFFFFF;
    --line: #C3D9E0;
    --text: #1A1A1A;
    --text-dim: #4A5A62;
    --accent: #2C6E8E;
    --up: #1F9D5C;
    --down: #D6334C;
}

.stApp {
    background-color: var(--bg);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

.stApp, .stApp p, .stApp span, .stApp label, .stApp div {
    color: var(--text);
}

/* タイトル */
h1 {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    color: var(--text) !important;
    border-bottom: 1px solid var(--line);
    padding-bottom: 0.6em;
}

h2, h3, h4 {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text) !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em;
}

/* サブヘッダー：等幅フォントでラベル風に */
.stMarkdown h3 {
    font-size: 0.95rem !important;
    text-transform: uppercase;
    color: var(--text-dim) !important;
    border-left: 2px solid var(--accent);
    padding-left: 0.6em;
    margin-top: 1.4em !important;
}

/* metric カード */
div[data-testid="stMetric"] {
    background-color: var(--bg-panel);
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 0.9rem 1rem;
}

div[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim) !important;
}

div[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    color: var(--text) !important;
}

/* タブ */
button[data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    color: var(--text-dim) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

div[data-baseweb="tab-border"] {
    background-color: var(--line) !important;
}

div[data-baseweb="tab-highlight"] {
    background-color: var(--accent) !important;
}

/* 区切り線 */
hr {
    border-color: var(--line) !important;
}

/* サイドバー */
section[data-testid="stSidebar"] {
    background-color: var(--bg-panel);
    border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] h3 {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    color: var(--text-dim) !important;
    letter-spacing: 0.05em;
}

/* サイドバー内のテキスト入力の文字色を白に */
section[data-testid="stSidebar"] div[data-baseweb="input"] {
    background-color: #2C6E8E !important;
    border-color: #2C6E8E !important;
}

section[data-testid="stSidebar"] div[data-baseweb="input"] input {
    color: #FFFFFF !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* サイドバー内のラベル文字色 */
section[data-testid="stSidebar"] label {
    color: var(--text) !important;
}

/* テキスト入力 */
div[data-baseweb="input"] {
    border-radius: 2px !important;
    border-color: var(--line) !important;
    background-color: var(--bg) !important;
}

div[data-baseweb="input"] input {
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text) !important;
}

/* ボタン */
.stButton button {
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 2px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 0.8rem !important;
}

/* caption */
.stCaption, [data-testid="stCaptionContainer"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text-dim) !important;
}

/* warning / success バナー */
div[data-testid="stAlert"] {
    border-radius: 2px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

st.title("◆ TOPIX / 日経225 ダッシュボード")

# --- サイドバー：手動入力 ---
with st.sidebar:
    st.header("📝 手動更新")

    st.subheader("NT倍率の判定レンジ")
    nt_ratio_low = st.text_input("NT倍率 下限", value=get_secret("NT_RATIO_LOW"), key="nt_ratio_low")
    nt_ratio_high = st.text_input("NT倍率 上限", value=get_secret("NT_RATIO_HIGH"), key="nt_ratio_high")

    st.divider()

    st.subheader("TOPIX EPS")
    topix_eps_prev = st.text_input("前期EPS", value=get_secret("TOPIX_EPS_PREV"), key="topix_eps_prev")
    topix_eps_curr = st.text_input("今期EPS", value=get_secret("TOPIX_EPS_CURR"), key="topix_eps_curr")
    topix_eps_next = st.text_input("来期EPS", value=get_secret("TOPIX_EPS_NEXT"), key="topix_eps_next")

    st.subheader("TOPIX PERの判定レンジ")
    topix_per_low = st.text_input("PER 下限", value=get_secret("TOPIX_PER_LOW"), key="topix_per_low")
    topix_per_high = st.text_input("PER 上限", value=get_secret("TOPIX_PER_HIGH"), key="topix_per_high")

    st.divider()

    topix_prev_close = st.text_input(
        "TOPIX 前日終値（毎営業日更新）",
        value=get_secret("TOPIX_PREV_CLOSE"),
        key="topix_prev_close",
        help="毎営業日、JPX公式サイト等でTOPIXの終値を確認しここに入力してください。ETF逆算の基準値として使われます。"
    )

    if st.button("保存", type="primary"):
        if IS_LOCAL:
            set_key(ENV_PATH, "NT_RATIO_LOW", nt_ratio_low)
            set_key(ENV_PATH, "NT_RATIO_HIGH", nt_ratio_high)
            set_key(ENV_PATH, "TOPIX_EPS_PREV", topix_eps_prev)
            set_key(ENV_PATH, "TOPIX_EPS_CURR", topix_eps_curr)
            set_key(ENV_PATH, "TOPIX_EPS_NEXT", topix_eps_next)
            set_key(ENV_PATH, "TOPIX_PER_LOW", topix_per_low)
            set_key(ENV_PATH, "TOPIX_PER_HIGH", topix_per_high)
            set_key(ENV_PATH, "TOPIX_PREV_CLOSE", topix_prev_close)
            load_dotenv(override=True)
            st.success("保存しました（ローカル）")
        else:
            st.warning("クラウドではStreamlit SecretsをWebから更新してください")

# --- PERを計算 ---
def calc_per(price, eps):
    try:
        price = float(price)
        eps = float(eps)
        if eps == 0:
            return None
        return price / eps
    except (ValueError, TypeError):
        return None

# --- レンジ判定（下限未満=割安、上限超え=割高、範囲内=標準） ---
def judge_range(value, low, high):
    if value is None:
        return "－", "#4A5A62"
    try:
        low = float(low)
        high = float(high)
    except (ValueError, TypeError):
        return "－", "#4A5A62"
    if value < low:
        return "割安", "#1F9D5C"
    elif value > high:
        return "割高", "#D6334C"
    else:
        return "標準", "#2C6E8E"

# --- yfinanceで日経225価格取得 ---
@st.cache_data(ttl=60)
def get_nikkei_price():
    nikkei = yf.Ticker("^N225")
    price = nikkei.fast_info.get("lastPrice") or nikkei.fast_info.get("regularMarketPrice")
    return price

# --- ETF(1306)キャリブレーション方式でTOPIXを推定 ---
@st.cache_data(ttl=60)
def get_topix_estimated(topix_prev_close_str):
    """
    TOPIX連動ETF(1306)の値動きを使い、前営業日のTOPIX公式終値を基準に
    リアルタイムTOPIXを推定する（キャリブレーション方式）。

    手順:
    1. 前営業日終値時点の比率を計算: ratio = TOPIX前日終値 / ETF前日終値
    2. リアルタイムのETF価格にratioを掛けて推定: TOPIX_estimate = ETF_price(t) × ratio
    """
    try:
        topix_prev_close = float(topix_prev_close_str)
    except (ValueError, TypeError):
        return None, None, "TOPIX前日終値が未設定です（サイドバーから入力してください）"

    try:
        etf = yf.Ticker("1306.T")
        etf_info = etf.fast_info

        etf_current = etf_info.get("lastPrice") or etf_info.get("regularMarketPrice")
        etf_prev_close = etf_info.get("previousClose") or etf_info.get("regular_market_previous_close")

        if not etf_current or not etf_prev_close:
            return None, None, "ETF(1306)の価格取得に失敗しました"

        ratio = topix_prev_close / etf_prev_close
        estimated_topix = etf_current * ratio
        change_ratio = (etf_current - etf_prev_close) / etf_prev_close

        return estimated_topix, change_ratio, None
    except Exception as e:
        return None, None, f"取得エラー: {e}"

# --- J-Quants V2で個別銘柄財務情報取得 ---
@st.cache_data(ttl=3600)
def get_fin_summary(code):
    headers = {"x-api-key": API_KEY}
    res = requests.get(
        f"{BASE_URL}/fins/summary",
        headers=headers,
        params={"code": code}
    )
    if res.status_code != 200:
        return None, f"J-Quants エラー: {res.status_code} / {res.text}"
    records = res.json().get("data", [])
    fy_records = [r for r in records if r.get("CurPerType") == "FY"]
    if not fy_records:
        return None, "対象銘柄の決算データが見つかりませんでした"
    latest = fy_records[-1]
    return {
        "開示日": latest.get("DiscDate"),
        "当期終了": latest.get("CurPerEn"),
        "前期EPS": latest.get("EPS"),
        "今期予想EPS": latest.get("FEPS"),
        "来期予想EPS": latest.get("NxFEPS"),
        "前期配当（実績・年間）": latest.get("DivAnn"),
        "今期配当予想（年間）": latest.get("FDivAnn"),
    }, None

# --- J-Quants V2で銘柄名取得 ---
@st.cache_data(ttl=86400)
def get_company_name(code):
    headers = {"x-api-key": API_KEY}
    res = requests.get(
        f"{BASE_URL}/equities/master",
        headers=headers,
        params={"code": code}
    )
    if res.status_code != 200:
        return None
    data = res.json()
    records = data.get("data") or data.get("info") or []
    if not records:
        return None
    return records[0].get("CoName")

# --- yfinanceで個別銘柄の価格・前日比・時価総額取得 ---
@st.cache_data(ttl=60)
def get_stock_price_info(code):
    """
    J-Quantsの証券コード（4桁+0、例: 72030）はyfinanceでは
    "7203.T" のような4桁+.T形式のため、末尾の0を除いて変換する。
    """
    yf_code = code[:-1] if len(code) == 5 and code.endswith("0") else code
    ticker = f"{yf_code}.T"
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        price = info.get("lastPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        market_cap = info.get("marketCap")
        if not price:
            return None, f"{ticker} の価格を取得できませんでした"
        change = None
        change_pct = None
        if prev_close:
            change = price - prev_close
            change_pct = (change / prev_close) * 100
        return {
            "ticker": ticker,
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "market_cap": market_cap,
        }, None
    except Exception as e:
        return None, f"取得エラー: {e}"

# --- 配当利回りを計算 ---
def calc_dividend_yield(price, dividend):
    try:
        price = float(price)
        dividend = float(dividend)
        if price == 0:
            return None
        return (dividend / price) * 100
    except (ValueError, TypeError):
        return None

# --- 価格取得 ---
n_price = get_nikkei_price()
t_price, t_change_ratio, t_error = get_topix_estimated(topix_prev_close)

# --- NT倍率を計算 ---
def calc_nt_ratio(nikkei_price, topix_price):
    try:
        if not nikkei_price or not topix_price:
            return None
        return nikkei_price / topix_price
    except (TypeError, ZeroDivisionError):
        return None

nt_ratio = calc_nt_ratio(n_price, t_price)

# --- タブ：指数 / 個別銘柄 ---
tab1, tab2 = st.tabs(["INDEX", "EQUITIES"])

with tab1:
    st.subheader("PRICE — 指数価格")
    c1, c2 = st.columns(2)

    with c1:
        if t_price:
            st.metric(
                "TOPIX（推定値）",
                f"{t_price:,.2f}",
                delta=f"{t_change_ratio * 100:+.2f}%" if t_change_ratio is not None else None,
            )
            st.caption("※ ETF(1306)のキャリブレーション方式による推定値です。")
        else:
            st.metric("TOPIX", "取得失敗")
            if t_error:
                st.caption(f"⚠️ {t_error}")

    with c2:
        st.metric("日経225", f"{n_price:,.2f}" if n_price else "取得失敗")

    st.divider()

    st.subheader("RATIO — NT倍率（日経225 ÷ TOPIX）")
    if nt_ratio is not None:
        judge, color = judge_range(nt_ratio, nt_ratio_low, nt_ratio_high)
        c1, c2 = st.columns([1, 2])
        with c1:
            st.metric("NT倍率", f"{nt_ratio:.2f}")
            st.markdown(
                f"判定: <span style='color:{color}; font-weight:bold;'>{judge}</span>",
                unsafe_allow_html=True,
            )
        with c2:
            st.caption(f"判定レンジ: {nt_ratio_low} 〜 {nt_ratio_high}")
            st.caption("下限未満＝割安、上限超え＝割高、範囲内＝標準")
    else:
        st.warning("日経225またはTOPIXの価格が取得できていないため、NT倍率を計算できません。")

    st.divider()

    st.subheader("VALUATION — TOPIX PER（前期・今期・来期EPS基準）")
    if t_price is not None:
        cols = st.columns(3)
        labels = ["前期PER", "今期PER", "来期PER"]
        eps_values = [topix_eps_prev, topix_eps_curr, topix_eps_next]
        eps_labels = ["前期EPS", "今期EPS", "来期EPS"]

        for col, label, eps_label, eps_val in zip(cols, labels, eps_labels, eps_values):
            per = calc_per(t_price, eps_val)
            judge, color = judge_range(per, topix_per_low, topix_per_high)
            with col:
                st.metric(label, f"{per:.2f}倍" if per is not None else "－")
                st.caption(f"{eps_label}: {eps_val}")
                st.markdown(
                    f"判定: <span style='color:{color}; font-weight:bold;'>{judge}</span>",
                    unsafe_allow_html=True,
                )

        st.caption(f"判定レンジ: {topix_per_low}倍 〜 {topix_per_high}倍（下限未満＝割安、上限超え＝割高）")
    else:
        st.warning("TOPIXの価格が取得できていないため、PERを計算できません。")

with tab2:
    st.subheader("EQUITIES — 個別銘柄（3銘柄まで比較表示）")

    code_cols = st.columns(3)
    stock_codes = []
    default_codes = ["7203", "", ""]
    for i, col in enumerate(code_cols):
        with col:
            code = st.text_input(
                f"銘柄コード（4桁）",
                value=default_codes[i],
                max_chars=4,
                key=f"stock_code_{i}",
                help="例: トヨタ自動車 = 7203"
            )
            stock_codes.append(code)

    st.divider()

    def render_stock_column(stock_code):
        if not (stock_code and len(stock_code) == 4 and stock_code.isdigit()):
            if stock_code:
                st.warning("4桁の数字で入力してください")
            return

        jquants_code = stock_code + "0"  # J-Quantsは5桁コード（末尾0）

        company_name = get_company_name(jquants_code)
        price_info, price_error = get_stock_price_info(jquants_code)
        fin_info, fin_error = get_fin_summary(jquants_code)

        if company_name:
            st.markdown(f"### {company_name}（{stock_code}）")
        else:
            st.markdown(f"### {stock_code}")
            st.caption("※ 銘柄名を取得できませんでした")

        # --- 価格・前日比・時価総額 ---
        st.markdown("##### PRICE")
        if price_info:
            st.metric(
                "株価",
                f"{price_info['price']:,.1f}円",
                delta=f"{price_info['change']:+.1f}円 ({price_info['change_pct']:+.2f}%)" if price_info['change'] is not None else None,
            )
            st.metric(
                "時価総額",
                f"{price_info['market_cap'] / 1e8:,.0f}億円" if price_info['market_cap'] else "－"
            )
            st.caption(f"ティッカー: {price_info['ticker']}")
        else:
            st.warning(price_error or "価格情報を取得できませんでした")

        st.markdown("##### VALUATION")
        if fin_info and price_info:
            labels = ["前期PER", "今期PER", "来期PER"]
            eps_keys = ["前期EPS", "今期予想EPS", "来期予想EPS"]

            for label, eps_key in zip(labels, eps_keys):
                eps_val = fin_info.get(eps_key)
                per = calc_per(price_info["price"], eps_val)
                st.metric(label, f"{per:.2f}倍" if per is not None else "－")
                st.caption(f"{eps_key}: {eps_val if eps_val is not None else '未開示'}")

            st.caption(f"開示日: {fin_info['開示日']} / 期末: {fin_info['当期終了']}")
        elif fin_error:
            st.warning(fin_error)
        else:
            st.warning("EPSまたは価格情報が取得できません")

        st.markdown("##### DIVIDEND YIELD")
        if fin_info and price_info:
            div_prev = fin_info.get("前期配当（実績・年間）")
            div_curr = fin_info.get("今期配当予想（年間）")

            yield_prev = calc_dividend_yield(price_info["price"], div_prev)
            yield_curr = calc_dividend_yield(price_info["price"], div_curr)

            st.metric(
                "配当利回り（前期実績）",
                f"{yield_prev:.2f}%" if yield_prev is not None else "－"
            )
            st.caption(f"前期配当: {div_prev if div_prev is not None else '未開示'}円")

            st.metric(
                "配当利回り（今期予想）",
                f"{yield_curr:.2f}%" if yield_curr is not None else "－"
            )
            st.caption(f"今期配当予想: {div_curr if div_curr is not None else '未開示'}円")
        else:
            st.warning("配当情報が取得できませんでした")

        st.caption("※ 自社株買いは無料データソースでは取得不可のため未対応")

    result_cols = st.columns(3)
    for col, code in zip(result_cols, stock_codes):
        with col:
            render_stock_column(code)
