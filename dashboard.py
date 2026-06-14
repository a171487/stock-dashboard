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
    # 使用者觀察名單補充
    "2492": "華新科", "8358": "金居",   "2313": "華通",   "3491": "昇達科",
    "8299": "群聯",   "2449": "京元電", "6269": "台郡",   "3529": "力旺",
    "4966": "譜瑞",   "6515": "穎崴",   "3702": "大聯大", "2376": "技嘉",
    "2377": "微星",   "3006": "晶豪科", "6274": "台燿",   "2401": "凌陽",
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
# ── 跨裝置同步：GitHub Gist（永久）+ /tmp 備援 ───────────────────
# ════════════════════════════════════════════════════════════════
_PROFILE_DIR   = Path("/tmp/stock_profiles")
_GIST_FILENAME = "stock-dashboard-profiles.json"
_GIST_ID_CACHE = Path("/tmp/stock_gist_id.txt")

def _gh_headers():
    token = st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _profile_path(key: str) -> Path:
    safe = hashlib.sha256(key.encode()).hexdigest()[:20]
    return _PROFILE_DIR / f"{safe}.json"

def _get_gist_id() -> str | None:
    """找到或建立 profiles Gist，回傳 Gist ID。以 /tmp 快取避免重複查詢。"""
    if _GIST_ID_CACHE.exists():
        return _GIST_ID_CACHE.read_text().strip()
    hdrs = _gh_headers()
    if not hdrs:
        return None
    try:
        r = requests.get("https://api.github.com/gists", headers=hdrs, timeout=10)
        if r.ok:
            for gist in r.json():
                if _GIST_FILENAME in gist.get("files", {}):
                    gid = gist["id"]
                    _GIST_ID_CACHE.write_text(gid)
                    return gid
        r2 = requests.post("https://api.github.com/gists", headers=hdrs, timeout=10, json={
            "description": "Stock Dashboard Profiles",
            "public": False,
            "files": {_GIST_FILENAME: {"content": "{}"}}
        })
        if r2.ok:
            gid = r2.json()["id"]
            _GIST_ID_CACHE.write_text(gid)
            return gid
    except Exception:
        pass
    return None

def load_profile(key: str):
    """讀取 profile。優先從 GitHub Gist，備援用 /tmp。"""
    gid = _get_gist_id()
    if gid:
        try:
            hdrs = _gh_headers()
            r = requests.get(f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10)
            if r.ok:
                content = r.json()["files"][_GIST_FILENAME]["content"]
                profiles = json.loads(content)
                d = profiles.get(key, {})
                if d:
                    return d.get("tw", []), d.get("us", []), d.get("ts", "")
        except Exception:
            pass
    # 備援：/tmp
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
    """寫入 profile。優先存 GitHub Gist，同時也存 /tmp。"""
    ts   = now_tw().strftime("%m/%d %H:%M")
    data = {"tw": tw, "us": us, "ts": ts}
    gid  = _get_gist_id()
    if gid:
        try:
            hdrs = _gh_headers()
            r = requests.get(f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10)
            profiles = json.loads(r.json()["files"][_GIST_FILENAME]["content"]) if r.ok else {}
            profiles[key] = data
            requests.patch(f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10, json={
                "files": {_GIST_FILENAME: {"content": json.dumps(profiles, ensure_ascii=False)}}
            })
        except Exception:
            pass
    # 也存 /tmp
    try:
        _PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        _profile_path(key).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
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

    has_url_stocks = bool(tw_raw) and bool(us_raw)
    if key and not has_url_stocks:
        # URL 沒有明確清單時才從 profile 讀取
        tw_p, us_p, _ = load_profile(key)
        if tw_p is not None:
            tw, us = tw_p, us_p

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

    # ── Step 1: 股價（三重來源）────────────────────────────────────────
    # 來源優先序（台股）：
    #   ① Yahoo Finance fast_info（chart API，最快）
    #   ② TWSE/TPEx 官方 mis API（mis.twse.com.tw，完全獨立）
    #   ③ Yahoo Finance yf.download（備援，不同 code path）
    # 來源優先序（美股）：① Yahoo fast_info  ② Yahoo download
    price = prev = chg = pct = None
    yf_sym = symbol + ".TW" if is_tw else symbol   # 預設

    def _try_price(sym: str):
        """來源①③：Yahoo Finance fast_info / download"""
        nonlocal price, prev, chg, pct
        try:
            fi = yf.Ticker(sym, session=_http_session()).fast_info
            p  = _safe_float(fi.last_price)
            if not p:
                return False
            pv     = _safe_float(fi.previous_close) or p
            price  = p; prev = pv
            chg    = price - prev
            pct    = chg / prev * 100 if prev else None
            return True
        except Exception:
            return False

    def _try_price_dl(sym: str):
        """來源③：Yahoo Finance yf.download（備援）"""
        nonlocal price, prev, chg, pct
        try:
            hist = yf.download(sym, period="5d", progress=False,
                               auto_adjust=True, multi_level_index=False)
            if hist.empty or len(hist) < 1:
                return False
            p = _safe_float(hist["Close"].iloc[-1])
            if not p:
                return False
            pv     = _safe_float(hist["Close"].iloc[-2]) if len(hist) > 1 else p
            price  = p; prev = pv
            chg    = price - prev
            pct    = chg / prev * 100 if prev else None
            return True
        except Exception:
            return False

    def _try_price_twse(sym_code: str):
        """來源②：TWSE/TPEx 官方即時 API（mis.twse.com.tw）
        自動嘗試 tse（上市）與 otc（上櫃）；回傳 'tse'/'otc' 或 None。
        注意：休市時 z='-'，此時資料無效。
        """
        nonlocal price, prev, chg, pct
        try:
            for ex in ("tse", "otc"):
                r = requests.get(
                    "https://mis.twse.com.tw/stock/api/getStockInfo.jsp",
                    params={"ex_ch": f"{ex}_{sym_code}.tw", "json": "1", "delay": "0"},
                    timeout=6,
                    headers={"Referer": "https://mis.twse.com.tw/",
                             "User-Agent": "Mozilla/5.0"},
                )
                arr = r.json().get("msgArray", [])
                if not arr:
                    continue
                item = arr[0]
                z = item.get("z", "-")
                if z in ("-", "", None):
                    return None    # 休市；無即時報價
                p = _safe_float(z)
                if not p:
                    continue
                y      = _safe_float(item.get("y"))
                price  = p; prev = y or p
                chg    = price - prev
                pct    = chg / prev * 100 if prev else None
                return ex          # 'tse'=上市(.TW)  'otc'=上櫃(.TWO)
        except Exception:
            pass
        return None

    if is_tw:
        if not _try_price(symbol + ".TW"):
            twse_ex = _try_price_twse(symbol)
            if twse_ex is None and not price:
                if not _try_price_dl(symbol + ".TW"):
                    if _try_price(symbol + ".TWO"):
                        yf_sym = symbol + ".TWO"
                    elif _try_price_dl(symbol + ".TWO"):
                        yf_sym = symbol + ".TWO"
            elif twse_ex == "otc":
                yf_sym = symbol + ".TWO"
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

    # ── Step 4: 選股信號＋52週高低點（技術指標，獨立快取 5 min）──────
    is_tpex = yf_sym.endswith(".TWO")
    tech = fetch_technical(yf_sym, symbol, is_tw, is_tpex)

    # 52週高低點：優先用 fetch_technical 自行計算（252 天 OHLC，不依賴 Yahoo 預計算值）
    # 若 fetch_technical 無資料（如新股），才回退到 fast_info year_high/year_low
    low52  = tech.get("low52")  or getattr(yf.Ticker(yf_sym, session=_http_session()).fast_info, "year_low",  None)
    high52 = tech.get("high52") or getattr(yf.Ticker(yf_sym, session=_http_session()).fast_info, "year_high", None)
    low52  = _safe_float(low52)
    high52 = _safe_float(high52)
    pos    = (price - low52) / (high52 - low52) * 100 if (price and low52 and high52 and high52 > low52) else None

    # PE：若 fund 未取得，用 FinMind TTM EPS × 目前股價自行計算（獨立來源）
    if pe is None and fund.get("ttm_eps") and price:
        pe = round(price / fund["ttm_eps"], 1)
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
    C) income_stmt + market_cap — 計算 PE（自行算，timeseries API 較少被封鎖）
    D) upgrades_downgrades — 評估日 + 歷史追蹤家數
    E) recommendations_summary — 近期追蹤家數
    F) FinMind 季報 EPS — 台股 PE 獨立第三來源（與 Yahoo 完全獨立）
    """
    result = {
        "pe": None, "sector": "", "industry": "",
        "t_mean": None, "t_high": None, "t_low": None,
        "n_ana": None, "n_ana_recent": None, "n_ana_total": None,
        "shortName": "", "longName": "",
        "ana_date": None, "ana_date_src": None,
        "ttm_eps": None,   # FinMind TTM EPS，供 _fetch_one 計算 PE 用
    }

    # ── F: FinMind 季報 EPS（台股獨立 PE 來源，優先嘗試）────────────
    # 與 Yahoo Finance 完全獨立；PE = 目前股價 / TTM EPS（最近 4 季合計）
    is_tw_sym = yf_sym.endswith((".TW", ".TWO"))
    if is_tw_sym:
        try:
            tw_code  = symbol   # symbol 是純數字代號
            start_dt = (now_tw() - timedelta(days=420)).strftime("%Y-%m-%d")
            r = requests.get(
                "https://api.finmindtrade.com/api/v4/data",
                params={"dataset": "TaiwanStockFinancialStatements",
                        "data_id": tw_code, "start_date": start_dt},
                timeout=10,
            )
            data = r.json()
            if data.get("status") == 200:
                # 尋找 EPS 相關欄位（FinMind 欄位名稱可能為 EPS 或 BasicEPS）
                eps_rows = [
                    row for row in data.get("data", [])
                    if row.get("type") in ("EPS", "BasicEPS", "每股盈餘")
                ]
                if len(eps_rows) >= 4:
                    ttm = sum(_safe_float(r.get("value", 0)) or 0 for r in eps_rows[-4:])
                    if ttm > 0:
                        result["ttm_eps"] = ttm
        except Exception:
            pass

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
    查詢最近 5 個交易日融資餘額是否淨增加。雙來源：
    來源①：FinMind（TaiwanStockMarginPurchaseShortSale）
    來源②：TWSE/TPEx 官方 API（MI_MARGN，備援）
    回傳 True=增加 / False=減少或持平 / None=無資料
    """
    # ── 來源①：FinMind ──────────────────────────────────────────────
    try:
        start_date = (now_tw() - timedelta(days=14)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockMarginPurchaseShortSale",
                    "data_id": symbol, "start_date": start_date},
            timeout=8,
        )
        data = r.json()
        if data.get("status") == 200:
            rows = data.get("data", [])
            if rows and len(rows) >= 2:
                recent    = rows[-5:] if len(rows) >= 5 else rows
                first_bal = int(recent[0].get("MarginPurchaseTodayBalance", 0))
                last_bal  = int(recent[-1].get("MarginPurchaseTodayBalance", 0))
                return last_bal > first_bal
    except Exception:
        pass

    # ── 來源②：TWSE/TPEx 官方 API（備援）───────────────────────────
    try:
        today    = now_tw()
        date_str = today.strftime("%Y%m%d")
        if is_tpex:
            url = (f"https://www.tpex.org.tw/web/stock/margin_trading/"
                   f"margin_balance/margin_bal_result.php?"
                   f"l=zh-tw&d={today.strftime('%Y/%m/%d')}&s=0,asc&o=json")
        else:
            url = (f"https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?"
                   f"response=json&date={date_str}&selectType=STOCK")
        r2 = requests.get(url, timeout=8,
                          headers={"Referer": "https://www.twse.com.tw/"})
        raw = r2.json()
        # TWSE 格式：tables[0].data = [[代號, 名稱, ..., 融資今日餘額, ...], ...]
        tables = raw.get("tables", raw.get("data", []))
        if tables:
            rows2 = (tables[0].get("data", []) if isinstance(tables[0], dict)
                     else tables)
            for row in rows2:
                if isinstance(row, list) and len(row) > 6 and str(row[0]) == symbol:
                    # 欄位順序依 TWSE 回傳，融資今日餘額通常在 index 6
                    bal_today = _safe_float(str(row[6]).replace(",", ""))
                    bal_prev  = _safe_float(str(row[5]).replace(",", "")) if len(row) > 5 else None
                    if bal_today is not None and bal_prev is not None:
                        return bal_today > bal_prev
    except Exception:
        pass

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
        "low52":     None,    # 自行計算，不依賴 ticker.info 預計算值
        "high52":    None,
    }

    # ── ①③：下載252日歷史（一年）自行計算技術指標＋52週高低點 ────
    # 52週高低：從 OHLC 直接計算（公式法，非 Yahoo 預計算）
    # K值/MA：使用全部資料（更多歷史→KD 收斂更準確）
    try:
        hist = yf.download(
            yf_sym, period="252d", progress=False,
            auto_adjust=True, multi_level_index=False,
        )
        if hist.empty or len(hist) < 20:
            return result

        # 52週高低點（自行計算）
        result["low52"]  = float(hist["Low"].min())
        result["high52"] = float(hist["High"].max())

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

        # 台股名稱：渲染時直接查 TW_NAMES，確保不受快取影響
        display_name = TW_NAMES.get(sym, s["name"]) if s.get("is_tw") else s["name"]

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
            <div class="stk-name">{display_name}</div>
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

def _compact_edit_list(wl: list[str], key_prefix: str, save_fn, name_map: dict):
    """下拉選股 + 操作按鈕，保證手機可用。"""
    if not wl:
        return
    n = len(wl)
    lines = "　".join(
        f"<span style='white-space:nowrap'>{i+1}.&nbsp;<b>{sym}</b>&nbsp;"
        f"<span style='color:#64748b;font-size:0.8rem'>{name_map.get(sym,'')}</span></span>"
        for i, sym in enumerate(wl)
    )
    st.markdown(f"<div style='font-size:0.88rem;line-height:2;margin-bottom:4px'>{lines}</div>",
                unsafe_allow_html=True)
    sel_idx = st.selectbox(
        "選擇股票",
        options=list(range(n)),
        format_func=lambda i: f"{wl[i]}　{name_map.get(wl[i], '')}",
        label_visibility="collapsed",
        key=f"{key_prefix}sel",
    )
    b1, b2, b3 = st.columns(3)
    if b1.button("⬆ 上移", key=f"{key_prefix}up", use_container_width=True, disabled=(sel_idx == 0)):
        wl[sel_idx], wl[sel_idx-1] = wl[sel_idx-1], wl[sel_idx]
        save_fn(wl); st.rerun()
    if b2.button("⬇ 下移", key=f"{key_prefix}dn", use_container_width=True, disabled=(sel_idx == n-1)):
        wl[sel_idx], wl[sel_idx+1] = wl[sel_idx+1], wl[sel_idx]
        save_fn(wl); st.rerun()
    if b3.button("🗑 刪除", key=f"{key_prefix}rm", use_container_width=True):
        wl.pop(sel_idx); save_fn(wl); st.rerun()


# ════════════════════════════════════════════════════════════════
# ── 檢查表：資料抓取與計算 ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600, show_spinner=False)
def _fetch_ohlcv_for_checklist(yf_sym: str) -> dict:
    try:
        hist = yf.download(yf_sym, period="90d", progress=False,
                           auto_adjust=True, multi_level_index=False)
        if hist.empty or len(hist) < 20:
            return {}
        return {
            "close":  hist["Close"].tolist(),
            "open":   hist["Open"].tolist(),
            "high":   hist["High"].tolist(),
            "low":    hist["Low"].tolist(),
            "volume": hist["Volume"].tolist(),
        }
    except Exception:
        return {}


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_institutional_for_checklist(symbol: str) -> list:
    try:
        start_date = (now_tw() - timedelta(days=40)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockInstitutionalInvestorsBuySell",
                    "data_id": symbol, "start_date": start_date},
            timeout=10,
        )
        data = r.json()
        if data.get("status") == 200:
            return data.get("data", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_margin_for_checklist(symbol: str) -> list:
    try:
        start_date = (now_tw() - timedelta(days=40)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockMarginPurchaseShortSale",
                    "data_id": symbol, "start_date": start_date},
            timeout=10,
        )
        data = r.json()
        if data.get("status") == 200:
            return data.get("data", [])
    except Exception:
        pass
    return []


def _parse_institutional(rows: list) -> list:
    """整理三大法人原始資料成按日期排列的 list"""
    from collections import defaultdict
    by_date: dict = defaultdict(lambda: {"foreign": 0, "sitc": 0, "dealer": 0})
    for row in rows:
        d    = row.get("date", "")
        name = row.get("name", "")
        net  = int(row.get("buy", 0)) - int(row.get("sell", 0))
        if "外資" in name:
            by_date[d]["foreign"] = net
        elif "投信" in name:
            by_date[d]["sitc"] = net
        elif "自營" in name:
            by_date[d]["dealer"] = net
    result = []
    for date in sorted(by_date.keys()):
        v = by_date[date]
        result.append({
            "date": date,
            "foreign": v["foreign"], "sitc": v["sitc"], "dealer": v["dealer"],
            "total": v["foreign"] + v["sitc"] + v["dealer"],
        })
    return result


def calc_daily_checklist(symbol: str, is_tw: bool) -> dict:
    """計算 12 題每日檢查表"""
    yf_sym  = symbol + ".TW" if is_tw else symbol
    ohlcv   = _fetch_ohlcv_for_checklist(yf_sym)
    scores  = [0] * 12
    details = [""] * 12

    if not ohlcv or len(ohlcv.get("close", [])) < 20:
        return {"scores": scores, "total": 0, "conclusion": "無資料", "details": details}

    close  = ohlcv["close"];  open_ = ohlcv["open"]
    high   = ohlcv["high"];   low   = ohlcv["low"]
    volume = ohlcv["volume"]

    # ── A. 趨勢狀態 ─────────────────────────────────────────────────
    ma20 = sum(close[-20:]) / 20
    scores[0] = int(close[-1] > ma20)
    details[0] = f"收{close[-1]:.1f} MA20={ma20:.1f}"

    support = min(low[-15:-1]) if len(low) > 15 else min(low[:-1])
    scores[1] = int(close[-1] > support * 0.97)
    details[1] = f"支撐{support:.1f}"

    if len(high) >= 10:
        r_hi = (high[-1] + high[-2]) / 2; p_hi = (high[-5] + high[-6]) / 2
        r_lo = (low[-1]  + low[-2])  / 2; p_lo = (low[-5]  + low[-6])  / 2
        scores[2] = int(r_hi > p_hi and r_lo > p_lo)
    details[2] = "高低墊高" if scores[2] else "未墊高"

    # ── B. 籌碼狀態 ─────────────────────────────────────────────────
    if is_tw:
        inst_data   = _parse_institutional(_fetch_institutional_for_checklist(symbol))
        margin_rows = _fetch_margin_for_checklist(symbol)
    else:
        inst_data = []; margin_rows = []

    if inst_data:
        lt = inst_data[-1]["total"]
        scores[3] = int(lt > 0)
        details[3] = f"法人合計{lt:+,}"
    elif len(close) >= 5 and len(volume) >= 10:
        vol_avg = sum(volume[-10:-5]) / 5
        scores[3] = int(close[-1] > close[-5] and volume[-1] > vol_avg)
        details[3] = "量增價升" if scores[3] else "量價偏弱"
    else:
        details[3] = "無資料"

    if is_tw and margin_rows:
        bals = [int(r.get("MarginPurchaseTodayBalance", 0)) for r in margin_rows[-5:]]
        b2 = bals[-1] > bals[0] if len(bals) >= 2 else False
        scores[4] = int(b2)
        details[4] = f"融資{'增' if b2 else '減'}"
    elif not is_tw and len(close) >= 3 and len(volume) >= 6:
        vol_avg = sum(volume[-6:-3]) / 3
        b2 = not (close[-1] < close[-2] and volume[-1] > vol_avg * 1.5)
        scores[4] = int(b2)
        details[4] = "量縮整理" if b2 else "量增下跌"
    else:
        details[4] = "無資料"

    if is_tw and len(inst_data) >= 2:
        consec_neg = inst_data[-1]["total"] < 0 and inst_data[-2]["total"] < 0
        scores[5] = int(not consec_neg)
        details[5] = "連2日賣超" if consec_neg else "無連續惡化"
    elif not is_tw and len(close) >= 3 and len(volume) >= 6:
        vol_avg  = sum(volume[-6:-3]) / 3
        both_dn  = close[-1] < close[-2] < close[-3]
        vol_up   = volume[-1] > vol_avg and volume[-2] > vol_avg
        scores[5] = int(not (both_dn and vol_up))
        details[5] = "連跌量增" if (both_dn and vol_up) else "無惡化"
    else:
        scores[5] = 1
        details[5] = "無資料"

    # ── C. 關鍵法人 ─────────────────────────────────────────────────
    if inst_data:
        scores[6] = int(inst_data[-1]["foreign"] > 0)
        details[6] = f"外資{inst_data[-1]['foreign']:+,}"
    elif len(close) >= 10:
        ma5  = sum(close[-5:]) / 5
        ma10 = sum(close[-10:]) / 10
        scores[6] = int(ma5 > ma10)
        details[6] = "短均>中均" if scores[6] else "短均<中均"
    else:
        details[6] = "無資料"

    if len(inst_data) >= 3:
        nets    = [d["total"] for d in inst_data[-5:]]
        avg_abs = sum(abs(x) for x in nets[:-1]) / max(len(nets) - 1, 1)
        big_sell = nets[-1] < 0 and abs(nets[-1]) > max(avg_abs * 1.5, 1000)
        scores[7] = int(not big_sell)
        details[7] = f"大賣超{nets[-1]:,}" if big_sell else "無異常賣超"
    else:
        scores[7] = 1
        details[7] = "⚠️ 替代資料"

    if len(inst_data) >= 2:
        prev_net = inst_data[-2]["total"]; curr_net = inst_data[-1]["total"]
        flip = prev_net > 0 and curr_net < -abs(prev_net) * 0.5
        scores[8] = int(not flip)
        details[8] = f"轉空({curr_net:,})" if flip else "方向穩定"
    elif len(close) >= 9:
        ma5n = sum(close[-5:]) / 5; ma5p = sum(close[-6:-1]) / 5
        scores[8] = int(ma5n >= ma5p)
        details[8] = "均線穩" if scores[8] else "均線轉弱"
    else:
        scores[8] = 1
        details[8] = "無資料"

    # ── D. 量價健康度 ────────────────────────────────────────────────
    vol_ma5 = sum(volume[-6:-1]) / 5 if len(volume) >= 6 else sum(volume[-5:]) / 5
    is_up   = close[-1] >= close[-2] if len(close) >= 2 else True
    d1 = (volume[-1] >= vol_ma5 * 0.7) if is_up else (volume[-1] <= vol_ma5 * 1.5)
    scores[9] = int(d1)
    details[9] = f"量{'放大' if volume[-1] > vol_ma5 else '縮小'}({'漲' if is_up else '跌'})"

    is_big_vol = volume[-1] > vol_ma5 * 2.0
    if is_big_vol and open_[-1] > 0:
        body  = (open_[-1] - close[-1]) / open_[-1]
        stall = abs(close[-1] - open_[-1]) / open_[-1] < 0.005
        d2 = not (body > 0.02 or stall)
        details[10] = ("爆量長黑" if body > 0.02 else "爆量不漲") if not d2 else "量大尚可"
    else:
        d2 = True
        details[10] = "量能正常"
    scores[10] = int(d2)

    is_pb = close[-1] < close[-2] if len(close) >= 2 else False
    if is_pb:
        d3 = volume[-1] < vol_ma5 * 0.9
        details[11] = f"回檔量{'縮✓' if d3 else '未縮✗'}"
    else:
        d3 = True
        details[11] = "未拉回"
    scores[11] = int(d3)

    total = sum(scores)
    concl = "✅ 續抱" if total >= 9 else ("👀 觀察" if total >= 6 else "🔴 出場")
    return {"scores": scores, "total": total, "conclusion": concl, "details": details}


def calc_weekly_checklist(symbol: str, is_tw: bool) -> dict:
    """計算 12 題每週檢查表（以日線資料近似週線）"""
    yf_sym  = symbol + ".TW" if is_tw else symbol
    ohlcv   = _fetch_ohlcv_for_checklist(yf_sym)
    scores  = [0] * 12
    details = [""] * 12

    if not ohlcv or len(ohlcv.get("close", [])) < 20:
        return {"scores": scores, "total": 0, "conclusion": "無資料", "details": details}

    close  = ohlcv["close"];  high   = ohlcv["high"]
    low    = ohlcv["low"];    volume = ohlcv["volume"]
    n = len(close)

    # 週線近似：最近5日=本週, 5-10日前=上週
    wc0 = close[-1]
    wc1 = close[-5]  if n >= 5  else close[0]
    wc4 = close[-20] if n >= 20 else close[0]
    wh0 = max(high[-5:])    if n >= 5  else high[-1]
    wh4 = max(high[-20:])   if n >= 20 else wh0
    wv0 = sum(volume[-5:])  if n >= 5  else volume[-1]
    wv1 = sum(volume[-10:-5]) if n >= 10 else wv0
    wv4_avg = sum(volume[-20:]) / 4 if n >= 20 else wv0

    # ── A. 中期趨勢 ─────────────────────────────────────────────────
    if n >= 25:
        wma5 = (close[-1] + close[-5] + close[-10] + close[-15] + close[-20]) / 5
        scores[0] = int(wc0 > wma5 and wc0 > wc4)
        details[0] = f"週收{wc0:.1f} 5週均{wma5:.1f}"
    else:
        details[0] = "週資料不足"

    if n >= 60:
        ma20 = sum(close[-20:]) / 20; ma60 = sum(close[-60:]) / 60
        scores[1] = int(ma20 > ma60)
        details[1] = f"MA20={ma20:.1f} MA60={ma60:.1f}"
    elif n >= 20:
        ma20 = sum(close[-20:]) / 20; ma10 = sum(close[-10:]) / 10
        scores[1] = int(ma20 > ma10)
        details[1] = f"MA20={ma20:.1f}（替代MA60）"
    else:
        details[1] = "資料不足"

    if n >= 20:
        support = min(low[-20:-5]) if n > 25 else min(low[-20:])
        scores[2] = int(close[-1] > support * 0.97)
        details[2] = f"支撐{support:.1f}"
    else:
        details[2] = "資料不足"

    # ── B. 中期籌碼 ─────────────────────────────────────────────────
    if is_tw:
        inst_data   = _parse_institutional(_fetch_institutional_for_checklist(symbol))
        margin_rows = _fetch_margin_for_checklist(symbol)
    else:
        inst_data = []; margin_rows = []

    if inst_data:
        wk = inst_data[-5:] if len(inst_data) >= 5 else inst_data
        wk_total = sum(d["total"] for d in wk)
        scores[3] = int(wk_total > 0)
        details[3] = f"近5日法人{wk_total:+,}"
    elif n >= 10:
        vol_avg = sum(volume[-10:-5]) / 5
        scores[3] = int(close[-1] > close[-5] and volume[-1] > vol_avg)
        details[3] = "量增價升" if scores[3] else "量價偏弱"
    else:
        details[3] = "無資料"

    if is_tw and margin_rows:
        bals = [int(r.get("MarginPurchaseTodayBalance", 0)) for r in margin_rows[-10:]]
        if len(bals) >= 5:
            scores[4] = int(bals[-1] > bals[-5])
            details[4] = f"週融資{'增' if scores[4] else '減'}"
        else:
            details[4] = "無融資資料"
    elif not is_tw and n >= 10:
        up_days = sum(1 for i in range(-5, 0) if close[i] > close[i - 1])
        scores[4] = int(up_days >= 3)
        details[4] = f"近5日漲{up_days}天"
    else:
        details[4] = "無資料"

    if inst_data and len(inst_data) >= 3:
        consec = 0
        for d in reversed(inst_data):
            if d["total"] > 0:
                consec += 1
            else:
                break
        scores[5] = int(consec >= 2)
        details[5] = f"連續買超{consec}日"
    elif n >= 20:
        ma5n = sum(close[-5:]) / 5; ma5p = sum(close[-10:-5]) / 5
        scores[5] = int(ma5n > ma5p)
        details[5] = "MA5上升" if scores[5] else "MA5下降"
    else:
        details[5] = "無資料"

    # ── C. 關鍵券商延續性 ────────────────────────────────────────────
    if inst_data and len(inst_data) >= 5:
        recent = inst_data[-5:]
        f_pos = sum(1 for d in recent if d["foreign"] > 0)
        s_pos = sum(1 for d in recent if d["sitc"] > 0)
        scores[6] = int(f_pos >= 3 or s_pos >= 3)
        details[6] = f"外資買{f_pos}/5 投信買{s_pos}/5"
    elif n >= 20:
        ma5  = sum(close[-5:]) / 5
        ma10 = sum(close[-10:]) / 10
        ma20 = sum(close[-20:]) / 20
        scores[6] = int(ma5 > ma10 > ma20)
        details[6] = "均線多頭" if scores[6] else "均線非多頭"
    else:
        details[6] = "無資料"

    if inst_data and len(inst_data) >= 10:
        tw_s = sum(d["total"] for d in inst_data[-5:])
        lw_s = sum(d["total"] for d in inst_data[-10:-5])
        scores[7] = int(not (lw_s > 0 and tw_s < 0))
        details[7] = f"上週{lw_s:+,} 本週{tw_s:+,}"
    elif inst_data:
        scores[7] = 1
        details[7] = "資料不足略過"
    elif n >= 5:
        scores[7] = int(wc0 >= wc1)
        details[7] = f"週收{'升' if scores[7] else '降'}"
    else:
        details[7] = "無資料"

    if inst_data and len(inst_data) >= 3:
        recent = inst_data[-3:]
        s_pos = sum(1 for d in recent if d["sitc"] > 0)
        d_pos = sum(1 for d in recent if d["dealer"] > 0)
        scores[8] = int(s_pos >= 2 or d_pos >= 2)
        details[8] = f"投信/自營近3日正{max(s_pos, d_pos)}/3"
    elif n >= 10:
        vn = sum(volume[-5:]) / 5; vp = sum(volume[-10:-5]) / 5
        scores[8] = int(vn >= vp * 0.9)
        details[8] = "量能穩定" if scores[8] else "量能萎縮"
    else:
        scores[8] = 1
        details[8] = "無資料"

    # ── D. 量價與型態（週線近似）────────────────────────────────────
    scores[9] = int(not (wv0 > wv4_avg * 2.0 and wc0 < wc1))
    details[9] = f"週量{'爆出' if wv0 > wv4_avg * 2 else '正常'} 週{'漲' if wc0 >= wc1 else '跌'}"

    is_new_high = wh0 >= wh4
    if is_new_high:
        scores[10] = int(wv0 >= wv4_avg)
        details[10] = f"創高量{'配合' if scores[10] else '不足'}"
    else:
        scores[10] = 1
        details[10] = "未創高"

    if n >= 5 and wc0 < wc1:
        drop = (wc1 - wc0) / wc1 * 100
        ma20 = sum(close[-20:]) / 20 if n >= 20 else close[-1]
        scores[11] = int(drop < 5 and close[-1] > ma20 * 0.97)
        details[11] = f"回檔{drop:.1f}%{' 正常' if scores[11] else ' 偏大'}"
    else:
        scores[11] = 1
        details[11] = "未回檔"

    total = sum(scores)
    concl = "✅ 續抱" if total >= 9 else ("👀 觀察" if total >= 6 else "🔴 出場")
    return {"scores": scores, "total": total, "conclusion": concl, "details": details}


def load_checklist_from_gist(date_key: str, mode: str) -> dict:
    gid = _get_gist_id()
    if not gid:
        return {}
    try:
        hdrs = _gh_headers()
        r = requests.get(f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10)
        if r.ok:
            data = json.loads(r.json()["files"][_GIST_FILENAME]["content"])
            return data.get(f"_checklist_{mode}", {}).get(date_key, {})
    except Exception:
        pass
    return {}


def save_checklist_to_gist(date_key: str, mode: str, results: dict):
    gid = _get_gist_id()
    if not gid:
        return
    try:
        hdrs = _gh_headers()
        r    = requests.get(f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10)
        data = json.loads(r.json()["files"][_GIST_FILENAME]["content"]) if r.ok else {}
        cl_key = f"_checklist_{mode}"
        if cl_key not in data:
            data[cl_key] = {}
        data[cl_key][date_key] = results
        if len(data[cl_key]) > 7:
            for old in sorted(data[cl_key].keys())[:-7]:
                del data[cl_key][old]
        requests.patch(
            f"https://api.github.com/gists/{gid}", headers=hdrs, timeout=10,
            json={"files": {_GIST_FILENAME: {"content": json.dumps(data, ensure_ascii=False)}}}
        )
    except Exception:
        pass


def _render_checklist_results(results: dict, tw_list: list, us_list: list, is_daily: bool):
    labels = ([
        "A1 站20MA上", "A2 未跌支撐", "A3 高低墊高",
        "B1 主力偏多", "B2 籌碼未散", "B3 無連惡化",
        "C1 外資買",   "C2 無倒貨",   "C3 方向穩",
        "D1 量價健康", "D2 無爆量黑", "D3 拉回量縮",
    ] if is_daily else [
        "A1 週線升趨", "A2 均線多頭", "A3 守住支撐",
        "B1 週法人正", "B2 籌碼週增", "B3 籌碼集中",
        "C1 法人連偏多", "C2 未轉賣", "C3 投信續買",
        "D1 週量健康", "D2 創高量配", "D3 回檔正常",
    ])

    rows_html = ""
    for sym in list(tw_list) + list(us_list):
        if sym not in results:
            continue
        r       = results[sym]
        scores  = r.get("scores", [0] * 12)
        total   = r.get("total", 0)
        concl   = r.get("conclusion", "—")
        name    = TW_NAMES.get(sym, sym)
        cc, cb  = (("#059669", "#d1fae5") if total >= 9
                   else ("#d97706", "#fef3c7") if total >= 6
                   else ("#dc2626", "#fee2e2"))
        dot_a = "".join("🟢" if scores[i] else "🔴" for i in range(0, 3))
        dot_b = "".join("🟢" if scores[i] else "🔴" for i in range(3, 6))
        dot_c = "".join("🟢" if scores[i] else "🔴" for i in range(6, 9))
        dot_d = "".join("🟢" if scores[i] else "🔴" for i in range(9, 12))
        rows_html += f"""<tr>
          <td class="left">
            <div class="stk-code">{sym}</div>
            <div class="stk-name">{name}</div>
          </td>
          <td style="text-align:center">
            <span style="font-size:1.1rem;font-weight:800;color:{cc};
                         background:{cb};padding:3px 10px;border-radius:20px">{total}/12</span>
          </td>
          <td style="text-align:center;font-weight:700;color:{cc}">{concl}</td>
          <td style="text-align:center;font-size:0.85rem;letter-spacing:1px">{dot_a}</td>
          <td style="text-align:center;font-size:0.85rem;letter-spacing:1px">{dot_b}</td>
          <td style="text-align:center;font-size:0.85rem;letter-spacing:1px">{dot_c}</td>
          <td style="text-align:center;font-size:0.85rem;letter-spacing:1px">{dot_d}</td>
        </tr>"""

    st.html(f"""
    <div class="wl-wrap">
    <table class="wl-table">
      <thead><tr>
        <th class="left">股票</th><th>得分</th><th>結論</th>
        <th>A 趨勢</th><th>B 籌碼</th><th>C 法人</th><th>D 量價</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table></div>""")

    with st.expander("📝 各題明細"):
        syms_with_data = [s for s in list(tw_list) + list(us_list) if s in results]
        if syms_with_data:
            tab_names   = [f"{s} {TW_NAMES.get(s, s)}" for s in syms_with_data]
            detail_tabs = st.tabs(tab_names)
            for dtab, sym in zip(detail_tabs, syms_with_data):
                with dtab:
                    r       = results[sym]
                    sc_list = r.get("scores", [0] * 12)
                    det     = r.get("details", [""] * 12)
                    cols    = st.columns(3)
                    for i, (lbl, sc, dv) in enumerate(zip(labels, sc_list, det)):
                        cols[i % 3].markdown(
                            f"{'🟢' if sc else '🔴'} **{lbl}**<br>"
                            f"<span style='font-size:0.82rem;color:#64748b'>{dv}</span>",
                            unsafe_allow_html=True,
                        )


def _render_checklist_mode(tw_list: list, us_list: list, mode_key: str):
    today    = now_tw()
    is_daily = (mode_key == "daily")

    if is_daily:
        date_key   = today.strftime("%Y-%m-%d")
        sched_info = "⏰ 自動執行：台股 平日 14:00 ／ 美股 平日 07:00（台灣時間）"
    else:
        iso      = today.isocalendar()
        date_key = f"{iso[0]}-W{iso[1]:02d}"
        sched_info = "⏰ 自動執行：每週六 09:00（台灣時間）"

    ss_key = f"cl_{mode_key}_{date_key}"
    if ss_key not in st.session_state:
        st.session_state[ss_key] = load_checklist_from_gist(date_key, mode_key)
    cached = st.session_state[ss_key]

    c_btn, c_info = st.columns([2, 4])
    with c_btn:
        run_btn = st.button("▶ 手動執行檢查", type="primary",
                            use_container_width=True, key=f"cl_run_{mode_key}")
    with c_info:
        if cached:
            first = next(iter(cached), None)
            upd   = cached.get(first, {}).get("updated", "") if first else ""
            st.caption(f"上次更新：{upd}　{date_key}")
        else:
            st.caption("尚無資料")
        st.caption(sched_info)

    if run_btn:
        all_syms = [(s, True) for s in tw_list] + [(s, False) for s in us_list]
        results  = {}
        upd_time = today.strftime("%H:%M")
        prog     = st.progress(0, text="準備計算…")
        for i, (sym, is_tw_sym) in enumerate(all_syms):
            prog.progress((i + 0.5) / len(all_syms), text=f"計算 {sym}（{i+1}/{len(all_syms)}）…")
            try:
                r = (calc_daily_checklist(sym, is_tw_sym)
                     if is_daily else calc_weekly_checklist(sym, is_tw_sym))
                r["updated"] = upd_time
                results[sym] = r
            except Exception as e:
                results[sym] = {"scores": [0]*12, "total": 0, "conclusion": "錯誤",
                                "details": [str(e)]*12, "updated": upd_time}
            if is_tw_sym:
                time.sleep(0.5)
        prog.empty()
        save_checklist_to_gist(date_key, mode_key, results)
        st.session_state[ss_key] = results
        cached = results
        st.success(f"✅ 計算完成（{len(results)} 支）")

    if cached:
        _render_checklist_results(cached, tw_list, us_list, is_daily)
    else:
        st.info("尚無資料。GitHub Actions 會依排程自動執行，或點「▶ 手動執行檢查」。")
        st.markdown("""
<div style="background:#f8fbff;border:1px solid #bfdbfe;border-radius:12px;
            padding:16px;margin-top:12px">
  <div style="font-weight:700;color:#1e40af;margin-bottom:8px">📊 評分說明（每日/每週各 12 題）</div>
  <div style="display:flex;gap:12px;flex-wrap:wrap">
    <span style="background:#d1fae5;border:1px solid #6ee7b7;padding:4px 12px;
                 border-radius:20px;color:#065f46;font-weight:700">✅ 9–12 分：續抱</span>
    <span style="background:#fef3c7;border:1px solid #fcd34d;padding:4px 12px;
                 border-radius:20px;color:#92400e;font-weight:700">👀 6–8 分：觀察</span>
    <span style="background:#fee2e2;border:1px solid #fca5a5;padding:4px 12px;
                 border-radius:20px;color:#991b1b;font-weight:700">🔴 0–5 分：優先出場</span>
  </div>
  <div style="margin-top:8px;font-size:0.86rem;color:#64748b">
    A=趨勢 B=籌碼 C=關鍵法人 D=量價　｜　美股 B 類使用量價替代
  </div>
</div>""", unsafe_allow_html=True)


def render_checklist_tab(tw_list: list, us_list: list):
    tab_d, tab_w = st.tabs(["📅 每日檢查", "📆 每週檢查"])
    with tab_d:
        _render_checklist_mode(tw_list, us_list, "daily")
    with tab_w:
        _render_checklist_mode(tw_list, us_list, "weekly")


# ════════════════════════════════════════════════════════════════
def main():
    # ── 初始化 session state ──
    if "tw_list" not in st.session_state or "us_list" not in st.session_state:
        tw, us, key = load_watchlists()
        st.session_state.tw_list    = tw
        st.session_state.us_list    = us
        st.session_state.profile_key = key
        if key:
            _tw_raw = st.query_params.get("tw", "")
            _us_raw = st.query_params.get("us", "")
            if _tw_raw and _us_raw:
                # URL 帶了明確清單 → 強制更新 profile（覆蓋舊的）
                save_profile(key, tw, us)
            elif load_profile(key)[0] is None:
                # 新 profile → 以目前清單建立
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
    with st.expander("🌐 全球經濟指標", expanded=False):
        with st.spinner("載入全球指標…"):
            global_data = fetch_global()
        render_global(global_data)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ══ 編輯清單 ／ 跨裝置同步（tabs）══════════════════════════════
    cur_key = st.session_state.get("profile_key", "")
    sync_tab_label = f"🔗 同步　✅{cur_key}" if cur_key else "🔗 跨裝置同步"
    tab_edit, tab_sync = st.tabs(["✏️ 編輯清單", sync_tab_label])

    with tab_edit:
        ea1, ea2, ea3 = st.columns([3, 1, 1])
        add_code = ea1.text_input(
            "股票代號", placeholder="台股：2330　美股：NVDA",
            label_visibility="collapsed", key="tab_add_input"
        )
        if ea2.button("＋台股", key="tab_add_tw", use_container_width=True):
            code = add_code.strip().upper()
            if code and code not in tw_list:
                tw_list.append(code); save_tw(tw_list)
                fetch_stocks_batch.clear(); st.rerun()
            elif code in tw_list:
                st.warning(f"{code} 已在台股清單")
        if ea3.button("＋美股", key="tab_add_us", use_container_width=True):
            code = add_code.strip().upper()
            if code and code not in us_list:
                us_list.append(code); save_us(us_list)
                fetch_stocks_batch.clear(); st.rerun()
            elif code in us_list:
                st.warning(f"{code} 已在美股清單")
        if tw_list:
            st.markdown("**🇹🇼 台股**")
            _compact_edit_list(tw_list, "te_tw_", save_tw, TW_NAMES)
        if us_list:
            st.markdown("**🇺🇸 美股**")
            _compact_edit_list(us_list, "te_us_", save_us, {})

    with tab_sync:
        st.markdown("電腦和手機輸入**相同代號**，清單自動同步。改了一台後，另一台點「拉取更新」即可。")
        sc1, sc2, sc3 = st.columns([3, 1, 1])
        key_input = sc1.text_input(
            "同步代號", value=cur_key,
            placeholder="自訂代號，例如 mystock88",
            label_visibility="collapsed", key="tab_sync_key_input",
        )
        if sc2.button("套用", key="tab_sync_apply", use_container_width=True):
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
        if sc3.button("拉取更新", key="tab_sync_pull",
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
            st.caption(f"上次同步：{ts}　｜　書籤請含 ?key={cur_key}")

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

    # ── 台股 / 美股 tabs ──
    tab_tw, tab_us, tab_cl = st.tabs([
        f"🇹🇼 台股（{len(tw_list)} 支）",
        f"🇺🇸 美股（{len(us_list)} 支）",
        "📋 檢查表",
    ])
    with tab_tw:
        if tw_list:
            with st.spinner("載入台股資料…"):
                tw_stocks = fetch_stocks_batch(tuple(tw_list))
            render_watchlist(tw_stocks)
        else:
            st.info("台股清單是空的，請在「✏️ 編輯清單」新增。")
    with tab_us:
        if us_list:
            with st.spinner("載入美股資料…"):
                us_stocks = fetch_stocks_batch(tuple(us_list))
            render_watchlist(us_stocks)
        else:
            st.info("美股清單是空的，請在「✏️ 編輯清單」新增。")
    with tab_cl:
        render_checklist_tab(tw_list, us_list)

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
