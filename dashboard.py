"""
股票儀表板
本地執行: streamlit run dashboard.py
雲端部署: Streamlit Community Cloud (share.streamlit.io)
"""

import streamlit as st
import yfinance as yf
from datetime import datetime, timezone, timedelta
import requests
import time
import json
import hashlib
from pathlib import Path

TW_TZ = timezone(timedelta(hours=8))   # 台灣時區 UTC+8

def now_tw() -> datetime:
    return datetime.now(TW_TZ)

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="股票儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px !important;
}
.stApp {
    background: linear-gradient(160deg, #eef2ff 0%, #f0f9ff 55%, #f0fdf4 100%) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #1e3a5f 0%, #0f2240 100%) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] label { color: #93b4d4 !important; }
section[data-testid="stSidebar"] h3 { color: #dbeafe !important; font-size: 1rem !important; }
section[data-testid="stSidebar"] strong { color: #bfdbfe !important; }
section[data-testid="stSidebar"] hr { border-color: #2a4a72 !important; }
section[data-testid="stSidebar"] .stTextInput input {
    background: #162d4a !important; border: 1px solid #2a4a72 !important;
    color: #dbeafe !important; border-radius: 8px !important;
}
section[data-testid="stSidebar"] .stTextInput input::placeholder { color: #4a7aa0 !important; }

.app-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 100%);
    border-radius: 16px; padding: 18px 28px; margin-bottom: 20px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 20px rgba(30,58,95,0.18);
}
.app-title { font-size: 1.55rem; font-weight: 900; color: #ffffff; letter-spacing: -0.3px; }
.app-subtitle { font-size: 0.78rem; color: #93c5fd; margin-top: 2px; }
.app-time { font-size: 0.8rem; color: #93c5fd; text-align: right; line-height: 1.6; }

.section-hdr {
    display: flex; align-items: center; gap: 10px;
    font-size: 1.15rem; font-weight: 700; color: #1e40af;
    text-transform: uppercase; letter-spacing: 0.8px;
    padding: 11px 18px;
    background: linear-gradient(90deg, rgba(37,99,235,0.08) 0%, transparent 70%);
    border-left: 4px solid #2563eb; border-radius: 0 10px 10px 0; margin-bottom: 16px;
}

/* Indicator cards */
.ind-card {
    background: #ffffff; border-radius: 14px; padding: 14px 16px 12px;
    min-height: 118px; display: flex; flex-direction: column; justify-content: space-between;
    box-shadow: 0 2px 16px rgba(30,58,95,0.07), 0 1px 3px rgba(0,0,0,0.04);
    border-top: 4px solid #cbd5e1;
    transition: box-shadow 0.2s, transform 0.2s; position: relative;
}
.ind-card:hover { box-shadow: 0 6px 28px rgba(30,58,95,0.13); transform: translateY(-1px); }
.ind-label { font-size: 0.87rem; color: #64748b; font-weight: 700;
             text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.4; }
.ind-value { font-size: 1.78rem; font-weight: 900; color: #0f172a;
             line-height: 1; letter-spacing: -0.5px; margin: 4px 0; }
.ind-up   { font-size: 1.02rem; color: #dc2626; font-weight: 700; }
.ind-down { font-size: 1.02rem; color: #059669; font-weight: 700; }
.ind-neu  { font-size: 1.02rem; color: #94a3b8; }
.ind-note { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
.ind-src  { font-size: 0.74rem; color: #cbd5e1; margin-top: 2px; text-align: right; }

/* Watchlist */
.wl-wrap {
    overflow-x: auto; border-radius: 16px; border: 1px solid #dde4f0;
    background: #ffffff; box-shadow: 0 4px 28px rgba(30,58,95,0.08);
}
.wl-table { width: 100%; border-collapse: collapse; font-size: 1.04rem; }
.wl-table thead th {
    background: linear-gradient(180deg, #f1f5fd 0%, #e8eef8 100%);
    color: #475569; font-weight: 700; font-size: 0.88rem;
    text-transform: uppercase; letter-spacing: 0.5px;
    padding: 13px 14px; text-align: right; white-space: nowrap;
    border-bottom: 2px solid #dde4f0;
}
.wl-table thead th.left { text-align: left; }
.wl-table tbody tr { border-bottom: 1px solid #f1f5f9; transition: background 0.12s; }
.wl-table tbody tr:last-child { border-bottom: none; }
.wl-table tbody tr:nth-child(even) { background: #fafbff; }
.wl-table tbody tr:hover { background: #eff6ff !important; }
.wl-table tbody td { padding: 12px 14px; vertical-align: middle; text-align: right; }
.wl-table tbody td.left { text-align: left; }

.stk-code { font-weight: 900; color: #1d4ed8; font-size: 1.18rem; }
.stk-name { font-size: 0.94rem; color: #94a3b8; margin-top: 2px; }
.stk-ind  { font-size: 0.85rem; color: #93c5fd; margin-top: 1px;
            background: rgba(37,99,235,0.07); padding: 1px 5px; border-radius: 4px; display: inline-block; }

.price   { font-weight: 800; font-size: 1.24rem; color: #0f172a; }
.chg-sub { font-size: 0.95rem; margin-top: 2px; }
.up      { color: #dc2626; font-weight: 700; }
.down    { color: #059669; font-weight: 700; }
.neutral { color: #94a3b8; }

/* P/E column */
.pe-val  { font-weight: 800; font-size: 1.2rem; }
.pe-ok   { color: #059669; }
.pe-mid  { color: #d97706; }
.pe-high { color: #dc2626; }
.pe-assess {
    display: inline-flex; align-items: center; gap: 3px;
    font-size: 0.88rem; font-weight: 700; padding: 2px 9px;
    border-radius: 10px; margin-top: 3px; white-space: nowrap;
}
.pe-a-low  { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.pe-a-mid  { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
.pe-a-high { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
.pe-ind-avg { font-size: 0.86rem; color: #94a3b8; margin-top: 2px; }

/* Position badges */
.badge-low  {
    background: linear-gradient(135deg,#d1fae5,#a7f3d0); color: #064e3b;
    border: 1px solid #6ee7b7; padding: 4px 13px; border-radius: 20px;
    font-size: 0.92rem; font-weight: 700; white-space: nowrap;
}
.badge-mid  {
    background: linear-gradient(135deg,#fef3c7,#fde68a); color: #78350f;
    border: 1px solid #fcd34d; padding: 4px 13px; border-radius: 20px;
    font-size: 0.92rem; font-weight: 700; white-space: nowrap;
}
.badge-high {
    background: linear-gradient(135deg,#fee2e2,#fecaca); color: #7f1d1d;
    border: 1px solid #fca5a5; padding: 4px 13px; border-radius: 20px;
    font-size: 0.92rem; font-weight: 700; white-space: nowrap;
}
.pos-bar  { display:inline-block; width:52px; height:5px;
            background:#e2e8f0; border-radius:3px; vertical-align:middle; }
.pos-fill { height:100%; border-radius:3px; }

/* Target price */
.target-val { font-weight: 800; color: #0f172a; }
.up-pct { color: #dc2626; font-weight: 700; font-size: 1.06rem; }
.dn-pct { color: #059669; font-weight: 700; font-size: 1.06rem; }
.ana-cnt { font-size: 0.9rem; color: #94a3b8; font-weight: 400; }
.date-txt { font-size: 0.94rem; color: #94a3b8; }
.date-fresh { font-size: 0.92rem; color: #059669; font-weight: 600; }
.date-old   { font-size: 0.92rem; color: #d97706; font-weight: 600; }

.na-txt { color: #cbd5e1; }
.src-tag { font-size: 0.78rem; color: #cbd5e1; }

.footer-note {
    margin-top: 16px; padding: 10px 16px;
    background: rgba(37,99,235,0.04); border-radius: 10px;
    border: 1px solid #dde4f0;
    font-size: 0.69rem; color: #94a3b8; line-height: 1.9; text-align: right;
}

/* ─ 台股 / 美股 Expander ─ */
div[data-testid="stExpander"] {
    border-radius: 14px !important;
    border: 1px solid #dde4f0 !important;
    box-shadow: 0 2px 12px rgba(30,58,95,0.06);
    background: #fff !important;
    margin-bottom: 14px !important;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    padding: 13px 20px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: #1e40af !important;
    background: linear-gradient(90deg, #eef2ff 0%, #f8fbff 100%) !important;
    border-bottom: 1px solid #dde4f0;
    list-style: none;
}
div[data-testid="stExpander"] summary:hover {
    background: linear-gradient(90deg, #e0e7ff 0%, #eff6ff 100%) !important;
}
div[data-testid="stExpanderDetails"] {
    padding: 0 !important;
}
/* 說明欄用另一樣式 */
div[data-testid="stExpander"].explain-box summary {
    background: #f8fafc !important;
    color: #475569 !important;
}
</style>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# ── 產業本益比基準表 ─────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
# 台股：(產業名稱, PE低檔, PE高檔)  → 低於低檔=低估, 高於高檔=偏高
TW_STOCK_PE = {
    # 晶圓代工 / 半導體製造
    "2330": ("半導體製造", 16, 26), "2303": ("半導體製造", 12, 22),
    "6770": ("半導體製造", 10, 18),
    # IC 設計
    "2454": ("IC設計", 18, 32), "3034": ("IC設計", 16, 28),
    "2379": ("IC設計", 14, 26), "3661": ("IC設計", 20, 40),
    "6415": ("IC設計", 20, 38),
    # 封測
    "3711": ("封測", 10, 20), "2449": ("封測", 8, 16),
    # PCB / 基板
    "3037": ("PCB", 10, 20), "8046": ("PCB", 10, 20), "4958": ("PCB", 10, 20),
    # 伺服器 / AI 供應鏈
    "2382": ("伺服器/EMS", 8, 18), "6669": ("伺服器/EMS", 10, 22),
    "3231": ("伺服器/EMS", 8, 18), "2356": ("伺服器/EMS", 8, 16),
    # 電子代工
    "2317": ("電子代工", 8, 16), "4938": ("電子代工", 8, 16),
    "2324": ("電子代工", 6, 14),
    # 電源 / 零組件
    "2308": ("電源零組件", 12, 22), "2395": ("工業電腦", 16, 28),
    # 消費電子
    "2357": ("消費電子", 10, 20), "2353": ("消費電子", 8, 18),
    "3008": ("光學元件", 18, 35),
    # 金融
    "2881": ("金融", 8, 14), "2882": ("金融", 8, 14),
    "2884": ("金融", 8, 14), "2886": ("金融", 7, 13),
    "2891": ("金融", 8, 14), "2885": ("金融", 8, 14),
    # 電信
    "2412": ("電信", 18, 28), "4904": ("電信", 16, 26),
    "3045": ("電信", 16, 26),
    # 航運
    "2603": ("航運", 5, 15), "2609": ("航運", 5, 15),
    "2615": ("航運", 5, 15),
    # 鋼鐵 / 原料
    "2002": ("鋼鐵", 8, 18),
    # 石化
    "1301": ("石化", 8, 18), "1303": ("石化", 8, 18),
    # 食品 / 零售
    "2912": ("零售", 20, 35), "1216": ("食品", 18, 30),
    # ETF
    "0050": ("ETF", 0, 0), "0056": ("ETF", 0, 0),
    "00878": ("ETF", 0, 0), "00919": ("ETF", 0, 0),
}

# 美股：按 sector
US_SECTOR_PE = {
    "Technology":             ("科技",        22, 38),
    "Financial Services":     ("金融服務",     9,  18),
    "Healthcare":             ("醫療",         18, 32),
    "Consumer Cyclical":      ("非必需消費",   14, 28),
    "Consumer Defensive":     ("必需消費",     18, 28),
    "Communication Services": ("通訊服務",     16, 30),
    "Energy":                 ("能源",          8, 18),
    "Utilities":              ("公用事業",     14, 22),
    "Real Estate":            ("房地產",       18, 35),
    "Basic Materials":        ("原物料",       10, 20),
    "Industrials":            ("工業",         16, 26),
    "Semiconductor":          ("半導體",       20, 40),
}

def pe_assessment(pe, symbol, sector):
    """
    Returns (label, color_cls, ind_name, ind_low, ind_high) or None tuple
    label: '低估'/'合理'/'偏高'/'ETF'
    """
    if pe is None:
        return None, None, None, None, None

    # Taiwan stock lookup
    tw = TW_STOCK_PE.get(symbol)
    if tw:
        ind_name, lo, hi = tw
        if ind_name == "ETF":
            return "ETF", "pe-a-mid", "ETF", 0, 0
        if pe < lo:
            return "低估", "pe-a-low", ind_name, lo, hi
        elif pe > hi:
            return "偏高", "pe-a-high", ind_name, lo, hi
        else:
            return "合理", "pe-a-mid", ind_name, lo, hi

    # US sector lookup
    if sector and sector in US_SECTOR_PE:
        ind_name, lo, hi = US_SECTOR_PE[sector]
        if pe < lo:
            return "低估", "pe-a-low", ind_name, lo, hi
        elif pe > hi:
            return "偏高", "pe-a-high", ind_name, lo, hi
        else:
            return "合理", "pe-a-mid", ind_name, lo, hi

    # Fallback — general market average ~20x
    if pe < 12:
        return "偏低", "pe-a-low", "市場", 12, 25
    elif pe > 30:
        return "偏高", "pe-a-high", "市場", 12, 25
    else:
        return "合理", "pe-a-mid", "市場", 12, 25

# ════════════════════════════════════════════════════════════════
# ── 台股中文名稱表 ────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
TW_NAMES = {
    "2330": "台積電", "2317": "鴻海",   "2454": "聯發科", "2382": "廣達",
    "2308": "台達電", "2303": "聯電",   "2881": "富邦金", "2882": "國泰金",
    "2884": "玉山金", "2886": "兆豐金", "2891": "中信金", "2412": "中華電",
    "2357": "華碩",   "2353": "宏碁",   "2379": "瑞昱",   "3034": "聯詠",
    "3711": "日月光", "2409": "友達",   "3481": "群創",   "2002": "中鋼",
    "2603": "長榮",   "2609": "陽明",   "2615": "萬海",   "6669": "緯穎",
    "3231": "緯創",   "2395": "研華",   "3037": "欣興",   "2327": "國巨",
    "3008": "大立光", "2912": "統一超", "6415": "矽力-KY","3661": "世芯",
    "0050": "台灣50", "0056": "元大高息","00878":"國泰永息","00919":"群益高息",
    "2885": "元大金", "2356": "英業達", "4938": "和碩",   "4958": "臻鼎",   "1301": "台塑",
    "1303": "南亞",   "1216": "統一",   "4904": "遠傳",   "3045": "台灣大",
    # 補充常見股票
    "2344": "華邦電", "3017": "奇鋐",   "2383": "台光電", "6274": "台燿",
    "7769": "鴻勁",   "3016": "嘉晶",   "6533": "晶心科", "2337": "旺宏",
    "3443": "創意",   "5274": "信驊",   "6510": "精測",   "2049": "上銀",
    "1590": "亞德客", "2308": "台達電", "2327": "國巨",   "3563": "牧德",
}

# ════════════════════════════════════════════════════════════════
# ── 全球指標定義 ──────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
INDICATORS = [
    {"label": "USD/JPY\n日幣匯率",   "symbol": "USDJPY=X",  "dec": 2, "src": "Yahoo Finance"},
    {"label": "美債10年期利率",       "symbol": "^TNX",      "dec": 3, "suffix": "%", "src": "Yahoo Finance"},
    {"label": "台指期\n(現貨代理)",   "symbol": "^TWII",     "dec": 0, "src": "Yahoo Finance",
     "note": "※夜盤需TAIFEX"},
    {"label": "S&P 500",              "symbol": "^GSPC",     "dec": 1, "src": "Yahoo Finance"},
    {"label": "NASDAQ",               "symbol": "^IXIC",     "dec": 1, "src": "Yahoo Finance"},
    {"label": "費城半導體",            "symbol": "^SOX",      "dec": 0, "src": "Yahoo Finance"},
    {"label": "美元指數 DXY",         "symbol": "DX-Y.NYB",  "dec": 2, "src": "Yahoo Finance"},
    {"label": "VIX 恐慌指數",         "symbol": "^VIX",      "dec": 2, "src": "Yahoo Finance"},
    {"label": "黃金",                 "symbol": "GC=F",      "dec": 1, "suffix": " USD", "src": "Yahoo Finance"},
    {"label": "WTI 原油",             "symbol": "CL=F",      "dec": 2, "suffix": " USD", "src": "Yahoo Finance"},
    {"label": "比特幣",               "symbol": "BTC-USD",   "dec": 0, "suffix": " USD", "src": "Yahoo Finance"},
]

DEFAULT_TW = ["2330", "2317", "2454", "2382"]
DEFAULT_US = ["NVDA", "AAPL"]

import re as _re

def is_tw_stock(code: str) -> bool:
    return bool(_re.match(r"^\d{4,6}$", code))

# ════════════════════════════════════════════════════════════════
# ── 跨裝置同步：Server-side profile（/tmp 共享）─────────────────────
# ════════════════════════════════════════════════════════════════
_PROFILE_DIR = Path("/tmp/stock_profiles")

def _profile_path(key: str) -> Path:
    safe = hashlib.sha256(key.encode()).hexdigest()[:20]
    return _PROFILE_DIR / f"{safe}.json"

def load_profile(key: str):
    """讀取 profile 檔案。回傳 (tw, us, timestamp_str) 或 (None, None, None)。"""
    try:
        _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        p = _profile_path(key)
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            return d.get("tw", []), d.get("us", []), d.get("ts", "")
    except Exception:
        pass
    return None, None, None

def save_profile(key: str, tw: list, us: list):
    """寫入 profile 檔案，同時附上更新時間。"""
    try:
        _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        _profile_path(key).write_text(
            json.dumps({"tw": tw, "us": us,
                        "ts": now_tw().strftime("%m/%d %H:%M")},
                       ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception:
        pass

# ── Watchlist: URL query params（tw= 台股，us= 美股）+ profile sync ──
def load_watchlists():
    """讀取清單：優先用 profile 檔案（若有 key），其次 URL params。"""
    old_w  = st.query_params.get("w",  "")
    tw_raw = st.query_params.get("tw", "")
    us_raw = st.query_params.get("us", "")
    key    = st.query_params.get("key", "").strip()

    if old_w and not tw_raw and not us_raw:
        stocks = [s.strip().upper() for s in old_w.split(",") if s.strip()]
        tw = [s for s in stocks if is_tw_stock(s)]
        us = [s for s in stocks if not is_tw_stock(s)]
        tw = tw or list(DEFAULT_TW); us = us or list(DEFAULT_US)
    else:
        tw = [s.strip().upper() for s in tw_raw.split(",") if s.strip()] if tw_raw else list(DEFAULT_TW)
        us = [s.strip().upper() for s in us_raw.split(",") if s.strip()] if us_raw else list(DEFAULT_US)

    if key:
        tw_p, us_p, _ = load_profile(key)
        if tw_p is not None:
            tw, us = tw_p, us_p   # profile 覆蓋 URL params

    return tw, us, key

def save_tw(wl: list[str]):
    st.query_params["tw"] = ",".join(wl)
    if k := st.session_state.get("profile_key", ""):
        save_profile(k, wl, st.session_state.get("us_list", []))

def save_us(wl: list[str]):
    st.query_params["us"] = ",".join(wl)
    if k := st.session_state.get("profile_key", ""):
        save_profile(k, st.session_state.get("tw_list", []), wl)

# ════════════════════════════════════════════════════════════════
# ── 資料抓取 ──────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════
# ── Yahoo Finance 防限流：HTTP 層快取 + 瀏覽器 Headers ────────────────
# ════════════════════════════════════════════════════════════════
@st.cache_resource
def _http_session() -> requests.Session:
    """
    建立瀏覽器模擬 Session（跨所有使用者共用，app 重啟前持續有效）。
    注意：yfinance 新版不支援 requests_cache，改用純 requests.Session。
    """
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    })
    return s


def _safe_float(val):
    """安全轉 float，NaN / None 回傳 None"""
    try:
        import math
        v = float(val)
        return None if math.isnan(v) else v
    except Exception:
        return None


def _fetch_one(symbol: str) -> dict:
    """
    取得單支股票資料（不快取，由 fetch_stocks_batch 統一管理）。
    - Step1 fast_info：價格 + 52 週高低（使用 year_high / year_low）
    - Step2 info：本益比 / 法人目標價（最多重試 3 次，每次間隔 2s）
    - Step3 upgrades_downgrades：最新評估日（最多重試 2 次）
    各步驟獨立失敗，不影響其他欄位。
    """
    import re
    is_tw  = bool(re.match(r"^\d{4,6}$", symbol))

    # ── Step 1: 價格 + 52週高低（自動嘗試 .TW → .TWO）──────────────
    # 台灣股票分兩市：上市(.TW) / 上櫃(.TWO)，先試 .TW，失敗改 .TWO
    price = prev = chg = pct = low52 = high52 = pos = None
    yf_sym = symbol + ".TW" if is_tw else symbol   # 預設

    def _try_price(sym: str):
        nonlocal price, prev, chg, pct, low52, high52, pos
        try:
            fi = yf.Ticker(sym, session=_http_session()).fast_info
            price  = _safe_float(fi.last_price)
            if not price:
                return False
            prev   = _safe_float(fi.previous_close) or price
            chg    = (price - prev) if price and prev else None
            pct    = chg / prev * 100 if chg and prev else None
            low52  = _safe_float(getattr(fi, "year_low",  None))
            high52 = _safe_float(getattr(fi, "year_high", None))
            if price and low52 and high52 and high52 > low52:
                pos = (price - low52) / (high52 - low52) * 100
            return True
        except Exception:
            return False

    def _try_price_dl(sym: str):
        """備援：yf.download()，同時取 52 週高低"""
        nonlocal price, prev, chg, pct, low52, high52, pos
        try:
            hist = yf.download(sym, period="1y", progress=False,
                               auto_adjust=True, multi_level_index=False)
            if hist.empty:
                return False
            price  = _safe_float(hist["Close"].iloc[-1])
            if not price:
                return False
            prev   = _safe_float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            chg    = (price - prev) if price and prev else None
            pct    = chg / prev * 100 if chg and prev else None
            low52  = _safe_float(hist["Low"].min())
            high52 = _safe_float(hist["High"].max())
            if price and low52 and high52 and high52 > low52:
                pos = (price - low52) / (high52 - low52) * 100
            return True
        except Exception:
            return False

    if is_tw:
        # 嘗試順序：.TW fast_info → .TW download → .TWO fast_info → .TWO download
        if not _try_price(symbol + ".TW"):
            if not _try_price_dl(symbol + ".TW"):
                if _try_price(symbol + ".TWO") or _try_price_dl(symbol + ".TWO"):
                    yf_sym = symbol + ".TWO"   # 上櫃股票，後續 info 也用此 symbol
    else:
        if not _try_price(symbol):
            _try_price_dl(symbol)

    if price is None:
        return {"ok": False, "symbol": symbol, "error": "無法取得股價"}

    time.sleep(1.2)

    # ── Step 2+3: fundamentals（獨立 2 小時快取，與價格快取分開）────
    # 每次 retry 建新 Ticker，避免 yfinance 內部快取舊的失敗結果
    fund = fetch_fundamentals(yf_sym, symbol)

    # ── 整合結果 ──────────────────────────────────────────────────────
    pe       = fund.get("pe")
    sector   = fund.get("sector", "")
    industry = fund.get("industry", "")
    t_mean       = fund.get("t_mean")
    t_high       = fund.get("t_high")
    t_low        = fund.get("t_low")
    n_ana        = fund.get("n_ana")
    n_ana_recent = fund.get("n_ana_recent")
    n_ana_total  = fund.get("n_ana_total")
    ana_date     = fund.get("ana_date")
    ana_date_src = fund.get("ana_date_src")
    upside   = (t_mean - price) / price * 100 if t_mean and price else None

    if is_tw:
        name = TW_NAMES.get(symbol, fund.get("shortName", symbol))
    else:
        name = (fund.get("shortName") or fund.get("longName") or symbol)[:16]

    pe_label, pe_cls, pe_ind, pe_lo, pe_hi = pe_assessment(pe, symbol, sector)

    # ── Step 4: 選股信號（技術指標，獨立快取 5 min）────────────────────
    is_tpex = yf_sym.endswith(".TWO")
    tech = fetch_technical(yf_sym, symbol, is_tw, is_tpex)

    return {
        "ok": True, "symbol": symbol, "name": name, "is_tw": is_tw,
        "price": price, "chg": chg, "pct": pct,
        "pe": pe, "pe_label": pe_label, "pe_cls": pe_cls,
        "pe_ind": pe_ind, "pe_lo": pe_lo, "pe_hi": pe_hi,
        "sector": sector, "industry": industry,
        "low52": low52, "high52": high52, "pos": pos,
        "t_mean": t_mean, "t_high": t_high, "t_low": t_low,
        "n_ana": n_ana, "n_ana_recent": n_ana_recent, "n_ana_total": n_ana_total,
        "upside": upside,
        "ana_date": ana_date, "ana_date_src": ana_date_src,
        # 選股信號
        "k_val":     tech.get("k_val"),
        "k_ok":      tech.get("k_ok",  False),
        "margin_ok": tech.get("margin_ok"),   # True/False/None(N/A)
        "ma20_ok":   tech.get("ma20_ok", False),
        "tech_score": tech.get("score", 0),
    }


@st.cache_data(ttl=7200, show_spinner=False)   # 2 小時快取，減少 rate limit
def fetch_fundamentals(yf_sym: str, symbol: str) -> dict:
    """
    四段式備援取得本益比、法人目標價、最新評估日。

    問題根源：Yahoo Finance 從雲端 IP 有時只回傳 quoteType 基本欄位
    （代號/交易所/幣別，約 8 個 key），沒有 PE 或目標價。
    舊版 len > 5 的判斷太寬鬆，會誤認成功後直接 break。

    修法：
    A) ticker.info — 主要方法，嚴格驗證是否包含財務欄位
    B) analyst_price_targets — 備援目標價（yfinance 0.2.37+，不同 endpoint）
    C) income_stmt + market_cap — 備援 PE（timeseries API，較少被封鎖）
    D) upgrades_downgrades — 評估日
    """
    result = {
        "pe": None, "sector": "", "industry": "",
        "t_mean": None, "t_high": None, "t_low": None,
        "n_ana": None, "n_ana_recent": None, "n_ana_total": None,
        "shortName": "", "longName": "",
        "ana_date": None, "ana_date_src": None,
    }

    # ── A: ticker.info（主要方法；需 quoteSummary 全模組）────────────
    # 嚴格確認有真實財務資料，而不只是 quoteType 基本欄位（8 個 key）
    for attempt in range(3):
        try:
            raw = yf.Ticker(yf_sym).info      # 每次新物件，防止 yfinance 內部快取
            has_finance = (
                raw.get("trailingPE") is not None
                or raw.get("forwardPE") is not None
                or raw.get("targetMeanPrice") is not None
                or bool(raw.get("sector"))     # sector 也有意義
            )
            if raw and has_finance:
                result["pe"]       = _safe_float(raw.get("trailingPE")) or _safe_float(raw.get("forwardPE"))
                result["sector"]   = raw.get("sector", "")
                result["industry"] = raw.get("industry", "")
                result["t_mean"]   = _safe_float(raw.get("targetMeanPrice"))
                result["t_high"]   = _safe_float(raw.get("targetHighPrice"))
                result["t_low"]    = _safe_float(raw.get("targetLowPrice"))
                result["n_ana"]    = raw.get("numberOfAnalystOpinions")
                result["shortName"] = raw.get("shortName", "")
                result["longName"]  = raw.get("longName", "")
                # 若已取得 PE 與目標價，不再重試
                if result["pe"] is not None and result["t_mean"] is not None:
                    break
        except Exception:
            pass
        if attempt < 2:
            time.sleep(2)

    # ── B: analyst_price_targets（備援目標價；yfinance 0.2.37+）─────
    # 使用不同的 Yahoo Finance endpoint，雲端被封時仍可能成功
    if result["t_mean"] is None:
        try:
            apt = yf.Ticker(yf_sym).analyst_price_targets
            if apt and isinstance(apt, dict) and apt.get("mean"):
                result["t_mean"] = _safe_float(apt.get("mean"))
                result["t_high"] = _safe_float(apt.get("high"))
                result["t_low"]  = _safe_float(apt.get("low"))
                if result["n_ana"] is None:
                    result["n_ana"] = apt.get("numberOfAnalysts")
        except Exception:
            pass

    # ── C: PE = 市值 ÷ 淨利（備援本益比；timeseries API 較少被封鎖）──
    if result["pe"] is None:
        try:
            fi = yf.Ticker(yf_sym).fast_info
            mc = _safe_float(getattr(fi, "market_cap", None))
            if mc and mc > 0:
                stmt = yf.Ticker(yf_sym).income_stmt   # timeseries API
                if stmt is not None and not stmt.empty:
                    for ni_key in [
                        "Net Income",
                        "Net Income Common Stockholders",
                        "Net Income From Continuing Operations",
                    ]:
                        if ni_key in stmt.index:
                            ni = _safe_float(stmt.loc[ni_key].iloc[0])
                            if ni and ni > 0:
                                result["pe"] = round(mc / ni, 1)
                            break   # 找到對應列即停（不論 ni 正負）
        except Exception:
            pass

    # ── D: upgrades_downgrades（評估日 + 歷史追蹤家數）──────────────
    try:
        ud = yf.Ticker(yf_sym).upgrades_downgrades
        if ud is not None and not ud.empty:
            idx = ud.index[0]
            if hasattr(idx, "strftime"):
                result["ana_date"]     = idx.strftime("%Y-%m-%d")
                result["ana_date_src"] = "券商評等"
            if "Firm" in ud.columns:
                result["n_ana_total"] = int(ud["Firm"].nunique())
    except Exception:
        pass

    # ── E: recommendations_summary（近期追蹤家數，0m 期間合計）────
    try:
        recs = yf.Ticker(yf_sym).recommendations_summary
        if recs is not None and not recs.empty:
            row = recs[recs["period"] == "0m"]
            if not row.empty:
                cols = [c for c in ["strongBuy","buy","hold","sell","strongSell"] if c in row.columns]
                total = int(row[cols].sum(axis=1).iloc[0])
                if total > 0:
                    result["n_ana_recent"] = total
    except Exception:
        pass

    return result


# ════════════════════════════════════════════════════════════════
# ── 選股信號：技術指標計算 ─────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_tw_margin_change(symbol: str, is_tpex: bool = False):
    """
    查詢最近 5 個交易日融資餘額（MarginPurchaseTodayBalance）是否淨增加。
    使用 FinMind 開放 API（免費、上市+上櫃皆支援）。
    回傳 True=增加 / False=減少或持平 / None=無資料或錯誤
    """
    try:
        start_date = (now_tw() - timedelta(days=14)).strftime("%Y-%m-%d")
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset":   "TaiwanStockMarginPurchaseShortSale",
            "data_id":   symbol,
            "start_date": start_date,
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()

        if data.get("status") != 200:
            return None

        rows = data.get("data", [])
        if not rows or len(rows) < 2:
            return None

        # 取最近 5 個交易日
        recent = rows[-5:] if len(rows) >= 5 else rows
        if len(recent) < 2:
            return None

        first_bal = int(recent[0].get("MarginPurchaseTodayBalance", 0))
        last_bal  = int(recent[-1].get("MarginPurchaseTodayBalance", 0))
        return last_bal > first_bal   # True = 融資餘額增加

    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def fetch_technical(yf_sym: str, symbol: str, is_tw: bool, is_tpex: bool) -> dict:
    """
    計算三項選股條件並回傳分數（0–3）：
    ① K值 < 40  ── 9期KD隨機指標（台灣慣用 α=1/3 指數平滑）
    ② 近5日融資增加 ── 僅台股；美股回傳 margin_ok=None（N/A，不計分）
    ③ 收盤 > 20MA 且 20MA 上升
    """
    result = {
        "k_val":     None,
        "k_ok":      False,
        "margin_ok": None,    # True / False / None(N/A)
        "ma20_ok":   False,
        "score":     0,
    }

    # ── ①③：下載60日歷史計算技術指標 ──────────────────────────────
    try:
        hist = yf.download(
            yf_sym, period="60d", progress=False,
            auto_adjust=True, multi_level_index=False,
        )
        if hist.empty or len(hist) < 20:
            return result

        close = hist["Close"].dropna()
        high  = hist["High"].dropna()
        low   = hist["Low"].dropna()

        # ① K值：9期RSV → 指數平滑（α=1/3，等效 2/3×Kprev + 1/3×RSV）
        if len(close) >= 9:
            n     = 9
            ll    = low.rolling(window=n).min()
            hh    = high.rolling(window=n).max()
            denom = (hh - ll).replace(0.0, float("nan"))
            rsv   = (close - ll) / denom * 100
            rsv   = rsv.fillna(50.0)          # 分母為0時預設50
            k_ser = rsv.ewm(alpha=1/3, adjust=False).mean()
            k_val = float(k_ser.iloc[-1])
            result["k_val"] = round(k_val, 1)
            result["k_ok"]  = k_val < 40.0

        # ③ 收盤 > 20MA 且 20MA 今日 > 昨日
        if len(close) >= 21:
            ma20   = close.rolling(window=20).mean()
            cur_ma = float(ma20.iloc[-1])
            prv_ma = float(ma20.iloc[-2])
            cur_c  = float(close.iloc[-1])
            result["ma20_ok"] = (cur_c > cur_ma) and (cur_ma > prv_ma)

    except Exception:
        pass

    # ── ②：融資（僅台股）────────────────────────────────────────────
    if is_tw:
        result["margin_ok"] = fetch_tw_margin_change(symbol, is_tpex)

    # ── 加總分數 ──────────────────────────────────────────────────
    result["score"] = sum([
        bool(result["k_ok"]),
        result["margin_ok"] is True,   # None(N/A) 不計分
        bool(result["ma20_ok"]),
    ])
    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_stocks_batch(symbols: tuple) -> list:
    """
    批次取得股票資料，每支之間等 0.6 秒，避免 Yahoo Finance rate limit。
    symbols 必須是 tuple（可 hash，才能被 st.cache_data 快取）。
    """
    results = []
    for i, sym in enumerate(symbols):
        if i > 0:
            time.sleep(2.0)   # 每支股票之間等 2 秒（已含子請求內部延遲）
        results.append(_fetch_one(sym))
    return results


@st.cache_data(ttl=300, show_spinner=False)
def fetch_global():
    results = []
    for i, cfg in enumerate(INDICATORS):
        if i > 0:
            time.sleep(0.3)   # 全球指標較輕，0.3 秒間隔
        try:
            fi    = yf.Ticker(cfg["symbol"], session=_http_session()).fast_info
            price = float(fi.last_price)
            prev  = float(fi.previous_close or price)
            chg   = price - prev
            pct   = chg / prev * 100 if prev else 0
            results.append({**cfg, "price": price, "chg": chg, "pct": pct, "ok": True})
        except Exception:
            results.append({**cfg, "ok": False})
    return results


# ── fetch_stock 保留作向下相容（sidebar clear 用）────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock(symbol: str) -> dict:
    """單支股票包裝，供需要單獨呼叫時使用"""
    try:
        is_tw  = bool(__import__("re").match(r"^\d{4,6}$", symbol))
        yf_sym = symbol + ".TW" if is_tw else symbol

        ticker = yf.Ticker(yf_sym, session=_http_session())
        info   = ticker.info or {}
        fi     = ticker.fast_info

        price = float(fi.last_price)     if fi.last_price     else None
        prev  = float(fi.previous_close) if fi.previous_close else price
        chg   = (price - prev)           if price and prev    else None
        pct   = chg / prev * 100         if chg and prev      else None

        low52  = info.get("fiftyTwoWeekLow")
        high52 = info.get("fiftyTwoWeekHigh")
        pos    = None
        if price and low52 and high52 and high52 > low52:
            pos = (price - low52) / (high52 - low52) * 100

        pe      = info.get("trailingPE") or info.get("forwardPE")
        sector  = info.get("sector", "")
        industry = info.get("industry", "")
        t_mean  = info.get("targetMeanPrice")
        t_high  = info.get("targetHighPrice")
        t_low   = info.get("targetLowPrice")
        n_ana   = info.get("numberOfAnalystOpinions")
        upside  = (t_mean - price) / price * 100 if t_mean and price else None

        # ── 法人評估日期 + 歷史追蹤家數 ──
        ana_date     = None
        ana_date_src = None
        n_ana_recent = None
        n_ana_total  = None
        try:
            ud = ticker.upgrades_downgrades
            if ud is not None and not ud.empty:
                idx = ud.index[0]
                if hasattr(idx, "strftime"):
                    ana_date     = idx.strftime("%Y-%m-%d")
                    ana_date_src = "券商評等"
                if "Firm" in ud.columns:
                    n_ana_total = int(ud["Firm"].nunique())
        except Exception:
            pass

        # ── 近期追蹤家數（recommendations_summary 0m 合計）──
        try:
            recs = ticker.recommendations_summary
            if recs is not None and not recs.empty:
                row = recs[recs["period"] == "0m"]
                if not row.empty:
                    cols = [c for c in ["strongBuy","buy","hold","sell","strongSell"] if c in row.columns]
                    total = int(row[cols].sum(axis=1).iloc[0])
                    if total > 0:
                        n_ana_recent = total
        except Exception:
            pass

        # ── 公司名稱 ──
        if is_tw:
            name = TW_NAMES.get(symbol, info.get("shortName", symbol))
        else:
            name = (info.get("shortName") or info.get("longName") or symbol)[:16]

        # ── P/E 產業評比 ──
        pe_label, pe_cls, pe_ind, pe_lo, pe_hi = pe_assessment(pe, symbol, sector)

        return {
            "ok": True, "symbol": symbol, "name": name, "is_tw": is_tw,
            "price": price, "chg": chg, "pct": pct,
            "pe": pe, "pe_label": pe_label, "pe_cls": pe_cls,
            "pe_ind": pe_ind, "pe_lo": pe_lo, "pe_hi": pe_hi,
            "sector": sector, "industry": industry,
            "low52": low52, "high52": high52, "pos": pos,
            "t_mean": t_mean, "t_high": t_high, "t_low": t_low,
            "n_ana": n_ana, "n_ana_recent": n_ana_recent, "n_ana_total": n_ana_total,
            "upside": upside,
            "ana_date": ana_date, "ana_date_src": ana_date_src,
        }
    except Exception as e:
        return {"ok": False, "symbol": symbol, "error": str(e)}


# ════════════════════════════════════════════════════════════════
# ── 輔助格式化 ────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
def fmt(v, dec=2):
    if v is None:
        return None
    if v >= 1000:
        return f"{v:,.0f}"
    return f"{v:.{dec}f}"

def chg_html(val, is_pct=False):
    if val is None:
        return '<span class="na-txt">—</span>'
    cls    = "up" if val >= 0 else "down"
    sign   = "+" if val >= 0 else ""
    suffix = "%" if is_pct else ""
    return f'<span class="{cls}">{sign}{val:.2f}{suffix}</span>'

def pos_cell(pct):
    if pct is None:
        return '<span class="na-txt">—</span>'
    if pct <= 30:
        badge, color = '<span class="badge-low">低位階</span>', "#10b981"
    elif pct <= 70:
        badge, color = '<span class="badge-mid">中位階</span>', "#f59e0b"
    else:
        badge, color = '<span class="badge-high">高位階</span>', "#ef4444"
    fill = f'<div class="pos-fill" style="width:{min(pct,100):.0f}%;background:{color}"></div>'
    bar  = f'<span class="pos-bar">{fill}</span>'
    return (f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:7px">'
            f'{badge}&nbsp;{bar}'
            f'<span style="font-size:0.7rem;color:#94a3b8">{pct:.0f}%</span></div>')

def date_freshness(date_str):
    """日期新鮮度：< 90天 → 綠, < 180天 → 橙, 更早 → 灰；格式不符則顯示 —"""
    import re
    if not date_str or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date_str)):
        return "na-txt", "—"
    try:
        delta = (now_tw().replace(tzinfo=None) - datetime.strptime(date_str, "%Y-%m-%d")).days
        if delta <= 90:
            return "date-fresh", f"{date_str}　✓ 近期"
        elif delta <= 180:
            return "date-old",   f"{date_str}　⚠ 逾90天"
        else:
            return "date-txt",   f"{date_str}　逾半年"
    except Exception:
        return "na-txt", "—"


# ════════════════════════════════════════════════════════════════
# ── 渲染：全球指標卡片（2列排列）────────────────────────────────────
# ════════════════════════════════════════════════════════════════
def render_global(data):
    # 分兩列排列指標卡片
    row1 = data[:6]
    row2 = data[6:]

    for row in (row1, row2):
        cols = st.columns(len(row))
        for col, d in zip(cols, row):
            with col:
                if not d.get("ok"):
                    col.markdown(f"""
                    <div class="ind-card" style="border-top-color:#e2e8f0">
                      <div class="ind-label">{d['label'].replace(chr(10),' ')}</div>
                      <div class="ind-value" style="color:#cbd5e1">—</div>
                      <div class="ind-neu">無法取得</div>
                    </div>""", unsafe_allow_html=True)
                    continue

                price = d["price"]
                pct   = d["pct"]
                chg   = d["chg"]
                dec   = d.get("dec", 2)
                suf   = d.get("suffix", "")
                src   = d.get("src", "")

                if price >= 10_000:
                    pstr = f"{price:,.0f}{suf}"
                elif price >= 100:
                    pstr = f"{price:,.{dec}f}{suf}"
                else:
                    pstr = f"{price:.{dec}f}{suf}"

                if pct > 0:
                    border_color, chg_cls, arrow = "#ef4444", "ind-up", "▲"   # 台灣慣例：紅漲
                elif pct < 0:
                    border_color, chg_cls, arrow = "#10b981", "ind-down", "▼"  # 台灣慣例：綠跌
                else:
                    border_color, chg_cls, arrow = "#94a3b8", "ind-neu", "─"

                chg_str = f"{arrow} {abs(chg):.{dec}f} ({abs(pct):.2f}%)"
                note    = f'<div class="ind-note">{d["note"]}</div>' if d.get("note") else ""
                label   = d["label"].replace("\n", "<br>")

                col.markdown(f"""
                <div class="ind-card" style="border-top-color:{border_color}">
                  <div class="ind-label">{label}</div>
                  <div class="ind-value">{pstr}</div>
                  <div class="{chg_cls}">{chg_str}</div>
                  {note}
                  <div class="ind-src">來源：{src}</div>
                </div>""", unsafe_allow_html=True)
        if row is row1:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ── 渲染：觀察名單表格 ────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
def render_watchlist(stocks):
    rows = ""
    for s in stocks:
        sym = s["symbol"]
        if not s.get("ok"):
            rows += f"""<tr>
              <td class="left">
                <div class="stk-code">{sym}</div>
                <div class="stk-name" style="color:#dc2626">{s.get('error','載入失敗')[:40]}</div>
              </td>
              <td colspan="6" class="na-txt" style="text-align:center">資料載入失敗</td></tr>"""
            continue

        # ── 現價 ──
        p     = s["price"]
        p_str = fmt(p, dec=0 if (p and p >= 100) else 2) if p else "—"
        pct_html = chg_html(s["pct"], is_pct=True)
        chg_sub  = f'<div class="chg-sub">{chg_html(s["chg"])}</div>' if s.get("chg") is not None else ""

        # ── 股票名稱＋產業標籤 ──
        ind_tag = ""
        if s.get("pe_ind") and s["pe_ind"] not in ("ETF", "市場"):
            ind_tag = f'<div class="stk-ind">{s["pe_ind"]}</div>'

        # ── 本益比＋產業評比 ──
        pe = s["pe"]
        if pe:
            if pe < 15:
                val_cls = "pe-ok"
            elif pe < 30:
                val_cls = "pe-mid"
            else:
                val_cls = "pe-high"
            pe_str  = f'<div class="pe-val {val_cls}">{pe:.1f}×</div>'

            label   = s.get("pe_label")
            a_cls   = s.get("pe_cls", "pe-a-mid")
            pe_lo   = s.get("pe_lo")
            pe_hi   = s.get("pe_hi")
            if label and label != "ETF" and pe_lo and pe_hi:
                ind_avg = (pe_lo + pe_hi) / 2
                assess  = f'<div><span class="pe-assess {a_cls}">{label}</span></div>'
                avg_txt = f'<div class="pe-ind-avg">產業均 {ind_avg:.0f}× (區間 {pe_lo}–{pe_hi})</div>'
            elif label == "ETF":
                assess  = f'<div><span class="pe-assess pe-a-mid">ETF</span></div>'
                avg_txt = ""
            else:
                assess  = f'<div><span class="pe-assess {a_cls}">{label}</span></div>' if label else ""
                avg_txt = ""
            pe_html = f'{pe_str}{assess}{avg_txt}'
        else:
            pe_html = '<span class="na-txt">—</span>'

        # ── 52週位階 ──
        pos_html = pos_cell(s["pos"])
        if s["low52"] and s["high52"]:
            lo  = fmt(s["low52"],  dec=0 if s["low52"]  >= 100 else 2)
            hi  = fmt(s["high52"], dec=0 if s["high52"] >= 100 else 2)
            rng = f'<div class="date-txt" style="margin-top:5px">{lo} – {hi}</div>'
        else:
            rng = ""

        # ── 法人目標價 ──
        t_mean = s["t_mean"]
        if t_mean:
            t_str    = fmt(t_mean, dec=0 if t_mean >= 100 else 2)
            up       = s["upside"]
            up_cls   = "up-pct" if up and up >= 0 else "dn-pct"
            sign     = "+" if up and up >= 0 else ""
            up_str   = f'<div class="{up_cls}">{sign}{up:.1f}% 上漲空間</div>' if up is not None else ""
            target_html = f'<div class="target-val">{t_str}</div>{up_str}'
            if s.get("t_low") and s.get("t_high"):
                tlo = fmt(s["t_low"],  dec=0 if s["t_low"]  >= 100 else 2)
                thi = fmt(s["t_high"], dec=0 if s["t_high"] >= 100 else 2)
                target_html += f'<div class="date-txt">目標區間 {tlo}~{thi}</div>'
            # 券商追蹤家數：近半年活躍家數｜歷史總計（來自 upgrades_downgrades 唯一券商數）
            n_recent = s.get("n_ana_recent")
            n_ud     = s.get("n_ana_total")    # None for TW（Yahoo 無 upgrades_downgrades 資料）
            n_base   = int(s["n_ana"]) if s.get("n_ana") else None
            n_total  = n_ud or n_base          # 優先用 upgrades 唯一家數，備援 numberOfAnalystOpinions
            if n_recent and n_total and n_total != n_recent:
                ana_line = f'近半年{n_recent}家｜共{n_total}家'
            elif n_recent:
                ana_line = f'追蹤{n_recent}家券商'
            elif n_total:
                ana_line = f'{n_total}家券商'
            else:
                ana_line = ""
            if ana_line:
                target_html += f'<div class="ana-cnt">{ana_line}</div>'
        else:
            target_html = '<span class="na-txt">—</span>'

        # ── 評估日期＋來源 ──
        if s.get("ana_date"):
            d_cls, d_str = date_freshness(s["ana_date"])
            src_str = s.get("ana_date_src", "")
            date_html = (f'<span class="{d_cls}">{d_str}</span>'
                         + (f'<div class="src-tag">{src_str}·Yahoo Finance</div>' if src_str else ""))
        else:
            date_html = '<span class="na-txt">—</span>'

        # ── 選股信號（K值 / 融資 / 20MA）──
        score  = s.get("tech_score", 0)
        k_ok   = s.get("k_ok",  False)
        m_ok   = s.get("margin_ok")     # True / False / None(N/A)
        ma_ok  = s.get("ma20_ok", False)
        k_v    = s.get("k_val")
        _is_tw = s.get("is_tw", False)

        # 條件狀態：🟢達成 / 🔴未達成
        k_dot  = "🟢" if k_ok  else "🔴"
        ma_dot = "🟢" if ma_ok else "🔴"
        k_lbl  = (f"K={k_v:.0f}" if k_v is not None else "K=?")

        # 融資條件：僅台股顯示，美股直接省略
        if _is_tw:
            m_dot  = "🟢" if m_ok is True else "🔴"
            margin_part = f"&emsp;{m_dot}&thinsp;融資"
        else:
            margin_part = ""   # 美股不顯示融資

        chk_str = "✅" * score if score > 0 else '<span class="na-txt" style="font-size:1rem">—</span>'
        signal_html = (
            f'<div style="text-align:center;line-height:1.2">'
            f'  <div style="font-size:1.32rem;letter-spacing:2px">{chk_str}</div>'
            f'  <div style="font-size:0.84rem;color:#64748b;margin-top:5px;white-space:nowrap">'
            f'    {k_dot}&thinsp;{k_lbl}{margin_part}&emsp;{ma_dot}&thinsp;均線'
            f'  </div>'
            f'</div>'
        )

        rows += f"""<tr>
          <td class="left">
            <div class="stk-code">{sym}</div>
            <div class="stk-name">{s['name']}</div>
            {ind_tag}
          </td>
          <td><div class="price">{p_str}</div>{chg_sub}</td>
          <td>{pct_html}</td>
          <td style="min-width:130px">{pe_html}</td>
          <td style="min-width:185px">{pos_html}{rng}</td>
          <td style="min-width:155px">{target_html}</td>
          <td style="min-width:120px">{date_html}</td>
          <td style="min-width:115px;text-align:center">{signal_html}</td>
        </tr>"""

    st.html(f"""
    <div class="wl-wrap">
    <table class="wl-table">
      <thead><tr>
        <th class="left">股票</th>
        <th>現價</th>
        <th>漲跌幅</th>
        <th>本益比 P/E</th>
        <th>52 週位階</th>
        <th>法人目標價</th>
        <th>最新評估日</th>
        <th>選股信號</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table></div>""")


# ════════════════════════════════════════════════════════════════
# ── Main ──────────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════
# ── Sidebar 輔助：單一股票清單的 ↑↓✕ 列表 ───────────────────────────
# ════════════════════════════════════════════════════════════════
def _sidebar_list(wl: list[str], key_prefix: str, save_fn, name_map: dict):
    """渲染帶有 ↑↓✕ 按鈕的清單；直接修改傳入的 list 並呼叫 save_fn。"""
    n = len(wl)
    for i, sym in enumerate(list(wl)):
        cn, cup, cdn, cdel = st.columns([3.2, 0.7, 0.7, 0.7])
        cn.markdown(
            f"<span style='font-size:1.05rem;font-weight:700;color:#dbeafe'>{sym}</span>"
            f"&nbsp;<span style='color:#7ab4d8;font-size:0.98rem'>"
            f"{name_map.get(sym,'')}</span>",
            unsafe_allow_html=True)
        if cup.button("↑", key=f"{key_prefix}up_{sym}",
                      disabled=(i == 0), use_container_width=True):
            wl[i], wl[i-1] = wl[i-1], wl[i]
            save_fn(wl); st.rerun()
        if cdn.button("↓", key=f"{key_prefix}dn_{sym}",
                      disabled=(i == n-1), use_container_width=True):
            wl[i], wl[i+1] = wl[i+1], wl[i]
            save_fn(wl); st.rerun()
        if cdel.button("✕", key=f"{key_prefix}rm_{sym}",
                       use_container_width=True):
            wl.pop(i); save_fn(wl); st.rerun()


# ════════════════════════════════════════════════════════════════
def main():
    # ── 初始化 session state ──
    if "tw_list" not in st.session_state or "us_list" not in st.session_state:
        tw, us, key = load_watchlists()
        st.session_state.tw_list    = tw
        st.session_state.us_list    = us
        st.session_state.profile_key = key
        # 若 key 存在但 profile 檔尚未建立，以目前 URL 清單建立 profile
        if key and load_profile(key)[0] is None:
            save_profile(key, tw, us)

    tw_list = st.session_state.tw_list
    us_list = st.session_state.us_list

    # ══ Sidebar ══════════════════════════════════════════════════
    with st.sidebar:
        st.markdown("### 📋 觀察名單管理")

        new = st.text_input("新增股票代碼",
                            placeholder="台股: 2330　　美股: AAPL")
        if st.button("＋ 新增（自動分類）", use_container_width=True,
                     type="primary"):
            code = new.strip().upper()
            if not code:
                pass
            elif is_tw_stock(code):
                if code not in tw_list:
                    tw_list.append(code); save_tw(tw_list)
                    fetch_stock.clear(); st.rerun()
                else:
                    st.warning(f"{code} 已在台股清單")
            else:
                if code not in us_list:
                    us_list.append(code); save_us(us_list)
                    fetch_stock.clear(); st.rerun()
                else:
                    st.warning(f"{code} 已在美股清單")

        # ── 台股清單 ──
        st.markdown("---")
        tw_hdr = (f"🇹🇼 台股清單（{len(tw_list)} 支）　"
                  f"<span style='font-size:0.93rem;color:#4a7aa0'>↑↓ 排序</span>")
        st.markdown(f"**{tw_hdr}**", unsafe_allow_html=True)
        if tw_list:
            _sidebar_list(tw_list, "tw_", save_tw, TW_NAMES)
        else:
            st.caption("尚無台股，輸入4~6位數代碼新增")

        # ── 美股清單 ──
        st.markdown("---")
        us_hdr = (f"🇺🇸 美股清單（{len(us_list)} 支）　"
                  f"<span style='font-size:0.93rem;color:#4a7aa0'>↑↓ 排序</span>")
        st.markdown(f"**{us_hdr}**", unsafe_allow_html=True)
        if us_list:
            _sidebar_list(us_list, "us_", save_us, {})
        else:
            st.caption("尚無美股，輸入英文代碼新增（如 AAPL）")

        st.markdown("---")
        if st.button("🔄 強制重新整理", use_container_width=True):
            fetch_global.clear(); fetch_stocks_batch.clear()
            fetch_fundamentals.clear(); fetch_stock.clear()
            fetch_technical.clear(); fetch_tw_margin_change.clear()
            st.rerun()

        # ── 跨裝置同步代號 ──────────────────────────────────────────
        st.markdown("---")
        st.markdown("**🔗 跨裝置同步**")
        cur_key = st.session_state.get("profile_key", "")
        new_key = st.text_input(
            "同步代號",
            value=cur_key,
            placeholder="自訂代號（如 mystock88）",
            help="電腦和手機填入相同代號，清單自動同步"
        )
        col_apply, col_pull = st.columns(2)
        with col_apply:
            if st.button("套用", use_container_width=True):
                nk = new_key.strip()
                if nk:
                    tw_p, us_p, ts = load_profile(nk)
                    if tw_p is not None:
                        # 已有 profile → 載入
                        st.session_state.tw_list    = tw_p
                        st.session_state.us_list    = us_p
                        st.session_state.profile_key = nk
                        st.query_params["key"] = nk
                        save_tw(tw_p); save_us(us_p)
                    else:
                        # 新代號 → 以目前清單建立
                        save_profile(nk, tw_list, us_list)
                        st.session_state.profile_key = nk
                        st.query_params["key"] = nk
                else:
                    st.session_state.profile_key = ""
                    st.query_params.pop("key", None)
                st.rerun()
        with col_pull:
            pull_disabled = not bool(cur_key)
            if st.button("拉取更新", use_container_width=True, disabled=pull_disabled):
                tw_p, us_p, ts = load_profile(cur_key)
                if tw_p is not None:
                    st.session_state.tw_list = tw_p
                    st.session_state.us_list = us_p
                    save_tw(tw_p); save_us(us_p)
                st.rerun()

        if cur_key:
            _, _, ts = load_profile(cur_key)
            ts_str = f"· 上次更新 {ts}" if ts else ""
            st.caption(f"✅ 同步中：**{cur_key}**　{ts_str}")
        else:
            st.caption("未設定代號，清單僅存在目前網址")

        st.markdown("---")
        st.caption("• 資料每 2 分鐘自動更新")
        st.caption("⚠️ 來源：Yahoo Finance，僅供參考")

    # ══ 頁首 ══════════════════════════════════════════════════════
    now_str = now_tw().strftime("%Y/%m/%d %H:%M")  # 台灣時間 UTC+8
    st.markdown(f"""
    <div class="app-header">
      <div>
        <div class="app-title">📊 股票儀表板</div>
        <div class="app-subtitle">
          全球經濟指標 · 台股 {len(tw_list)} 支 · 美股 {len(us_list)} 支 ·
          法人目標價 · 本益比產業評比
        </div>
      </div>
      <div class="app-time">更新時間<br>
        <strong style="color:#fff;font-size:0.95rem">{now_str}</strong>
      </div>
    </div>""", unsafe_allow_html=True)

    # ══ 全球指標 ══════════════════════════════════════════════════
    st.markdown('<div class="section-hdr">🌐 全球經濟指標</div>',
                unsafe_allow_html=True)
    with st.spinner("載入全球指標…"):
        global_data = fetch_global()
    render_global(global_data)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)

    # ══ 手機版：新增股票快捷區（桌機可用側欄；手機側欄預設收起）══
    with st.expander("📱 新增 / 管理股票（手機版）", expanded=False):
        m_col1, m_col2 = st.columns([3, 1])
        m_code = m_col1.text_input("輸入代碼", placeholder="台股: 2330　美股: AAPL",
                                   key="mobile_add_input", label_visibility="collapsed")
        if m_col2.button("＋ 新增", key="mobile_add_btn", use_container_width=True):
            code = m_code.strip().upper()
            if code:
                if is_tw_stock(code):
                    if code not in tw_list:
                        tw_list.append(code); save_tw(tw_list)
                        fetch_stocks_batch.clear(); st.rerun()
                    else:
                        st.warning(f"{code} 已在台股清單")
                else:
                    if code not in us_list:
                        us_list.append(code); save_us(us_list)
                        fetch_stocks_batch.clear(); st.rerun()
                    else:
                        st.warning(f"{code} 已在美股清單")

        # 目前清單（可刪除）
        if tw_list or us_list:
            st.caption("🇹🇼 台股：" + "　".join(tw_list) if tw_list else "")
            st.caption("🇺🇸 美股：" + "　".join(us_list) if us_list else "")

        # 書籤連結提示
        st.info("💡 **儲存個人清單**：將目前頁面網址加入手機書籤，下次直接開書籤即可恢復你的清單。")

    # ══ 跨裝置同步（主畫面版，手機不用開側欄）══════════════════════
    cur_key = st.session_state.get("profile_key", "")
    sync_label = f"🔗 跨裝置同步　✅ 代號：{cur_key}" if cur_key else "🔗 跨裝置同步（電腦 ↔ 手機）"
    with st.expander(sync_label, expanded=not bool(cur_key)):
        st.markdown(
            "電腦和手機輸入**相同代號**，清單自動同步。"
            "　改了一台後，另一台點「**拉取更新**」即可。",
            unsafe_allow_html=False)
        sc1, sc2, sc3 = st.columns([3, 1, 1])
        key_input = sc1.text_input(
            "同步代號",
            value=cur_key,
            placeholder="自訂代號，例如 mystock88",
            label_visibility="collapsed",
            key="main_sync_key_input",
        )
        if sc2.button("套用", key="main_sync_apply", use_container_width=True):
            nk = key_input.strip()
            if nk:
                tw_p, us_p, ts = load_profile(nk)
                if tw_p is not None:
                    st.session_state.tw_list     = tw_p
                    st.session_state.us_list     = us_p
                    st.session_state.profile_key = nk
                    st.query_params["key"] = nk
                    save_tw(tw_p); save_us(us_p)
                    st.success(f"已載入代號「{nk}」的清單（上次更新 {ts}）")
                else:
                    save_profile(nk, tw_list, us_list)
                    st.session_state.profile_key = nk
                    st.query_params["key"] = nk
                    st.success(f"已建立新代號「{nk}」，目前清單已儲存")
            else:
                st.session_state.profile_key = ""
                st.query_params.pop("key", None)
                st.info("已清除同步代號")
            st.rerun()
        if sc3.button("拉取更新", key="main_sync_pull",
                      use_container_width=True, disabled=not bool(cur_key)):
            tw_p, us_p, ts = load_profile(cur_key)
            if tw_p is not None:
                st.session_state.tw_list = tw_p
                st.session_state.us_list = us_p
                save_tw(tw_p); save_us(us_p)
                st.success(f"已從代號「{cur_key}」拉取最新清單（{ts}）")
            else:
                st.warning("找不到同步資料，請重新套用代號")
            st.rerun()
        if cur_key:
            _, _, ts = load_profile(cur_key)
            st.caption(f"上次同步：{ts}　｜　將含有 ?key={cur_key} 的網址加入書籤，下次自動載入")

    # ══ 觀察名單 ══════════════════════════════════════════════════
    st.markdown('<div class="section-hdr">👁 我的觀察名單</div>',
                unsafe_allow_html=True)

    # ── 選股邏輯說明條 ──
    st.markdown("""
<div style="
  background:linear-gradient(90deg,#eff6ff 0%,#f8fbff 100%);
  border:1px solid #bfdbfe; border-left:4px solid #2563eb;
  border-radius:0 12px 12px 0; padding:11px 18px; margin-bottom:14px;
  display:flex; align-items:center; gap:6px; flex-wrap:wrap;
">
  <span style="font-size:0.98rem;font-weight:800;color:#1e40af;
               margin-right:8px;white-space:nowrap;">📌 目前選股邏輯</span>
  <span style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:20px;
               padding:5px 15px;font-size:0.95rem;font-weight:700;color:#065f46;
               white-space:nowrap;">① K值 &lt; 40</span>
  <span style="color:#cbd5e1;font-size:1rem">＋</span>
  <span style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:20px;
               padding:5px 15px;font-size:0.95rem;font-weight:700;color:#065f46;
               white-space:nowrap;">② 近5日融資增加（台股）</span>
  <span style="color:#cbd5e1;font-size:1rem">＋</span>
  <span style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:20px;
               padding:5px 15px;font-size:0.95rem;font-weight:700;color:#065f46;
               white-space:nowrap;">③ 收盤價 &gt; 20日均線且均線上升</span>
  <span style="font-size:0.86rem;color:#94a3b8;margin-left:6px;white-space:nowrap;">
    三項全達成 ✅✅✅ · 二項 ✅✅ · 一項 ✅（美股②不適用）
  </span>
</div>""", unsafe_allow_html=True)

    if not tw_list and not us_list:
        st.info("觀察名單是空的，請點上方「📱 新增 / 管理股票」或展開左側側欄新增代碼。")
        return

    # ── 🇹🇼 台股（可折疊）──
    if tw_list:
        with st.expander(f"🇹🇼 台股觀察名單（{len(tw_list)} 支）",
                         expanded=True):
            with st.spinner("載入台股資料…"):
                tw_stocks = fetch_stocks_batch(tuple(tw_list))
            render_watchlist(tw_stocks)

    # ── 🇺🇸 美股（可折疊）──
    if us_list:
        with st.expander(f"🇺🇸 美股觀察名單（{len(us_list)} 支）",
                         expanded=True):
            with st.spinner("載入美股資料…"):
                us_stocks = fetch_stocks_batch(tuple(us_list))
            render_watchlist(us_stocks)

    # ── 說明欄 ──
    with st.expander("📖 欄位說明 & 資料來源"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""
**本益比 P/E 產業評比**
- **低估**：低於該產業均值低檔
- **合理**：介於產業正常估值區間
- **偏高**：超過產業均值高檔
- 「產業均 XX×」＝該產業中位數 P/E
- 基準參考：Bloomberg、歷史均值""")
        with c2:
            st.markdown("""
**最新評估日**
- ✓ 綠色：90天內（資訊新鮮）
- ⚠ 橙色：90–180天（建議確認）
- 灰色：超過180天（報告可能過時）
- — ：Yahoo Finance 查無券商記錄
- 來源：Yahoo Finance 券商評等資料""")
        with c3:
            st.markdown("""
**全球指標來源**
- 股價 / 指數 / 匯率：Yahoo Finance
- 美債10年期：^TNX（CBOE）
- DXY 美元指數：ICE / Yahoo Finance
- VIX 恐慌指數：CBOE / Yahoo Finance
- 黃金 / 原油：CME 期貨
- ※ 台指期夜盤需 TAIFEX API""")

    st.markdown("""
    <div class="footer-note">
      ※ 法人目標價為 Yahoo Finance 分析師共識均值，評估日取各券商最新評等記錄日期。<br>
      ※ 本益比產業評比基準參考 Bloomberg 產業均值，不同景氣週期可能有所差異，僅供相對比較。<br>
      ※ 本平台資料僅供研究參考，不構成任何投資建議。
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
