#!/usr/bin/env python3
"""
自動化每日/每週檢查表計算腳本（GitHub Actions 使用）
結果存入 GitHub Gist，Streamlit app 開啟時自動讀取

用法：
  python run_checklist.py --mode daily  --market tw
  python run_checklist.py --mode daily  --market us
  python run_checklist.py --mode weekly --market all
"""
import argparse, json, os, sys, time, requests
import yfinance as yf
from datetime import datetime, timezone, timedelta
from collections import defaultdict

TW_TZ = timezone(timedelta(hours=8))
def now_tw(): return datetime.now(TW_TZ)

GIST_TOKEN    = os.environ.get("GIST_TOKEN", "")
PROFILE_KEY   = os.environ.get("PROFILE_KEY", "")
GIST_FILENAME = "stock-dashboard-profiles.json"
DEFAULT_TW    = ["2330", "2317", "2454", "2382"]
DEFAULT_US    = ["NVDA", "AAPL"]


# ── Gist 工具 ──────────────────────────────────────────────────────
def _gh():
    return {"Authorization": f"token {GIST_TOKEN}",
            "Accept": "application/vnd.github.v3+json"}

def get_gist_id():
    r = requests.get("https://api.github.com/gists", headers=_gh(), timeout=10)
    if r.ok:
        for g in r.json():
            if GIST_FILENAME in g.get("files", {}):
                return g["id"]
    return None

def load_gist(gist_id):
    r = requests.get(f"https://api.github.com/gists/{gist_id}",
                     headers=_gh(), timeout=10)
    if r.ok:
        return json.loads(r.json()["files"][GIST_FILENAME]["content"])
    return {}

def save_gist(gist_id, data):
    requests.patch(
        f"https://api.github.com/gists/{gist_id}", headers=_gh(), timeout=15,
        json={"files": {GIST_FILENAME: {"content": json.dumps(data, ensure_ascii=False)}}}
    )

def get_watchlist(data):
    if PROFILE_KEY and PROFILE_KEY in data:
        return (data[PROFILE_KEY].get("tw", DEFAULT_TW),
                data[PROFILE_KEY].get("us", DEFAULT_US))
    return DEFAULT_TW, DEFAULT_US


# ── 資料抓取（無 Streamlit cache）────────────────────────────────────
def fetch_ohlcv(yf_sym):
    try:
        hist = yf.download(yf_sym, period="90d", progress=False,
                           auto_adjust=True, multi_level_index=False)
        if hist.empty or len(hist) < 20:
            return {}
        return {"close": hist["Close"].tolist(), "open": hist["Open"].tolist(),
                "high":  hist["High"].tolist(),  "low":  hist["Low"].tolist(),
                "volume": hist["Volume"].tolist()}
    except Exception:
        return {}

def fetch_institutional(symbol):
    try:
        start = (now_tw() - timedelta(days=40)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockInstitutionalInvestorsBuySell",
                    "data_id": symbol, "start_date": start},
            timeout=10,
        )
        d = r.json()
        if d.get("status") == 200:
            return d.get("data", [])
    except Exception:
        pass
    return []

def fetch_margin(symbol):
    try:
        start = (now_tw() - timedelta(days=40)).strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.finmindtrade.com/api/v4/data",
            params={"dataset": "TaiwanStockMarginPurchaseShortSale",
                    "data_id": symbol, "start_date": start},
            timeout=10,
        )
        d = r.json()
        if d.get("status") == 200:
            return d.get("data", [])
    except Exception:
        pass
    return []

def parse_institutional(rows):
    by_date = defaultdict(lambda: {"foreign": 0, "sitc": 0, "dealer": 0})
    for row in rows:
        d    = row.get("date", "")
        name = row.get("name", "")
        net  = int(row.get("buy", 0)) - int(row.get("sell", 0))
        if "外資" in name:   by_date[d]["foreign"] = net
        elif "投信" in name: by_date[d]["sitc"]    = net
        elif "自營" in name: by_date[d]["dealer"]  = net
    result = []
    for date in sorted(by_date.keys()):
        v = by_date[date]
        result.append({"date": date,
                       "foreign": v["foreign"], "sitc": v["sitc"], "dealer": v["dealer"],
                       "total": v["foreign"] + v["sitc"] + v["dealer"]})
    return result


# ── 每日計算（邏輯與 dashboard.py 完全相同）──────────────────────────
def calc_daily(symbol, is_tw):
    yf_sym  = symbol + ".TW" if is_tw else symbol
    ohlcv   = fetch_ohlcv(yf_sym)
    scores  = [0] * 12
    details = [""] * 12

    if not ohlcv or len(ohlcv.get("close", [])) < 20:
        return {"scores": scores, "total": 0, "conclusion": "無資料", "details": details}

    close  = ohlcv["close"];  open_ = ohlcv["open"]
    high   = ohlcv["high"];   low   = ohlcv["low"];  volume = ohlcv["volume"]

    # A
    ma20 = sum(close[-20:]) / 20
    scores[0] = int(close[-1] > ma20); details[0] = f"收{close[-1]:.1f} MA20={ma20:.1f}"
    support = min(low[-15:-1]) if len(low) > 15 else min(low[:-1])
    scores[1] = int(close[-1] > support * 0.97); details[1] = f"支撐{support:.1f}"
    if len(high) >= 10:
        r_hi = (high[-1]+high[-2])/2; p_hi = (high[-5]+high[-6])/2
        r_lo = (low[-1]+low[-2])/2;   p_lo = (low[-5]+low[-6])/2
        scores[2] = int(r_hi > p_hi and r_lo > p_lo)
    details[2] = "高低墊高" if scores[2] else "未墊高"

    # B
    if is_tw:
        inst_data   = parse_institutional(fetch_institutional(symbol))
        margin_rows = fetch_margin(symbol)
    else:
        inst_data = []; margin_rows = []

    if inst_data:
        lt = inst_data[-1]["total"]; scores[3] = int(lt > 0); details[3] = f"法人{lt:+,}"
    elif len(close) >= 5 and len(volume) >= 10:
        vol_avg = sum(volume[-10:-5]) / 5
        scores[3] = int(close[-1] > close[-5] and volume[-1] > vol_avg)
        details[3] = "量增價升" if scores[3] else "量價偏弱"
    else:
        details[3] = "無資料"

    if is_tw and margin_rows:
        bals = [int(r.get("MarginPurchaseTodayBalance", 0)) for r in margin_rows[-5:]]
        b2 = bals[-1] > bals[0] if len(bals) >= 2 else False
        scores[4] = int(b2); details[4] = f"融資{'增' if b2 else '減'}"
    elif not is_tw and len(close) >= 3 and len(volume) >= 6:
        vol_avg = sum(volume[-6:-3]) / 3
        b2 = not (close[-1] < close[-2] and volume[-1] > vol_avg * 1.5)
        scores[4] = int(b2); details[4] = "量縮整理" if b2 else "量增下跌"
    else:
        details[4] = "無資料"

    if is_tw and len(inst_data) >= 2:
        cn = inst_data[-1]["total"] < 0 and inst_data[-2]["total"] < 0
        scores[5] = int(not cn); details[5] = "連2日賣超" if cn else "無連續惡化"
    elif not is_tw and len(close) >= 3 and len(volume) >= 6:
        vol_avg = sum(volume[-6:-3]) / 3
        both_dn = close[-1] < close[-2] < close[-3]
        vol_up  = volume[-1] > vol_avg and volume[-2] > vol_avg
        scores[5] = int(not (both_dn and vol_up))
        details[5] = "連跌量增" if (both_dn and vol_up) else "無惡化"
    else:
        scores[5] = 1; details[5] = "無資料"

    # C
    if inst_data:
        scores[6] = int(inst_data[-1]["foreign"] > 0)
        details[6] = f"外資{inst_data[-1]['foreign']:+,}"
    elif len(close) >= 10:
        ma5 = sum(close[-5:])/5; ma10 = sum(close[-10:])/10
        scores[6] = int(ma5 > ma10); details[6] = "短均>中均" if scores[6] else "短均<中均"
    else:
        details[6] = "無資料"

    if len(inst_data) >= 3:
        nets    = [d["total"] for d in inst_data[-5:]]
        avg_abs = sum(abs(x) for x in nets[:-1]) / max(len(nets)-1, 1)
        big_sell = nets[-1] < 0 and abs(nets[-1]) > max(avg_abs*1.5, 1000)
        scores[7] = int(not big_sell)
        details[7] = f"大賣超{nets[-1]:,}" if big_sell else "無異常"
    else:
        scores[7] = 1; details[7] = "替代資料"

    if len(inst_data) >= 2:
        p = inst_data[-2]["total"]; c = inst_data[-1]["total"]
        flip = p > 0 and c < -abs(p)*0.5
        scores[8] = int(not flip); details[8] = f"轉空({c:,})" if flip else "方向穩"
    elif len(close) >= 9:
        ma5n = sum(close[-5:])/5; ma5p = sum(close[-6:-1])/5
        scores[8] = int(ma5n >= ma5p); details[8] = "均線穩" if scores[8] else "均線轉弱"
    else:
        scores[8] = 1; details[8] = "無資料"

    # D
    vol_ma5 = sum(volume[-6:-1])/5 if len(volume) >= 6 else sum(volume[-5:])/5
    is_up   = close[-1] >= close[-2] if len(close) >= 2 else True
    d1 = (volume[-1] >= vol_ma5*0.7) if is_up else (volume[-1] <= vol_ma5*1.5)
    scores[9] = int(d1)
    details[9] = f"量{'放大' if volume[-1]>vol_ma5 else '縮小'}({'漲' if is_up else '跌'})"

    is_big = volume[-1] > vol_ma5 * 2.0
    if is_big and open_[-1] > 0:
        body  = (open_[-1] - close[-1]) / open_[-1]
        stall = abs(close[-1] - open_[-1]) / open_[-1] < 0.005
        d2    = not (body > 0.02 or stall)
        details[10] = ("爆量長黑" if body > 0.02 else "爆量不漲") if not d2 else "量大尚可"
    else:
        d2 = True; details[10] = "量能正常"
    scores[10] = int(d2)

    is_pb = close[-1] < close[-2] if len(close) >= 2 else False
    if is_pb:
        d3 = volume[-1] < vol_ma5 * 0.9
        details[11] = f"回檔量{'縮✓' if d3 else '未縮✗'}"
    else:
        d3 = True; details[11] = "未拉回"
    scores[11] = int(d3)

    total = sum(scores)
    concl = "✅ 續抱" if total >= 9 else ("👀 觀察" if total >= 6 else "🔴 出場")
    return {"scores": scores, "total": total, "conclusion": concl, "details": details}


# ── 每週計算 ────────────────────────────────────────────────────────
def calc_weekly(symbol, is_tw):
    yf_sym = symbol + ".TW" if is_tw else symbol
    ohlcv  = fetch_ohlcv(yf_sym)
    scores = [0] * 12; details = [""] * 12

    if not ohlcv or len(ohlcv.get("close", [])) < 20:
        return {"scores": scores, "total": 0, "conclusion": "無資料", "details": details}

    close = ohlcv["close"]; high = ohlcv["high"]
    low   = ohlcv["low"];   volume = ohlcv["volume"]; n = len(close)

    wc0 = close[-1]; wc1 = close[-5] if n >= 5 else close[0]
    wh0 = max(high[-5:]) if n >= 5 else high[-1]
    wh4 = max(high[-20:]) if n >= 20 else wh0
    wv0 = sum(volume[-5:]) if n >= 5 else volume[-1]
    wv4_avg = sum(volume[-20:]) / 4 if n >= 20 else wv0

    # A
    if n >= 25:
        wma5 = (close[-1]+close[-5]+close[-10]+close[-15]+close[-20]) / 5
        scores[0] = int(wc0 > wma5 and wc0 > (close[-20] if n >= 20 else close[0]))
        details[0] = f"週收{wc0:.1f} 5週均{wma5:.1f}"
    else:
        details[0] = "週資料不足"

    if n >= 60:
        ma20 = sum(close[-20:])/20; ma60 = sum(close[-60:])/60
        scores[1] = int(ma20 > ma60); details[1] = f"MA20={ma20:.1f} MA60={ma60:.1f}"
    elif n >= 20:
        ma20 = sum(close[-20:])/20; ma10 = sum(close[-10:])/10
        scores[1] = int(ma20 > ma10); details[1] = f"MA20={ma20:.1f}"
    else:
        details[1] = "資料不足"

    if n >= 20:
        sup = min(low[-20:-5]) if n > 25 else min(low[-20:])
        scores[2] = int(close[-1] > sup * 0.97); details[2] = f"支撐{sup:.1f}"
    else:
        details[2] = "資料不足"

    # B
    if is_tw:
        inst_data   = parse_institutional(fetch_institutional(symbol))
        margin_rows = fetch_margin(symbol)
    else:
        inst_data = []; margin_rows = []

    if inst_data:
        wk = inst_data[-5:] if len(inst_data) >= 5 else inst_data
        wt = sum(d["total"] for d in wk)
        scores[3] = int(wt > 0); details[3] = f"近5日法人{wt:+,}"
    elif n >= 10:
        vol_avg = sum(volume[-10:-5]) / 5
        scores[3] = int(close[-1] > close[-5] and volume[-1] > vol_avg)
        details[3] = "量增價升" if scores[3] else "量價偏弱"
    else:
        details[3] = "無資料"

    if is_tw and margin_rows:
        bals = [int(r.get("MarginPurchaseTodayBalance", 0)) for r in margin_rows[-10:]]
        if len(bals) >= 5:
            scores[4] = int(bals[-1] > bals[-5]); details[4] = f"週融資{'增' if scores[4] else '減'}"
        else:
            details[4] = "無融資資料"
    elif not is_tw and n >= 10:
        up = sum(1 for i in range(-5, 0) if close[i] > close[i-1])
        scores[4] = int(up >= 3); details[4] = f"近5日漲{up}天"
    else:
        details[4] = "無資料"

    if inst_data and len(inst_data) >= 3:
        consec = 0
        for d in reversed(inst_data):
            if d["total"] > 0: consec += 1
            else: break
        scores[5] = int(consec >= 2); details[5] = f"連續買超{consec}日"
    elif n >= 20:
        ma5n = sum(close[-5:])/5; ma5p = sum(close[-10:-5])/5
        scores[5] = int(ma5n > ma5p); details[5] = "MA5上升" if scores[5] else "MA5下降"
    else:
        details[5] = "無資料"

    # C
    if inst_data and len(inst_data) >= 5:
        rec = inst_data[-5:]
        fp = sum(1 for d in rec if d["foreign"] > 0)
        sp = sum(1 for d in rec if d["sitc"] > 0)
        scores[6] = int(fp >= 3 or sp >= 3); details[6] = f"外資買{fp}/5 投信買{sp}/5"
    elif n >= 20:
        ma5  = sum(close[-5:])/5; ma10 = sum(close[-10:])/10; ma20 = sum(close[-20:])/20
        scores[6] = int(ma5 > ma10 > ma20); details[6] = "均線多頭" if scores[6] else "均線非多頭"
    else:
        details[6] = "無資料"

    if inst_data and len(inst_data) >= 10:
        tw_s = sum(d["total"] for d in inst_data[-5:])
        lw_s = sum(d["total"] for d in inst_data[-10:-5])
        scores[7] = int(not (lw_s > 0 and tw_s < 0)); details[7] = f"上週{lw_s:+,} 本週{tw_s:+,}"
    elif inst_data:
        scores[7] = 1; details[7] = "資料不足略過"
    elif n >= 5:
        scores[7] = int(wc0 >= wc1); details[7] = f"週收{'升' if scores[7] else '降'}"
    else:
        details[7] = "無資料"

    if inst_data and len(inst_data) >= 3:
        rec = inst_data[-3:]
        sp = sum(1 for d in rec if d["sitc"] > 0)
        dp = sum(1 for d in rec if d["dealer"] > 0)
        scores[8] = int(sp >= 2 or dp >= 2); details[8] = f"投信/自營近3日正{max(sp,dp)}/3"
    elif n >= 10:
        vn = sum(volume[-5:])/5; vp = sum(volume[-10:-5])/5
        scores[8] = int(vn >= vp*0.9); details[8] = "量能穩定" if scores[8] else "量能萎縮"
    else:
        scores[8] = 1; details[8] = "無資料"

    # D
    scores[9] = int(not (wv0 > wv4_avg*2.0 and wc0 < wc1))
    details[9] = f"週量{'爆出' if wv0>wv4_avg*2 else '正常'} 週{'漲' if wc0>=wc1 else '跌'}"

    if wh0 >= wh4:
        scores[10] = int(wv0 >= wv4_avg); details[10] = f"創高量{'配合' if scores[10] else '不足'}"
    else:
        scores[10] = 1; details[10] = "未創高"

    if n >= 5 and wc0 < wc1:
        drop = (wc1 - wc0) / wc1 * 100
        ma20 = sum(close[-20:])/20 if n >= 20 else close[-1]
        scores[11] = int(drop < 5 and close[-1] > ma20*0.97)
        details[11] = f"回檔{drop:.1f}%{' 正常' if scores[11] else ' 偏大'}"
    else:
        scores[11] = 1; details[11] = "未回檔"

    total = sum(scores)
    concl = "✅ 續抱" if total >= 9 else ("👀 觀察" if total >= 6 else "🔴 出場")
    return {"scores": scores, "total": total, "conclusion": concl, "details": details}


# ── 主程式 ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="自動化檢查表計算")
    parser.add_argument("--mode",   choices=["daily", "weekly"], required=True)
    parser.add_argument("--market", choices=["tw", "us", "all"], required=True)
    args = parser.parse_args()

    if not GIST_TOKEN:
        print("❌ 請設定環境變數 GIST_TOKEN"); sys.exit(1)

    print(f"▶ 模式：{args.mode}  市場：{args.market}")
    print(f"  台灣時間：{now_tw().strftime('%Y-%m-%d %H:%M')}")

    gist_id = get_gist_id()
    if not gist_id:
        print("❌ 找不到 Gist，請確認 GIST_TOKEN 有 gist 權限"); sys.exit(1)
    print(f"  Gist ID：{gist_id}")

    data = load_gist(gist_id)
    tw_list, us_list = get_watchlist(data)
    print(f"  台股：{tw_list}")
    print(f"  美股：{us_list}")

    syms_tw = [(s, True)  for s in tw_list] if args.market in ("tw", "all") else []
    syms_us = [(s, False) for s in us_list] if args.market in ("us", "all") else []
    all_syms = syms_tw + syms_us

    today = now_tw()
    date_key = (today.strftime("%Y-%m-%d") if args.mode == "daily"
                else f"{today.isocalendar()[0]}-W{today.isocalendar()[1]:02d}")

    cl_key = f"_checklist_{args.mode}"
    if cl_key not in data:
        data[cl_key] = {}

    results  = data[cl_key].get(date_key, {})
    upd_time = today.strftime("%H:%M")

    for sym, is_tw in all_syms:
        print(f"  計算 {sym}...", end=" ", flush=True)
        try:
            r = calc_daily(sym, is_tw) if args.mode == "daily" else calc_weekly(sym, is_tw)
            r["updated"] = upd_time
            results[sym] = r
            print(f"{r['total']}/12 {r['conclusion']}")
        except Exception as e:
            print(f"❌ {e}")
        if is_tw:
            time.sleep(0.8)

    data[cl_key][date_key] = results
    if len(data[cl_key]) > 7:
        for old in sorted(data[cl_key].keys())[:-7]:
            del data[cl_key][old]

    save_gist(gist_id, data)
    print(f"\n✅ 完成！{len(results)} 支股票已存入 Gist（{date_key}）")


if __name__ == "__main__":
    main()
