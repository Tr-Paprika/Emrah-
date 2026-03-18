"""
╔══════════════════════════════════════════════════════════════════╗
║          PAPRIKA ELİTE TERMİNAL  v6.0  (Düzeltilmiş)           ║
║──────────────────────────────────────────────────────────────────║
║  Kurulum:                                                        ║
║    pip install streamlit yfinance requests pandas numpy          ║
║    pip install streamlit-autorefresh                             ║
║                                                                  ║
║  Çalıştır:                                                       ║
║    streamlit run paprika_terminal_v6.py                          ║
║                                                                  ║
║  Veri Kaynakları:                                                ║
║   • Hisse / BIST100 : yfinance (Yahoo Finance, ~15dk gecikme)   ║
║   • Döviz / Altın   : TCMB Resmi XML (anlık)                    ║
║   • Kripto          : CoinGecko (anlık, key yok)                 ║
║   • Petrol          : yfinance BZ=F                              ║
║   • Haberler        : Google News RSS (XML, ücretsiz)            ║
║   • Duygu Endeksi   : RSI/MACD/Hacim bazlı hesaplanmış           ║
╚══════════════════════════════════════════════════════════════════╝

DÜZELTMELER (v6.0 → v6.0-fix):
  [1] top10_analiz: macd NameError → macd_son değişkeni ile kapsam düzeltildi
  [2] top10_analiz: dip_pct NameError → varsayılan 50.0 ile başlatıldı
  [3] haber_duyarlilik_skoru: 40 senkron HTTP → ThreadPoolExecutor(max_workers=8)
  [4] fp_radar: dip_uzaklik NameError → varsayılan 50.0 ile başlatıldı
  [5] st_autorefresh eksikse st.warning ile kullanıcı bilgilendiriliyor
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import html as html_mod

# ── SAYFA ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Paprika Elite Terminal", layout="wide",
                   initial_sidebar_state="collapsed")

# [DÜZELTME 5] Autorefresh eksikse kullanıcıyı bilgilendir
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="paprika_v6")
except ImportError:
    st.warning("⚠️ Otomatik yenileme devre dışı. Aktif etmek için: pip install streamlit-autorefresh")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.stApp{background:#f0f2f5;font-family:'IBM Plex Sans',sans-serif;color:#111827}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0!important;max-width:100%!important}
[data-testid="stVerticalBlock"]{gap:0!important}
.stMarkdown{margin:0!important}
hr{display:none!important}

/* TOP BAR */
.topbar{background:#0f172a;padding:0 24px;height:54px;display:flex;align-items:center;
        justify-content:space-between;border-bottom:2px solid #1e3a5f}
.t-logo{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:#f1f5f9;
        display:flex;align-items:center;gap:10px}
.t-logo .dot{color:#38bdf8}
.t-badge{font-size:10px;font-weight:600;font-family:'IBM Plex Sans',sans-serif;
         background:#1e3a5f;color:#7dd3fc;padding:3px 9px;border-radius:4px;letter-spacing:.4px}
.live-dot{width:8px;height:8px;background:#4ade80;border-radius:50%;
          box-shadow:0 0 0 2px rgba(74,222,128,.2);animation:pulse 2s ease infinite}
@keyframes pulse{50%{opacity:.3}}
.t-strip{display:flex;align-items:center;height:100%}
.t-item{display:flex;align-items:center;gap:6px;padding:0 13px;
        border-left:1px solid #1e3a5f;height:100%}
.t-lbl{font-family:'IBM Plex Sans',sans-serif;font-size:10px;font-weight:700;
       color:#64748b;letter-spacing:.5px;text-transform:uppercase;white-space:nowrap}
.t-val{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;
       color:#e2e8f0;white-space:nowrap}
.t-up{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;
      color:#4ade80;white-space:nowrap}
.t-dn{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;
      color:#f87171;white-space:nowrap}
.t-fl{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#64748b;white-space:nowrap}

/* SECTION */
.sw{padding:16px 24px 12px}
.sh{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.sb{width:4px;height:20px;background:#2563eb;border-radius:3px;flex-shrink:0}
.st{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
    letter-spacing:1.8px;text-transform:uppercase;color:#2563eb}
.ss{margin-left:auto;font-size:11px;color:#94a3b8;white-space:nowrap}

/* RADAR */
.rg{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}
.rc{background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;padding:14px 10px;
    text-align:center;position:relative;overflow:hidden;transition:box-shadow .2s,transform .15s}
.rc:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.1)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.rc-B::before{background:#7c3aed}.rc-T::before{background:#dc2626}
.rc-D::before{background:#d97706}.rc-I::before{background:#94a3b8}
.rc-B{border-color:rgba(124,58,237,.2)}.rc-T{border-color:rgba(220,38,38,.2)}
.rc-D{border-color:rgba(217,119,6,.2)}
.rc-tic{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#0f172a;margin-bottom:2px}
.rc-fiy{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#1e40af;margin-bottom:4px}
.rc-vol{font-size:10px;color:#64748b;margin-bottom:7px}
.pill{display:inline-block;padding:3px 7px;border-radius:20px;font-family:'IBM Plex Sans',sans-serif;
      font-size:9px;font-weight:700;letter-spacing:.4px;text-transform:uppercase}
.p-B{background:#f5f3ff;color:#5b21b6;border:1px solid #c4b5fd}
.p-T{background:#fef2f2;color:#b91c1c;border:1px solid #fca5a5;animation:blink 1.5s ease infinite}
.p-D{background:#fffbeb;color:#92400e;border:1px solid #fcd34d}
.p-I{background:#f8fafc;color:#475569;border:1px solid #cbd5e1}
@keyframes blink{50%{opacity:.55}}
.rc-up{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:#16a34a;margin-top:4px}
.rc-dn{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:#dc2626;margin-top:4px}

/* TABLO */
.mw{background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;overflow:hidden}
.mt{width:100%;border-collapse:collapse;font-size:13px;font-family:Arial,sans-serif}
.mt thead tr{background:#f1f5f9}
.mt th{padding:11px 14px;text-align:left;font-family:Arial,sans-serif;
       font-size:11px;font-weight:700;letter-spacing:.5px;color:#1d4ed8;
       text-transform:uppercase;border-bottom:2px solid #dde3ec}
.mt tbody tr{border-bottom:1px solid #f1f5f9;transition:background .12s}
.mt tbody tr:last-child{border-bottom:none}
.mt tbody tr:hover{background:#f5f8ff}
.mt td{padding:11px 14px;vertical-align:middle;font-family:Arial,sans-serif;font-size:13px}
.td-r{font-family:Arial,sans-serif;font-size:13px;font-weight:700;color:#1e40af;
      background:#eff6ff;border-radius:6px;padding:2px 8px;text-align:center;display:inline-block}
.td-h{font-family:Arial,sans-serif;font-size:13px;font-weight:700;color:#0f172a}
.td-f{font-family:Arial,sans-serif;font-weight:700;font-size:13px;color:#1e293b}
.td-ht{font-family:Arial,sans-serif;font-size:13px;color:#15803d;font-weight:700}
.td-u{font-family:Arial,sans-serif;font-size:13px;font-weight:700;color:#16a34a}
.td-d{font-family:Arial,sans-serif;font-size:13px;font-weight:700;color:#dc2626}
.td-a{font-family:Arial,sans-serif;font-size:13px;color:#475569;font-weight:400}
.td-s{font-family:Arial,sans-serif;font-size:13px;font-weight:700;color:#2563eb}
.td-y{font-family:Arial,sans-serif;font-size:13px;color:#334155;line-height:1.5;max-width:240px;font-weight:400}

/* SENSOR */
.sensor-wrap{background:#f8fafc;border-radius:16px;padding:20px 24px 24px;
             border:1.5px solid #e2e8f0;margin:0 0 2px}
.sensor-hdr{display:flex;align-items:center;gap:10px;margin-bottom:16px;
            padding-bottom:14px;border-bottom:2px solid #e2e8f0}
.sensor-hdr-title{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
                  letter-spacing:2px;text-transform:uppercase;color:#2563eb}
.sensor-hdr-sub{margin-left:auto;font-size:11px;color:#94a3b8}
.sensor-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}

/* F/P kart */
.fp-card{background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #2563eb;
         border-radius:12px;padding:18px 20px}
.fp-ttl{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
        letter-spacing:1.5px;text-transform:uppercase;color:#2563eb;
        margin-bottom:14px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.fp-row{display:flex;justify-content:space-between;align-items:center;
        padding:9px 0;border-bottom:1px solid #f1f5f9}
.fp-row:last-child{border-bottom:none}
.fp-left{display:flex;flex-direction:column;gap:3px;flex:1}
.fp-name{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;color:#0f172a}
.fp-meta{font-family:'IBM Plex Sans',sans-serif;font-size:11px;color:#64748b}
.fp-bar-bg{background:#e2e8f0;border-radius:3px;height:3px;width:80px;overflow:hidden;margin-top:3px}
.fp-bar-fill{height:100%;border-radius:3px;background:linear-gradient(90deg,#2563eb,#60a5fa)}
.fp-bdg{font-family:'IBM Plex Sans',sans-serif;font-size:9px;font-weight:700;
        padding:3px 9px;border-radius:20px;letter-spacing:.4px;text-transform:uppercase;
        flex-shrink:0;margin-left:8px}
.fpb-g{background:#f0fdf4;color:#15803d;border:1px solid #86efac}
.fpb-b{background:#eff6ff;color:#1d4ed8;border:1px solid #93c5fd}
.fpb-a{background:#fffbeb;color:#92400e;border:1px solid #fcd34d}

/* Hacim kart */
.hc-card{background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #16a34a;
         border-radius:12px;padding:18px 20px}
.hc-ttl{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
        letter-spacing:1.5px;text-transform:uppercase;color:#16a34a;
        margin-bottom:14px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.hc-big{font-family:'IBM Plex Mono',monospace;font-size:30px;font-weight:700;
        line-height:1;margin:4px 0 4px}
.hc-g{color:#16a34a}.hc-r{color:#dc2626}
.hc-sub{font-family:'IBM Plex Sans',sans-serif;font-size:11px;color:#64748b;margin-bottom:12px}
.hc-bar{background:#e2e8f0;border-radius:6px;height:6px;overflow:hidden;margin-bottom:8px}
.hc-bar-g{height:100%;background:linear-gradient(90deg,#16a34a,#4ade80);border-radius:6px}
.hc-bar-r{height:100%;background:linear-gradient(90deg,#dc2626,#f87171);border-radius:6px}
.hc-pct{display:flex;justify-content:space-between;font-size:13px;font-weight:700;
        margin-bottom:12px}
.hc-row{display:flex;justify-content:space-between;align-items:center;
        padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:12px}
.hc-row:last-child{border-bottom:none}
.hc-lbl{font-family:'IBM Plex Sans',sans-serif;color:#64748b}
.hc-val{font-family:'IBM Plex Mono',monospace;color:#1e293b;font-weight:700;font-size:12px}

/* Duygu kart */
.dg-card{background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #7c3aed;
         border-radius:12px;padding:18px 20px}
.dg-ttl{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
        letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;
        margin-bottom:14px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.dg-num{font-family:'IBM Plex Mono',monospace;font-size:52px;font-weight:700;
        line-height:1;margin:4px 0 2px}
.dg-lbl{font-family:'IBM Plex Sans',sans-serif;font-size:14px;font-weight:600;margin-bottom:3px}
.dg-rsi{font-family:'IBM Plex Sans',sans-serif;font-size:12px;color:#64748b;margin-bottom:12px}
.dg-bar{background:#e2e8f0;border-radius:8px;height:8px;overflow:hidden;margin-bottom:5px}
.dg-fill{height:100%;border-radius:8px}
.dg-scale{display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;
          font-family:'IBM Plex Mono',monospace;margin-bottom:12px}
.dg-row{display:flex;justify-content:space-between;align-items:center;
        padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:12px}
.dg-row:last-child{border-bottom:none}
.dg-rlbl{font-family:'IBM Plex Sans',sans-serif;color:#64748b}
.dg-rval{font-family:'IBM Plex Sans',sans-serif;color:#475569;font-size:11px}

/* INTEL */
.ig{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ic{background:#fff;border:1.5px solid #e2e8f0;border-left:4px solid #2563eb;
    border-radius:10px;padding:16px 18px}
.itag{display:inline-block;margin-bottom:8px;padding:3px 10px;font-size:10px;
      font-weight:700;letter-spacing:.8px;text-transform:uppercase;
      background:#eff6ff;color:#1d4ed8;border-radius:5px}
.ittl{font-size:14px;font-weight:700;color:#0f172a;margin-bottom:6px;line-height:1.4}
.ibod{font-size:12px;color:#475569;line-height:1.65}
.ilink{font-size:11px;color:#2563eb;text-decoration:none}

/* NEWS */
.ng{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.np{background:#fff;border:1.5px solid #e2e8f0;border-radius:12px;padding:18px 20px}
.ntt{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
     letter-spacing:1.5px;text-transform:uppercase;color:#1d4ed8;
     margin-bottom:12px;padding-bottom:11px;border-bottom:1.5px solid #e2e8f0}
.nr{display:flex;align-items:flex-start;gap:10px;padding:8px 0;
    border-bottom:1px solid #f1f5f9}
.nr:last-child{border-bottom:none}
.nt{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
    color:#dc2626;min-width:42px;flex-shrink:0;margin-top:1px}
.nb{font-size:13px;color:#1e293b;line-height:1.5;font-weight:500}
.nc{font-size:10px;font-weight:700;background:#eff6ff;color:#1d4ed8;
    padding:1px 6px;border-radius:3px;margin-right:5px;white-space:nowrap}

/* FOOTER */
.footer{background:#0f172a;border-top:1px solid #1e3a5f;padding:12px 24px;
        display:flex;justify-content:space-between;font-size:11px;color:#475569;
        font-family:'IBM Plex Mono',monospace;margin-top:8px}

/* SCORE BAR */
.score-bar-wrap{width:100%;background:#f1f5f9;border-radius:4px;height:6px;margin-top:4px;overflow:hidden}
.score-bar{height:100%;border-radius:4px;background:linear-gradient(90deg,#2563eb,#38bdf8)}

/* ══ MOBİL RESPONSIVE ══════════════════════════════════════════════════════ */
.topbar-desktop { display:flex; }
.topbar-mobile  { display:none; }
.st-long  { display:inline; }
.st-short { display:none; }

@media (max-width: 768px) {
  .stApp { font-size:14px; }
  .sw { padding:10px 12px 8px !important; }
  .topbar-desktop { display:none !important; }
  .topbar-mobile  { display:block !important; }
  .st-long  { display:none !important; }
  .st-short { display:inline !important; }
  .st { font-size:10px !important; letter-spacing:1.2px !important; }
  .ss { font-size:10px !important; }
  .rg { grid-template-columns:repeat(2,1fr) !important; gap:6px !important; }
  .rc { padding:10px 8px !important; }
  .rc-tic { font-size:12px !important; }
  .rc-fiy { font-size:12px !important; }
  .rc-vol { font-size:9px !important; }
  .mw { overflow-x:auto !important; -webkit-overflow-scrolling:touch; }
  .mt { font-size:12px !important; min-width:580px; }
  .mt th { padding:8px 10px !important; font-size:10px !important; }
  .mt td { padding:8px 10px !important; }
  .td-h  { font-size:12px !important; }
  .td-f,.td-ht,.td-u,.td-d,.td-a,.td-y { font-size:11px !important; }
  .sensor-grid { grid-template-columns:1fr !important; }
  .sensor-wrap { padding:12px 12px 16px !important; }
  .ig { grid-template-columns:1fr !important; }
  .ng { grid-template-columns:1fr !important; }
  [style*="grid-template-columns:1fr 1fr 1fr"],
  [style*="grid-template-columns: 1fr 1fr 1fr"],
  [style*="repeat(3,1fr)"],
  [style*="repeat(3, 1fr)"] { grid-template-columns:1fr !important; }
  [style*="grid-template-columns:1fr 1fr"],
  [style*="grid-template-columns: 1fr 1fr"],
  [style*="repeat(2,1fr)"],
  [style*="repeat(2, 1fr)"] { grid-template-columns:1fr !important; }
  .footer { flex-direction:column; gap:4px; padding:10px 12px;
            font-size:10px !important; }
  .footer span:nth-child(2),.footer span:nth-child(3) { color:#334155; }
}

@media (max-width: 480px) {
  .sw { padding:8px 10px 6px !important; }
  .rg { grid-template-columns:1fr 1fr !important; gap:5px !important; }
  .mt { font-size:11px !important; min-width:540px; }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  BIST100 SEMBOLLERİ
# ═══════════════════════════════════════════════════════════════════════════════
BIST100 = [
    "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
    "SISE" ,"TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
    "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
    "ARCLK","ISCTR","SOKM" ,"TTKOM","SASA" ,"AGHOL","ALGYO","CCOLA",
    "CIMSA","DOAS" ,"EGEEN","MPARK","NETAS","ODAS" ,"OYAKC","PARSN",
    "AKSEN","AEFES","AKGRT","ALFAS","BRISA","CANTE","CUSAN","DEVA",
    "EKOS" ,"ENJSA","GESAN","GUBRF","IHLGM","IHEVA","IPEKE","ISGYO",
    "IZMDC","KARSN","KCAER","KLGYO","KONYA","MAVI" ,"MGROS","NUHCM",
    "OTKAR","OYAYO","PAPIL","PENTA","QUAGR","RYSAS","SARKY","SELVA",
    "SMRTG","TSKB" ,"TTRAK","ULKER","VESBE","YATAS","ZOREN",
]
BIST100 = [s.strip() for s in BIST100]

RADAR_FALLBACK = ["GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL"]

# ═══════════════════════════════════════════════════════════════════════════════
#  YARDIMCI HESAPLAMALAR
# ═══════════════════════════════════════════════════════════════════════════════

def hesapla_rsi(closes, period=14):
    delta = closes.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def hesapla_macd(closes, fast=12, slow=26, signal=9):
    ema_f = closes.ewm(span=fast, adjust=False).mean()
    ema_s = closes.ewm(span=slow, adjust=False).mean()
    macd  = ema_f - ema_s
    sig   = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig

def puan_hesapla(closes, volumes):
    """RSI + MACD + Momentum + Hacim Artışı → 0-100 puan"""
    if len(closes) < 30:
        return 0.0
    try:
        rsi  = hesapla_rsi(closes).iloc[-1]
        macd, sig = hesapla_macd(closes)
        macd_v = macd.iloc[-1]
        sig_v  = sig.iloc[-1]
        mom = ((closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6]) * 100
        vol_artis = 0
        if volumes is not None and len(volumes) >= 6:
            vol_ort = volumes.iloc[-6:-1].mean()
            if vol_ort > 0:
                vol_artis = ((volumes.iloc[-1] - vol_ort) / vol_ort) * 100
        puan = 0
        if 40 <= rsi <= 60:   puan += 25
        elif 30 <= rsi < 40:  puan += 35
        elif 60 < rsi <= 70:  puan += 20
        elif rsi < 30:        puan += 30
        elif rsi > 70:        puan += 10
        if macd_v > sig_v:    puan += 25
        else:                 puan += 5
        if mom > 3:           puan += 20
        elif mom > 0:         puan += 15
        elif mom > -2:        puan += 8
        if vol_artis > 50:    puan += 15
        elif vol_artis > 20:  puan += 10
        elif vol_artis > 0:   puan += 5
        return min(float(puan), 100)
    except Exception:
        return 0.0

# ═══════════════════════════════════════════════════════════════════════════════
#  VERİ FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60, show_spinner=False)
def radar_hacim_cek():
    hedefler = [
        "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
        "SISE","TOASO","FROTO","AKBNK","HALKB","VAKBN","PGSUS","TCELL",
        "ENKAI","KRDMD","PETKM","BIMAS","ARCLK","ISCTR","TTKOM","EKGYO",
    ]
    results = []
    for sym in hedefler:
        try:
            h    = yf.Ticker(f"{sym}.IS").history(period="5d")
            clz  = h["Close"].dropna()
            vol  = h["Volume"].dropna()
            if len(clz) < 1 or len(vol) < 1:
                continue
            price    = float(clz.iloc[-1])
            vol_adet = float(vol.iloc[-1])
            prev     = float(clz.iloc[-2]) if len(clz) >= 2 else price
            chg      = round(((price - prev) / prev) * 100, 2) if prev > 0 else 0
            tl_hacim = price * vol_adet
            if price > 0 and tl_hacim > 0:
                results.append({
                    "sym":     sym,
                    "price":   round(price, 2),
                    "chg":     chg,
                    "vol_tl":  tl_hacim,
                    "vol_lot": vol_adet,
                })
        except Exception:
            continue
    results.sort(key=lambda x: x["vol_tl"], reverse=True)
    return results[:8]


# [DÜZELTME 3] Paralel HTTP istekleri — ThreadPoolExecutor
@st.cache_data(ttl=600, show_spinner=False)
def haber_duyarlilik_skoru():
    BIST_LIST = [
        "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
        "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
        "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
        "ARCLK","ISCTR","TTKOM","SASA","CCOLA","DOAS","AKSEN","AEFES",
        "BRISA","ENJSA","MGROS","OTKAR","ULKER","VESBE","TSKB","TTRAK",
    ]
    POZITIF = ["yükseliş","artış","rekor","güçlü","alım","ihale","kâr","büyüme",
               "yatırım","sipariş","temettü","pozitif","rally","toparlandı","yukarı"]
    NEGATIF = ["düşüş","zarar","satış","baskı","risk","endişe","uyarı","negatif",
               "zayıf","kaybetti","geriledi","soruşturma","ceza","borç","kriz"]
    HDR = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    def _cek(sym):
        try:
            url = (f"https://news.google.com/rss/search?q={sym}+hisse+borsa"
                   f"&hl=tr&gl=TR&ceid=TR:tr")
            r = requests.get(url, headers=HDR, timeout=6)
            r.raise_for_status()
            text_lower = r.text.lower()
            haber_sayi = text_lower.count("<item>")
            poz = sum(text_lower.count(k) for k in POZITIF)
            neg = sum(text_lower.count(k) for k in NEGATIF)
            toplam_kelime = poz + neg + 1
            oran = (poz - neg) / toplam_kelime
            skor = round(min(max(oran * 20 + haber_sayi * 0.5, -10), 10), 1)
            return sym, skor
        except Exception:
            return sym, 0.0

    skorlar = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_cek, s): s for s in BIST_LIST}
        for f in as_completed(futures):
            sym, skor = f.result()
            skorlar[sym] = skor
    return skorlar


@st.cache_data(ttl=300, show_spinner=False)
def top10_analiz():
    """
    ÇOK BOYUTLU ANALİZ MOTORİ — 4 Katman:
    1. TEKNİK  (40 puan): RSI + MACD + Momentum + Hacim artışı
    2. DUYGU   (25 puan): Haber duyarlılığı + Google News frekansı
    3. ANALİTİK(25 puan): 52H dip/zirve konumu + Bollinger bant
    4. SOSYAL  (10 puan): Haber sayısı trendine göre ilgi skoru
    """
    ANALIZ_LISTESI = [
        "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
        "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
        "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
        "ARCLK","ISCTR","TTKOM","SASA","CCOLA","DOAS","AKSEN","AEFES",
        "BRISA","ENJSA","MGROS","OTKAR","ULKER","VESBE","TSKB","TTRAK",
    ]

    haber_sk = haber_duyarlilik_skoru()

    rows = []
    for sym in ANALIZ_LISTESI:
        try:
            t = yf.Ticker(f"{sym}.IS")
            h = t.history(period="65d")
            if len(h) < 20:
                continue

            closes  = h["Close"].dropna()
            volumes = h["Volume"].dropna()
            price   = float(closes.iloc[-1])
            prev    = float(closes.iloc[-2]) if len(closes) >= 2 else price
            chg     = round(((price - prev) / prev) * 100, 2)
            vol_son = float(volumes.iloc[-1]) if len(volumes) >= 1 else 0
            tl_hacim = price * vol_son

            # ── 1. TEKNİK PUAN (0-40) ─────────────────────────────────────
            tek_puan = 0
            rsi_son = 50.0
            if len(closes) >= 15:
                rsi_son = float(hesapla_rsi(closes).iloc[-1])

            if rsi_son < 30:    tek_puan += 16
            elif rsi_son < 40:  tek_puan += 14
            elif rsi_son < 50:  tek_puan += 11
            elif rsi_son < 60:  tek_puan += 8
            elif rsi_son < 70:  tek_puan += 5
            else:               tek_puan += 2

            # [DÜZELTME 1] macd_son ile kapsam sorunu giderildi
            macd_son = 0.0
            if len(closes) >= 30:
                macd, sig = hesapla_macd(closes)
                macd_son = float(macd.iloc[-1])
                sig_son  = float(sig.iloc[-1])
                if macd_son > sig_son:
                    tek_puan += 12
                    if float(macd.iloc[-2]) <= float(sig.iloc[-2]):
                        tek_puan += 4  # Taze kesişim bonus
                else:
                    tek_puan += 2

            if len(volumes) >= 10:
                vol_ort = float(volumes.iloc[-10:-1].mean())
                if vol_ort > 0:
                    vol_art = (vol_son - vol_ort) / vol_ort * 100
                    if vol_art > 100: tek_puan += 8
                    elif vol_art > 50: tek_puan += 6
                    elif vol_art > 20: tek_puan += 4
                    elif vol_art > 0:  tek_puan += 2
            tek_puan = min(tek_puan, 40)

            # ── 2. HABER/DUYGU PUANI (0-25) ──────────────────────────────
            haber_skor = haber_sk.get(sym, 0.0)
            duygu_puan = int((haber_skor + 10) / 20 * 25)
            duygu_puan = min(max(duygu_puan, 0), 25)

            # ── 3. ANALİTİK PUAN (0-25) ──────────────────────────────────
            analitik = 0

            # [DÜZELTME 2] dip_pct varsayılan değeri ile kapsam sorunu giderildi
            dip_pct = 50.0
            h52 = t.history(period="252d")
            clz52 = h52["Close"].dropna() if len(h52) > 0 else closes
            low52  = float(clz52.min())
            high52 = float(clz52.max())
            rng52  = high52 - low52
            if rng52 > 0:
                dip_pct = (price - low52) / rng52 * 100

            if dip_pct <= 15:    analitik += 14
            elif dip_pct <= 30:  analitik += 11
            elif dip_pct <= 50:  analitik += 7
            elif dip_pct <= 70:  analitik += 4
            else:                analitik += 1

            if len(closes) >= 20:
                sma20 = float(closes.rolling(20).mean().iloc[-1])
                std20 = float(closes.rolling(20).std().iloc[-1])
                lower_band = sma20 - 2 * std20
                if std20 > 0:
                    bb_pos = (price - lower_band) / (4 * std20)
                    if bb_pos <= 0.2:    analitik += 11
                    elif bb_pos <= 0.4:  analitik += 8
                    elif bb_pos <= 0.6:  analitik += 5
                    else:                analitik += 2
            analitik = min(analitik, 25)

            # ── 4. SOSYAL/İLGİ PUANI (0-10) ──────────────────────────────
            sosyal = min(max(int((haber_skor + 10) / 4), 0), 10)

            # ── TOPLAM ───────────────────────────────────────────────────
            toplam_puan = tek_puan + duygu_puan + analitik + sosyal

            # [DÜZELTME 1] macd_son kullanılıyor, artık NameError yok
            if rsi_son < 35 and macd_son > 0:
                sinyal_lbl = "GÜÇLÜ AL"
            elif rsi_son < 45 and duygu_puan >= 15:
                sinyal_lbl = "AL"
            elif dip_pct <= 20:
                sinyal_lbl = "DİP BÖLGE"
            elif haber_skor >= 5:
                sinyal_lbl = "HABER POZ."
            else:
                sinyal_lbl = "İZLE"

            rows.append({
                "Hisse":      sym,
                "Fiyat":      round(price, 2),
                "Degisim":    chg,
                "TL_Hacim":   tl_hacim,
                "RSI":        round(rsi_son, 1),
                "Tek_Puan":   tek_puan,
                "Duygu_Puan": duygu_puan,
                "Analitik":   analitik,
                "Sosyal":     sosyal,
                "Puan":       round(float(toplam_puan), 1),
                "Sinyal":     sinyal_lbl,
                "Haber_Sk":   round(haber_skor, 1),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("Puan", ascending=False).head(10).reset_index(drop=True)
    df.index = df.index + 1
    return df


@st.cache_data(ttl=60, show_spinner=False)
def makro_cek():
    m = dict(
        USD_TRY=0.0, EUR_TRY=0.0,
        GRAM_ALTIN=0.0, ONS_ALTIN=0.0,
        BTC_USD=0.0, BTC_CHG=0.0, ETH_USD=0.0,
        BIST100=0.0, BIST100_CHG=0.0,
        BIST100_VOL=0.0,
        PETROL=0.0,
    )

    # TCMB XML
    try:
        r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml",
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
        for cur in root.findall("Currency"):
            kod = cur.get("CurrencyCode", "")
            def _v(tag, c=cur):
                el = c.find(tag)
                try: return float(el.text.replace(",", ".")) if el is not None and el.text else 0.0
                except: return 0.0
            if kod == "USD":
                m["USD_TRY"] = _v("ForexSelling") or _v("ForexBuying")
            elif kod == "EUR":
                m["EUR_TRY"] = _v("ForexSelling") or _v("ForexBuying")
    except Exception:
        pass

    # Altın: truncgil.com
    try:
        r = requests.get(
            "https://finans.truncgil.com/v4/today.json",
            timeout=8, headers={"User-Agent": "Mozilla/5.0"}
        )
        d = r.json()
        for key in ["gram-altin", "GA", "Gram Altın", "gram_altin"]:
            entry = d.get(key, {})
            if entry:
                raw = entry.get("Selling") or entry.get("selling") or entry.get("Buying") or entry.get("buying") or 0
                try:
                    m["GRAM_ALTIN"] = round(float(str(raw).replace(",", ".")), 1)
                    break
                except Exception:
                    continue
    except Exception:
        pass

    # ONS altın: yfinance GC=F
    try:
        gc = yf.Ticker("GC=F").history(period="3d")
        clz = gc["Close"].dropna()
        if len(clz) >= 1:
            m["ONS_ALTIN"] = round(float(clz.iloc[-1]), 1)
    except Exception:
        pass

    # Gram fallback
    if m["GRAM_ALTIN"] == 0 and m["ONS_ALTIN"] > 0 and m["USD_TRY"] > 0:
        m["GRAM_ALTIN"] = round(m["ONS_ALTIN"] * m["USD_TRY"] / 31.1035, 1)

    # CoinGecko
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids":"bitcoin,ethereum","vs_currencies":"usd","include_24hr_change":"true"},
            timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        d = r.json()
        m["BTC_USD"] = float(d.get("bitcoin",{}).get("usd",0))
        m["BTC_CHG"] = round(float(d.get("bitcoin",{}).get("usd_24h_change",0)),2)
        m["ETH_USD"] = float(d.get("ethereum",{}).get("usd",0))
    except Exception:
        pass

    # BIST100
    try:
        t   = yf.Ticker("XU100.IS")
        h   = t.history(period="2d")
        clz = h["Close"].dropna()
        vol = h["Volume"].dropna()
        if len(clz) >= 2:
            m["BIST100"]     = round(float(clz.iloc[-1]))
            m["BIST100_CHG"] = round(((float(clz.iloc[-1])-float(clz.iloc[-2]))/float(clz.iloc[-2]))*100, 2)
        elif len(clz)==1:
            m["BIST100"] = round(float(clz.iloc[0]))
        if len(vol) >= 1:
            m["BIST100_VOL"] = float(vol.iloc[-1])
    except Exception:
        pass

    # Brent
    try:
        h = yf.Ticker("BZ=F").history(period="2d")
        clz = h["Close"].dropna()
        if len(clz) >= 1:
            m["PETROL"] = round(float(clz.iloc[-1]),2)
    except Exception:
        pass

    return m


@st.cache_data(ttl=300, show_spinner=False)
def duygu_endeksi_hesapla():
    BIST_GENEL = [
        "GARAN.IS","THYAO.IS","ASELS.IS","EREGL.IS","TUPRS.IS",
        "KCHOL.IS","YKBNK.IS","SAHOL.IS","SISE.IS","TOASO.IS",
        "AKBNK.IS","HALKB.IS","VAKBN.IS","FROTO.IS","BIMAS.IS",
        "PGSUS.IS","TCELL.IS","ENKAI.IS","KRDMD.IS","EKGYO.IS",
    ]
    try:
        rsi_listesi = []
        yukselenler = 0
        toplam      = 0
        for sym in BIST_GENEL:
            try:
                h   = yf.Ticker(sym).history(period="30d")
                clz = h["Close"].dropna()
                if len(clz) >= 15:
                    rsi = float(hesapla_rsi(clz).iloc[-1])
                    rsi_listesi.append(rsi)
                    toplam += 1
                    if float(clz.iloc[-1]) > float(clz.iloc[-2]):
                        yukselenler += 1
            except Exception:
                pass

        if not rsi_listesi:
            return 50, "Nötr", "#d97706", 50.0, 0, 0

        ort_rsi = float(np.mean(rsi_listesi))
        oran    = yukselenler / max(toplam, 1)

        momentum_katki = 0
        try:
            h5  = yf.Ticker("XU100.IS").history(period="7d")
            clz5 = h5["Close"].dropna()
            if len(clz5) >= 5:
                mom5 = ((float(clz5.iloc[-1]) - float(clz5.iloc[-5])) / float(clz5.iloc[-5])) * 100
                momentum_katki = min(max(mom5 * 3, -15), 15)
        except Exception:
            pass

        endeks = int(ort_rsi * 0.60 + oran * 100 * 0.30 + (50 + momentum_katki) * 0.10)
        endeks = max(0, min(100, endeks))

        if endeks >= 75:   durum, renk = "Aşırı Açgözlülük", "#16a34a"
        elif endeks >= 60: durum, renk = "Açgözlülük",        "#22c55e"
        elif endeks >= 45: durum, renk = "Nötr / Pozitif",    "#d97706"
        elif endeks >= 30: durum, renk = "Korku",              "#dc2626"
        else:              durum, renk = "Aşırı Korku",        "#991b1b"

        return endeks, durum, renk, round(ort_rsi, 1), yukselenler, toplam
    except Exception:
        return 50, "Nötr", "#d97706", 50.0, 0, 0


@st.cache_data(ttl=300, show_spinner=False)
def haber_cek():
    FEEDS = [
        ("https://news.google.com/rss/search?q=borsa+istanbul+hisse+BIST&hl=tr&gl=TR&ceid=TR:tr", "G.NEWS"),
        ("https://news.google.com/rss/search?q=KAP+kamuoyu+aydınlatma+hisse+bildirimi&hl=tr&gl=TR&ceid=TR:tr", "KAP"),
        ("https://news.google.com/rss/search?q=BIST+borsa+faiz+dolar+TL+Türkiye&hl=tr&gl=TR&ceid=TR:tr", "G.NEWS"),
        ("https://news.google.com/rss/search?q=brüt+takas+hisse+borsa+istanbul&hl=tr&gl=TR&ceid=TR:tr", "BİST"),
    ]
    HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/120.0.0.0 Safari/537.36",
           "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"}
    haberler = []

    for url, kaynak in FEEDS:
        if len(haberler) >= 12:
            break
        try:
            r = requests.get(url, headers=HDR, timeout=10)
            r.raise_for_status()
            text = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', '', r.text)
            text = re.sub(r'<\?xml[^>]+\?>', '', text)
            root = ET.fromstring(text.encode("utf-8","replace"))
            items = root.findall(".//item") or root.findall(".//entry")
            for item in items[:6]:
                t_el = item.find("title")
                title = ""
                if t_el is not None:
                    raw = t_el.text or ""
                    raw = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', raw, flags=re.DOTALL)
                    title = html_mod.unescape(raw).strip()
                    title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
                if len(title) < 8:
                    continue
                zaman = datetime.now().strftime("%H:%M")
                for tag in ("pubDate","published","updated"):
                    el = item.find(tag)
                    if el is not None and el.text:
                        raw_t = el.text.strip()
                        for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                                    "%a, %d %b %Y %H:%M:%S %Z",
                                    "%Y-%m-%dT%H:%M:%S%z",
                                    "%Y-%m-%dT%H:%M:%SZ"):
                            try:
                                zaman = datetime.strptime(raw_t, fmt).strftime("%H:%M")
                                break
                            except ValueError:
                                continue
                        break
                link_el = item.find("link")
                link = (link_el.text or "").strip() if link_el is not None else ""
                haberler.append((zaman, kaynak, title[:110], link))
        except Exception:
            continue

    # Fallback: yfinance
    if len(haberler) < 4:
        try:
            news = yf.Ticker("XU100.IS").news or []
            for it in news[:8]:
                title = (it.get("title") or "").strip()
                ts    = it.get("providerPublishTime", 0)
                link  = it.get("link","")
                zaman = datetime.fromtimestamp(ts).strftime("%H:%M") if ts else datetime.now().strftime("%H:%M")
                if title:
                    haberler.append((zaman, "YF/BIST", title[:110], link))
        except Exception:
            pass

    return haberler[:12]


@st.cache_data(ttl=300, show_spinner=False)
def sosyal_trend_cek():
    import os
    today_str = datetime.now().strftime("%Y-%m-%d")
    trendler  = []

    # Gerçek Twitter API (Bearer Token varsa)
    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if bearer:
        try:
            headers = {"Authorization": f"Bearer {bearer}"}
            r = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers=headers,
                params={
                    "query": "BIST100 OR BIST OR #hisse OR borsa istanbul lang:tr -is:retweet",
                    "max_results": 10,
                    "tweet.fields": "created_at,public_metrics",
                    "sort_order": "recency"
                },
                timeout=8
            )
            if r.status_code == 200:
                for tw in r.json().get("data", [])[:8]:
                    text     = (tw.get("text") or "").strip()[:110]
                    created  = tw.get("created_at", "")
                    if today_str not in created:
                        continue
                    zaman = created[11:16] if len(created) >= 16 else datetime.now().strftime("%H:%M")
                    m = tw.get("public_metrics", {})
                    meta = f"❤️{m.get('like_count',0)} 🔁{m.get('retweet_count',0)}"
                    trendler.append((zaman, meta, text, ""))
        except Exception:
            pass

    # Google News RSS — sadece bugün
    if len(trendler) < 6:
        FEEDS = [
            "https://news.google.com/rss/search?q=BIST100+borsa+hisse&hl=tr&gl=TR&ceid=TR:tr",
            "https://news.google.com/rss/search?q=borsa+istanbul+yükseliş+düşüş+hisse&hl=tr&gl=TR&ceid=TR:tr",
            "https://news.google.com/rss/search?q=BIST+finans+yatırım+2026&hl=tr&gl=TR&ceid=TR:tr",
        ]
        HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

        for url in FEEDS:
            if len(trendler) >= 8:
                break
            try:
                r = requests.get(url, headers=HDR, timeout=7)
                r.raise_for_status()
                text_x = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', '', r.text)
                root = ET.fromstring(text_x.encode("utf-8", "replace"))
                for item in root.findall(".//item"):
                    t_el = item.find("title")
                    if t_el is None: continue
                    raw_t = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'', t_el.text or "", flags=re.DOTALL)
                    title = html_mod.unescape(raw_t).strip()
                    title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
                    if len(title) < 8: continue

                    p_el = item.find("pubDate")
                    zaman = None
                    if p_el is not None and p_el.text:
                        raw_d = p_el.text.strip()
                        for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                                    "%a, %d %b %Y %H:%M:%S %Z",
                                    "%a, %d %b %Y %H:%M:%S +0000"):
                            try:
                                dt_obj = datetime.strptime(raw_d, fmt)
                                if dt_obj.tzinfo:
                                    from datetime import timezone
                                    dt_obj = dt_obj.astimezone(timezone.utc).replace(tzinfo=None)
                                if dt_obj.strftime("%Y-%m-%d") == today_str:
                                    zaman = dt_obj.strftime("%H:%M")
                                break
                            except Exception:
                                continue
                    if zaman is None: continue

                    link_el = item.find("link")
                    link = (link_el.text or "").strip() if link_el else ""
                    trendler.append((zaman, "📰", title[:110], link))
            except Exception:
                continue

    trendler.sort(key=lambda x: x[0], reverse=True)
    return trendler[:8]


@st.cache_data(ttl=600, show_spinner=False)
def istihbarat_analiz():
    SEKTORLER = {
        "bankacılık": ["GARAN","AKBNK","YKBNK","HALKB","VAKBN","ISCTR"],
        "havacılık":  ["THYAO","PGSUS"],
        "savunma":    ["ASELS","ROKET","ASELSAN"],
        "enerji":     ["TUPRS","AKSEN","ENJSA","ZOREN","ODAS"],
        "gyo":        ["EKGYO","ISGYO","ALGYO"],
        "madencilik": ["KOZAL","EREGL","KRDMD","ARCLK"],
        "perakende":  ["BIMAS","MGROS","SOKM"],
        "teknoloji":  ["TTKOM","NETAS","LOGO"],
    }
    POZITIF_KW = ["rekor","yükseliş","artış","kâr","büyüme","ihale","sipariş","temettü",
                  "güçlü","alım","toparlandı","pozitif","teşvik","yatırım","ihracat"]
    NEGATIF_KW = ["düşüş","zarar","kayıp","baskı","risk","soruşturma","ceza","kriz",
                  "endişe","zayıf","gerileme","borç","iflas","uyarı","negatif"]

    HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    FEEDS = [
        "https://news.google.com/rss/search?q=borsa+istanbul+hisse+sektör&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=TCMB+faiz+Türkiye+ekonomi&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=BIST+hisse+yükseliş+düşüş&hl=tr&gl=TR&ceid=TR:tr",
    ]

    haberler_raw = []
    for url in FEEDS:
        try:
            r = requests.get(url, headers=HDR, timeout=7)
            r.raise_for_status()
            text_x = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', '', r.text)
            root = ET.fromstring(text_x.encode("utf-8","replace"))
            for item in root.findall(".//item")[:6]:
                t_el = item.find("title")
                if t_el is None: continue
                raw = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'', t_el.text or "", flags=re.DOTALL)
                title = html_mod.unescape(raw).strip()
                title = re.sub(r'\s*-\s*[^-]+$', '', title).strip()
                p_el = item.find("pubDate")
                zaman = datetime.now().strftime("%d.%m %H:%M")
                if p_el is not None and p_el.text:
                    for fmt in ("%a, %d %b %Y %H:%M:%S %z","%a, %d %b %Y %H:%M:%S %Z"):
                        try:
                            zaman = datetime.strptime(p_el.text.strip(), fmt).strftime("%d.%m %H:%M")
                            break
                        except: continue
                link_el = item.find("link")
                link = (link_el.text or "").strip() if link_el else ""
                haberler_raw.append({"title": title, "zaman": zaman, "link": link})
        except Exception:
            continue

    sonuclar = []
    for h in haberler_raw:
        title_lower = h["title"].lower()
        poz = sum(title_lower.count(k) for k in POZITIF_KW)
        neg = sum(title_lower.count(k) for k in NEGATIF_KW)
        duygu = "pozitif" if poz > neg else ("negatif" if neg > poz else "nötr")
        ilgili_sektor = "genel"
        for sektor, hisseler in SEKTORLER.items():
            if sektor in title_lower or any(h_.lower() in title_lower for h_ in hisseler):
                ilgili_sektor = sektor
                break
        sonuclar.append({
            "title":   h["title"],
            "zaman":   h["zaman"],
            "link":    h["link"],
            "duygu":   duygu,
            "sektor":  ilgili_sektor,
            "poz":     poz,
            "neg":     neg,
        })

    sonuclar.sort(key=lambda x: (x["duygu"] != "nötr", x["poz"] + x["neg"]), reverse=True)
    return sonuclar[:8]


@st.cache_data(ttl=300, show_spinner=False)
def fp_radar():
    """
    F/P Değerleme Radarı — Top 5.
    Teknik+değerleme puanı: RSI, 52H dip, Momentum eğimi, Hacim/fiyat.
    """
    aday = [
        "GARAN","EREGL","BIMAS","KCHOL","SISE",
        "TUPRS","YKBNK","TTKOM","CCOLA","ULKER",
        "VESBE","ENJSA","MGROS","TSKB","OTKAR",
        "AKBNK","SAHOL","TAVHL","ARCLK","PETKM",
    ]
    rows = []
    for sym in aday:
        try:
            t   = yf.Ticker(f"{sym}.IS")
            h   = t.history(period="65d")
            clz = h["Close"].dropna()
            vol = h["Volume"].dropna()
            if len(clz) < 20:
                continue

            price  = float(clz.iloc[-1])
            rsi    = float(hesapla_rsi(clz).iloc[-1])

            # [DÜZELTME 4] dip_uzaklik varsayılan değeri ile kapsam sorunu giderildi
            dip_uzaklik = 50.0
            h52 = t.history(period="252d")
            clz52 = h52["Close"].dropna()
            low52  = float(clz52.min()) if len(clz52) > 0 else price
            high52 = float(clz52.max()) if len(clz52) > 0 else price
            range52 = high52 - low52
            if range52 > 0:
                dip_uzaklik = ((price - low52) / range52 * 100)

            son10 = clz.iloc[-10:].values
            egim  = float(np.polyfit(range(len(son10)), son10, 1)[0])
            egim_pct = egim / price * 100

            vol_artis = 0
            if len(vol) >= 10:
                vol_son5 = float(vol.iloc[-5:].mean())
                vol_onc5 = float(vol.iloc[-10:-5].mean())
                if vol_onc5 > 0:
                    vol_artis = (vol_son5 - vol_onc5) / vol_onc5 * 100

            puan = 0

            if 25 <= rsi <= 40:   puan += 35
            elif 40 < rsi <= 50:  puan += 25
            elif rsi < 25:        puan += 28
            elif 50 < rsi <= 60:  puan += 15
            else:                 puan += 5

            if dip_uzaklik <= 20:   puan += 30
            elif dip_uzaklik <= 35: puan += 22
            elif dip_uzaklik <= 50: puan += 14
            elif dip_uzaklik <= 65: puan += 7

            if 0 < egim_pct <= 0.3: puan += 20
            elif egim_pct > 0.3:    puan += 12
            elif -0.2 < egim_pct <= 0: puan += 10
            else:                   puan += 3

            if vol_artis > 30 and rsi < 50:   puan += 15
            elif vol_artis > 10:              puan += 8

            if rsi < 35:             etiket = "AŞIRI UCUZ"
            elif dip_uzaklik < 25:   etiket = "52H DİP"
            elif egim_pct > 0:       etiket = "DÖNÜŞ SİNYALİ"
            else:                    etiket = "DEĞER BÖLGESİ"

            rows.append({
                "Hisse":    sym,
                "Fiyat":    round(price, 2),
                "RSI":      round(rsi, 1),
                "Dip%":     round(dip_uzaklik, 0),
                "Puan":     min(puan, 100),
                "Etiket":   etiket,
            })
        except Exception:
            continue

    rows.sort(key=lambda x: x["Puan"], reverse=True)
    return rows[:5]


# ═══════════════════════════════════════════════════════════════════════════════
#  FORMAT YARDIMCILARI
# ═══════════════════════════════════════════════════════════════════════════════

def ftl(v, d=2):
    if not v or v==0: return "—"
    return f"₺{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")

def fusd(v, d=0):
    if not v or v==0: return "—"
    return f"${v:,.{d}f}"

def fchg(v):
    if v is None: return "<span class='t-fl'>—</span>"
    try: v = float(v)
    except: return "<span class='t-fl'>—</span>"
    if v > 0:  return f"<span class='t-up'>▲ +%{v:.2f}</span>"
    if v < 0:  return f"<span class='t-dn'>▼ %{v:.2f}</span>"
    return "<span class='t-fl'>─</span>"

def mclass(m):
    if "BALİNA" in m: return "B"
    if "TAVAN"  in m: return "T"
    if "DİP"    in m: return "D"
    return "I"

def sinyal(chg, rsi=None):
    if chg > 7:   return "TAVAN ADAYI","T"
    if chg < -2:  return "DİP AVCI","D"
    if chg > 2:   return "BALİNA GİRİŞİ","B"
    return "İZLEME","I"

# ═══════════════════════════════════════════════════════════════════════════════
#  VERİ ÇEK
# ═══════════════════════════════════════════════════════════════════════════════

now       = datetime.now()
mk        = makro_cek()
radar_lst = radar_hacim_cek()
haberler  = haber_cek()
duygu_val, duygu_lbl, duygu_renk, rsi_ort, yukselen_sayi, toplam_sayi = duygu_endeksi_hesapla()

# ═══════════════════════════════════════════════════════════════════════════════
#  TOP BAR
# ═══════════════════════════════════════════════════════════════════════════════

bist_s  = f"{mk['BIST100']:,.0f}".replace(",",".") if mk["BIST100"] else "—"
usd_s   = f"{mk['USD_TRY']:.2f}" if mk["USD_TRY"] else "—"
eur_s   = f"{mk['EUR_TRY']:.2f}" if mk["EUR_TRY"] else "—"
gram_s  = ftl(mk["GRAM_ALTIN"],0)
ons_s   = fusd(mk["ONS_ALTIN"],0)
btc_s   = fusd(mk["BTC_USD"],0)
eth_s   = fusd(mk["ETH_USD"],0)
brent_s = fusd(mk["PETROL"],1)

bist_chg_html  = fchg(mk["BIST100_CHG"])
btc_chg_html   = fchg(mk["BTC_CHG"])
saat_str       = now.strftime('%H:%M')

# Masaüstü topbar
st.markdown(f"""
<div class='topbar topbar-desktop'>
  <div class='t-logo'>
    <div class='live-dot'></div>
    Emrah<span class='dot'>.</span>AI
    <span class='t-badge'>Finans v6 RT</span>
  </div>
  <div class='t-strip'>
    <div class='t-item'><span class='t-lbl'>BIST 100</span>
      <span class='t-val'>{bist_s}</span>{bist_chg_html}</div>
    <div class='t-item'><span class='t-lbl'>USD/TRY</span>
      <span class='t-val'>{usd_s}</span></div>
    <div class='t-item'><span class='t-lbl'>EUR/TRY</span>
      <span class='t-val'>{eur_s}</span></div>
    <div class='t-item'><span class='t-lbl'>GRAM ALTIN</span>
      <span class='t-val'>{gram_s}</span></div>
    <div class='t-item'><span class='t-lbl'>ONS ALTIN</span>
      <span class='t-val'>{ons_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BTC</span>
      <span class='t-val'>{btc_s}</span>{btc_chg_html}</div>
    <div class='t-item'><span class='t-lbl'>ETH</span>
      <span class='t-val'>{eth_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BRENT</span>
      <span class='t-val'>{brent_s}</span></div>
    <div class='t-item'><span class='t-lbl'>TCMB</span>
      <span class='t-val'>%37,00</span><span class='t-fl'>SABİT</span></div>
    <div class='t-item'><span class='t-lbl'>SAAT</span>
      <span class='t-val'>{now.strftime('%H:%M:%S')}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Mobil topbar
_mob_tmpl = """
<div class='topbar-mobile'>
  <div style='background:#0f172a;padding:10px 14px 6px;border-bottom:2px solid #1e3a5f;'>
    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;'>
      <div style='display:flex;align-items:center;gap:8px;'>
        <div class='live-dot'></div>
        <span style='font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:700;color:#f1f5f9;'>
          PAPRIKA<span style='color:#38bdf8;'>.</span>AI
        </span>
        <span style='font-size:9px;background:#1e3a5f;color:#7dd3fc;padding:2px 7px;border-radius:4px;'>v6 RT</span>
      </div>
      <span style='font-family:IBM Plex Mono,monospace;font-size:12px;color:#94a3b8;'>{SAAT}</span>
    </div>
    <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
                background:#1e3a5f;border-radius:8px;overflow:hidden;margin-bottom:1px;'>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>BIST</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{BIST}</div>
        <div style='font-size:10px;'>{BIST_CHG}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>USD/TL</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{USD}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>GRAM</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{GRAM}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>ONS $</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{ONS}</div>
      </div>
    </div>
    <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
                background:#1e3a5f;border-radius:8px;overflow:hidden;margin-bottom:4px;'>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>BTC</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{BTC}</div>
        <div style='font-size:10px;'>{BTC_CHG}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>EUR/TL</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{EUR}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>BRENT</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{BRENT}</div>
      </div>
      <div style='background:#0d1b2e;padding:7px 8px;'>
        <div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>TCMB</div>
        <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#fbbf24;'>%37,00</div>
      </div>
    </div>
  </div>
</div>
"""
_mob_html = _mob_tmpl.format(
    SAAT=saat_str, BIST=bist_s, BIST_CHG=bist_chg_html,
    USD=usd_s, GRAM=gram_s, ONS=ons_s,
    BTC=btc_s, BTC_CHG=btc_chg_html,
    EUR=eur_s, BRENT=brent_s,
)
st.markdown(_mob_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  1. RADAR — En Yüksek Hacimli 8 Hisse
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class='sw'>
  <div class='sh'>
    <div class='sb'></div>
    <div class='st'><span class='st-long'>En Yüksek Hacimli 8 Hisse — Para Akışı Radarı</span><span class='st-short'>Hacim Radarı</span></div>
    <div class='ss'>yfinance · ~15dk · 60s yenileme</div>
  </div>
""", unsafe_allow_html=True)

if radar_lst:
    cards = "<div class='rg'>"
    for r in radar_lst:
        sin_lbl, sin_cls = sinyal(r["chg"])
        chg_cls = "rc-up" if r["chg"] >= 0 else "rc-dn"
        chg_sym = "▲" if r["chg"] >= 0 else "▼"
        vol_tl  = r.get("vol_tl", 0)
        if vol_tl >= 1_000_000_000:
            vol_str = f"{vol_tl/1_000_000_000:.1f}B ₺"
        elif vol_tl >= 1_000_000:
            vol_str = f"{vol_tl/1_000_000:.0f}M ₺"
        elif vol_tl > 0:
            vol_str = f"{vol_tl/1_000:.0f}K ₺"
        else:
            vol_str = "—"
        cards += f"""
        <div class='rc rc-{sin_cls}'>
          <div class='rc-tic'>{r["sym"]}</div>
          <div class='rc-fiy'>{ftl(r["price"])}</div>
          <div class='rc-vol'>Günlük: {vol_str}</div>
          <span class='pill p-{sin_cls}'>{sin_lbl}</span>
          <div class='{chg_cls}'>{chg_sym} %{abs(r["chg"]):.2f}</div>
        </div>"""
    cards += "</div></div>"
    st.markdown(cards, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  2. STRATEJİK KARAR MATRİSİ — Top 10
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class='sw'>
  <div class='sh'>
    <div class='sb'></div>
    <div class='st'><span class='st-long'>Stratejik Karar Matrisi — Çok Boyutlu Analiz Top 10</span><span class='st-short'>Top 10 Analiz</span></div>
    <div class='ss'>Teknik %40 · Haber/Duygu %25 · Analitik %25 · Sosyal %10 → 100 puan</div>
  </div>
""", unsafe_allow_html=True)

with st.spinner("BIST analizi yapılıyor… (teknik + haber + duygu + analitik)"):
    df_top10 = top10_analiz()

if not df_top10.empty:
    rows_h = ""
    for rank, row in df_top10.iterrows():
        dcls  = "td-u" if row["Degisim"] >= 0 else "td-d"
        chg_s = "▲" if row["Degisim"] >= 0 else "▼"
        fp    = ftl(row["Fiyat"]) if row["Fiyat"] > 0 else "—"
        fh    = ftl(row["Fiyat"] * 1.15) if row["Fiyat"] > 0 else "—"
        puan  = row["Puan"]
        bar_w = min(int(puan), 100)

        tl_h = row.get("TL_Hacim", 0)
        if tl_h >= 1_000_000_000:
            hacim_fmt = f"{tl_h/1_000_000_000:.1f}B ₺"
        elif tl_h >= 1_000_000:
            hacim_fmt = f"{tl_h/1_000_000:.0f}M ₺"
        elif tl_h > 0:
            hacim_fmt = f"{tl_h/1_000:.0f}K ₺"
        else:
            hacim_fmt = "—"

        sinyal_str = row.get("Sinyal", "İZLE")
        if sinyal_str == "GÜÇLÜ AL":
            sin_bg, sin_c = "#dcfce7", "#15803d"
        elif sinyal_str == "AL":
            sin_bg, sin_c = "#eff6ff", "#1d4ed8"
        elif sinyal_str == "DİP BÖLGE":
            sin_bg, sin_c = "#fffbeb", "#92400e"
        elif sinyal_str == "HABER POZ.":
            sin_bg, sin_c = "#f5f3ff", "#6d28d9"
        else:
            sin_bg, sin_c = "#f8fafc", "#475569"

        tek   = int(row.get("Tek_Puan", 0))
        duygu = int(row.get("Duygu_Puan", 0))
        anal  = int(row.get("Analitik", 0))
        sos   = int(row.get("Sosyal", 0))
        haber_sk = row.get("Haber_Sk", 0)
        haber_renk = "#16a34a" if haber_sk >= 0 else "#dc2626"

        rows_h += f"""
        <tr>
          <td><span class='td-r'>{rank}</span></td>
          <td class='td-h'>{row["Hisse"]}</td>
          <td class='td-f'>{fp}</td>
          <td class='td-ht'>{fh}</td>
          <td class='{dcls}'>{chg_s} %{abs(row["Degisim"]):.2f}</td>
          <td>
            <span style='font-size:13px;font-weight:700;color:#2563eb;font-family:Arial,sans-serif;'>{row["RSI"]}</span>
            <span style='font-size:11px;color:#64748b;margin-left:4px;'
            >{'Ucuz' if row["RSI"]<45 else ('Güçlü' if row["RSI"]<65 else 'Pahalı')}</span>
          </td>
          <td>
            <span style='font-size:11px;font-weight:700;color:{haber_renk};'>
            {'▲' if haber_sk>=0 else '▼'} {abs(haber_sk):.1f}</span>
          </td>
          <td>
            <div style='display:flex;align-items:center;gap:6px;'>
              <div style='font-size:13px;font-weight:700;color:#1d4ed8;font-family:Arial,sans-serif;white-space:nowrap;'>{puan:.0f}/100</div>
              <div style='flex:1;min-width:60px;'>
                <div style='background:#f1f5f9;border-radius:3px;height:4px;overflow:hidden;'>
                  <div style='height:100%;width:{bar_w}%;background:linear-gradient(90deg,#2563eb,#38bdf8);border-radius:3px;'></div>
                </div>
                <div style='font-size:9px;color:#94a3b8;margin-top:2px;'>
                  T:{tek} D:{duygu} A:{anal} S:{sos}
                </div>
              </div>
            </div>
          </td>
          <td>
            <span style='font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;
              background:{sin_bg};color:{sin_c};white-space:nowrap;'>{sinyal_str}</span>
          </td>
          <td class='td-a' style='font-size:12px;'>{hacim_fmt}</td>
        </tr>"""

    st.markdown(f"""
    <div class='mw'>
      <table class='mt'>
        <thead><tr>
          <th>#</th><th>Hisse</th><th>Fiyat</th><th>Hedef (+15%)</th>
          <th>Değişim</th><th>RSI</th><th>Haber Sk.</th>
          <th>Toplam Puan <span style='font-weight:400;font-size:10px;'>(T·D·A·S)</span></th>
          <th>Sinyal</th><th>TL Hacim</th>
        </tr></thead>
        <tbody>{rows_h}</tbody>
      </table>
    </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='sw'><p style='color:#dc2626;font-size:13px;'>Analiz verisi alınamadı. Bağlantı kontrol ediniz.</p></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  3. SENSOR PANELLERİ
# ═══════════════════════════════════════════════════════════════════════════════

with st.spinner("Derin analiz hesaplanıyor…"):
    fp_lst = fp_radar()

vol_bist  = mk.get("BIST100_VOL", 0)
radar_vol = sum(r.get("vol_tl", 0) for r in radar_lst) if radar_lst else 0
hacim_gosterge = radar_vol if radar_vol > 0 else (vol_bist * mk.get("BIST100", 13000) / 100_000 if vol_bist > 0 else 0)
chg_b     = mk.get("BIST100_CHG", 0)
alis_pct  = min(max(50 + chg_b * 4, 30), 80)
satis_pct = 100 - alis_pct
hacim_str = (f"{hacim_gosterge/1_000_000_000:.1f}B ₺" if hacim_gosterge >= 1e9
             else f"{hacim_gosterge/1_000_000:.0f}M ₺" if hacim_gosterge >= 1e6 else "—")
duygu_bar_w = duygu_val

fp_satirlar = ""
if fp_lst:
    for i, r in enumerate(fp_lst, 1):
        hisse = r.get("Hisse", "")
        fiyat = ftl(r.get("Fiyat", 0))
        rsi_v = r.get("RSI", 0)
        dip_v = r.get("Dip%", 0)
        puan  = r.get("Puan", 0)
        etikt = r.get("Etiket", "DEĞER")
        bdg_cls = "fpb-g" if ("UCUZ" in etikt or "DİP" in etikt) else ("fpb-b" if "DÖNÜŞ" in etikt else "fpb-a")
        bar_w = int(puan)
        fp_satirlar += (
            "<div class='fp-row'>"
              "<div class='fp-left'>"
                f"<span class='fp-name'>{i}. {hisse}</span>"
                f"<span class='fp-meta'>{fiyat} &nbsp;·&nbsp; RSI:{rsi_v} &nbsp;·&nbsp; 52H:%{dip_v:.0f} &nbsp;·&nbsp; Puan:{puan}</span>"
                f"<div class='fp-bar-bg'><div class='fp-bar-fill' style='width:{bar_w}%;'></div></div>"
              "</div>"
              f"<span class='fp-bdg {bdg_cls}'>{etikt}</span>"
            "</div>"
        )
else:
    fp_satirlar = "<div style='color:#475569;font-size:12px;padding:14px 0;text-align:center;'>Veri hesaplanıyor…</div>"

hc_bar_cls = "hc-bar-g" if chg_b >= 0 else "hc-bar-r"
yon_icon2  = "📈" if chg_b >= 0 else "📉"
hc_renk    = "#16a34a" if chg_b >= 0 else "#dc2626"
hc_chg_sym = "▲ +" if chg_b > 0 else "▼ "

kart1 = (
    "<div style='"
    "background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #2563eb;"
    "border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;"
    "'>"
    "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#2563eb;"
    "margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    "💎 F/P Değerleme Radarı — Top 5</div>"
    + fp_satirlar
    + "</div>"
)

kart2 = (
    f"<div style='"
    f"background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #16a34a;"
    f"border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;"
    f"'>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    f"letter-spacing:1.5px;text-transform:uppercase;color:#16a34a;"
    f"margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    f"📈 Günlük Para Akışı &amp; Hacim</div>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:26px;font-weight:700;"
    f"color:{hc_renk};margin:4px 0 3px;'>{yon_icon2} {hacim_str}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>24 büyük hisse · ~15dk gecikme</div>"
    f"<div style='background:#e2e8f0;border-radius:6px;height:6px;overflow:hidden;margin-bottom:7px;'>"
    f"<div class='{hc_bar_cls}' style='width:{int(alis_pct)}%;height:100%;border-radius:6px;'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:12px;font-weight:700;margin-bottom:10px;'>"
    f"<span style='color:#16a34a;'>ALIŞ %{alis_pct:.0f}</span>"
    f"<span style='color:#dc2626;'>SATIŞ %{satis_pct:.0f}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>BIST100</span><span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:#1e293b;'>{bist_s}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>Değişim</span>"
    f"<span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:{hc_renk};'>{hc_chg_sym}%{abs(chg_b):.2f}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>İşlem Hacmi</span>"
    f"<span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:#2563eb;'>{hacim_str}</span></div>"
    f"</div>"
)

kart3 = (
    f"<div style='"
    f"background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #7c3aed;"
    f"border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;"
    f"'>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    f"letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;"
    f"margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    f"🧠 BIST Duygu Endeksi</div>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:48px;font-weight:700;"
    f"line-height:1;color:{duygu_renk};margin:4px 0 2px;'>{duygu_val}</div>"
    f"<div style='font-size:13px;font-weight:600;color:{duygu_renk};margin-bottom:3px;'>{duygu_lbl}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>RSI Ort: <b style='color:#1e293b;'>{rsi_ort}</b></div>"
    f"<div style='background:#e2e8f0;border-radius:8px;height:7px;overflow:hidden;margin-bottom:4px;'>"
    f"<div style='height:100%;width:{duygu_bar_w}%;background:{duygu_renk};border-radius:8px;'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;"
    f"font-family:\"IBM Plex Mono\",monospace;margin-bottom:10px;'>"
    f"<span>KORKU</span><span>NÖTR</span><span>AÇGÖZLÜLÜK</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:11px;'>"
    f"<span style='color:#64748b;'>Baz</span><span style='color:#475569;font-weight:600;'>BIST100 — 20 hisse</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:11px;'>"
    f"<span style='color:#64748b;'>Yükselen / Toplam</span>"
    f"<span style='color:#16a34a;font-weight:700;font-family:\"IBM Plex Mono\",monospace;'>{yukselen_sayi} / {toplam_sayi}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:11px;'>"
    f"<span style='color:#64748b;'>Yöntem</span><span style='color:#475569;'>RSI %60 · Yön %30 · Mom %10</span></div>"
    f"</div>"
)

sensor_html = (
    "<div style='padding:16px 24px 12px;'>"
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>"
    "<div style='width:4px;height:20px;background:#2563eb;border-radius:3px;flex-shrink:0;'></div>"
    "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:11px;font-weight:700;"
    "letter-spacing:1.8px;text-transform:uppercase;color:#2563eb;'><span class='st-long'>Derin Analiz Sensörleri</span><span class='st-short'>Sensörler</span></span>"
    "<span style='margin-left:auto;font-size:11px;color:#94a3b8;'>F/P · Para Akışı · Duygu Endeksi</span>"
    "</div>"
    "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start;'>"
    + kart1 + kart2 + kart3 +
    "</div>"
    "</div>"
)

st.markdown(sensor_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  4. PİYASA İSTİHBARATI
# ═══════════════════════════════════════════════════════════════════════════════

with st.spinner("İstihbarat analizi yapılıyor…"):
    istihbarat_lst = istihbarat_analiz()

tcmb_faiz = 37.0
if chg_b > 1.5:
    bist_strateji = "Endeks güçlü yükseliyor. Momentum hisselerine odaklan: THYAO, ASELS, YKBNK."
elif chg_b > 0:
    bist_strateji = "Endeks ılımlı pozitif. Seçici alım fırsatı — düşük RSI'li hisseler cazip."
elif chg_b > -1:
    bist_strateji = "Endeks yatay. Dip bölgelerinde biriktirme yapılabilir. Bankacılık sektörünü izle."
else:
    bist_strateji = "Endeks baskılı. Savunma hisseleri ve altın öne çıkabilir. Temkinli pozisyon al."

if mk["PETROL"] > 100:
    petrol_yorum = f"Brent {brent_s} — 100$/varil üstünde. AKSEN/ENJSA/ZOREN olumlu, TUPRS baskılı."
elif mk["PETROL"] > 80:
    petrol_yorum = f"Brent {brent_s} — Normal seviyelerde. TUPRS için nötr görünüm."
else:
    petrol_yorum = f"Brent {brent_s} — Düşük petrol. TUPRS marjları için olumlu."

btc_val = mk.get("BTC_USD", 0)
kripto_yorum = ("Risk iştahı yüksek. Kripto rallisi BIST'e pozitif." if btc_val > 90000
                else "BTC konsolidasyon bandında. Makro beklenti odaklı."
                if btc_val > 70000 else "BTC baskılı. Risk-off ortamı, savunma hisselerine yönel.")

def istihbarat_satirlari(liste):
    html = ""
    for item in liste[:4]:
        title_safe = item["title"].replace("<","&lt;").replace(">","&gt;")
        duygu = item["duygu"]
        sektor = item["sektor"].upper()
        zaman  = item["zaman"]
        link   = item["link"]
        if duygu == "pozitif":
            duygu_bg, duygu_c, duygu_ic = "#f0fdf4","#15803d","▲"
        elif duygu == "negatif":
            duygu_bg, duygu_c, duygu_ic = "#fef2f2","#b91c1c","▼"
        else:
            duygu_bg, duygu_c, duygu_ic = "#f8fafc","#475569","─"

        if link and link.startswith("http"):
            baslik_html = (f"<a href='{link}' target='_blank' "
                           f"style='color:#1e293b;text-decoration:none;font-weight:600;"
                           f"border-bottom:1px dashed #94a3b8;'>{title_safe} "
                           f"<span style='font-size:10px;color:#2563eb;'>↗</span></a>")
        else:
            baslik_html = f"<span style='font-weight:600;color:#1e293b;'>{title_safe}</span>"

        html += (
            f"<div style='padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:5px;'>"
            f"<span style='font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;"
            f"background:{duygu_bg};color:{duygu_c};'>{duygu_ic} {sektor}</span>"
            f"<span style='font-size:10px;color:#94a3b8;font-family:IBM Plex Mono,monospace;'>{zaman}</span>"
            f"</div>"
            f"<div style='font-size:12px;line-height:1.5;'>{baslik_html}</div>"
            f"</div>"
        )
    if not html:
        html = "<div style='font-size:12px;color:#94a3b8;padding:12px 0;'>Haberler yükleniyor…</div>"
    return html

ist_sol = istihbarat_satirlari(istihbarat_lst[:4])
ist_sag_data = [
    {"title": f"TCMB faizi %{tcmb_faiz:.0f} sabit · Haziran indirim beklentisi gündemde.", "zaman": now.strftime("%d.%m %H:%M"), "link":"", "duygu":"nötr","sektor":"tcmb"},
    {"title": f"USD/TRY {usd_s} · GRAM ALTIN {gram_s} · ONS {ons_s}", "zaman": now.strftime("%d.%m %H:%M"), "link":"","duygu":"nötr","sektor":"döviz"},
    {"title": petrol_yorum, "zaman": now.strftime("%d.%m %H:%M"), "link":"","duygu":"nötr","sektor":"petrol"},
    {"title": f"BTC {btc_s} {'+' if mk.get('BTC_CHG',0)>=0 else ''}%{mk.get('BTC_CHG',0):.2f} (24s) · {kripto_yorum}", "zaman": now.strftime("%d.%m %H:%M"), "link":"","duygu":"nötr","sektor":"kripto"},
]
ist_sag = istihbarat_satirlari(ist_sag_data)

st.markdown(f"""
<div class="sw">
  <div class="sh">
    <div class="sb"></div>
    <div class="st"><span class="st-long">Piyasa İstihbaratı — Hisse Seçim Rehberi</span><span class="st-short">İstihbarat</span></div>
    <div class="ss">Haber + Duygu Analizi · {now.strftime("%d.%m.%Y %H:%M")} itibarıyla</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <div style="background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #2563eb;
                border-radius:12px;padding:18px 20px;">
      <div style="font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;
                  letter-spacing:1.5px;text-transform:uppercase;color:#2563eb;
                  margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;">
        🔍 Borsa Haber Analizi — Canlı Duygu</div>
      {ist_sol}
    </div>
    <div style="background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #d97706;
                border-radius:12px;padding:18px 20px;">
      <div style="font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;
                  letter-spacing:1.5px;text-transform:uppercase;color:#d97706;
                  margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;">
        🌐 Makro & Strateji Rehberi</div>
      <div style="font-size:13px;font-weight:600;color:#1e293b;margin-bottom:8px;">
        BIST {bist_s} · {bist_strateji}</div>
      {ist_sag}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  5. SON DAKİKA HABERLERİ + SOSYAL TREND
# ═══════════════════════════════════════════════════════════════════════════════

with st.spinner("Haberler ve sosyal gündem yükleniyor…"):
    sosyal_lst = sosyal_trend_cek()

st.markdown(f"""
<div class="sw">
  <div class="sh">
    <div class="sb"></div>
    <div class="st"><span class="st-long">Canlı Haber Akışı & Sosyal Gündem</span><span class="st-short">Haberler & Gündem</span></div>
    <div class="ss">RSS + Google News · Twitter/X Proxy · 5dk yenileme · Tıkla → habere git</div>
  </div>
""", unsafe_allow_html=True)

def haber_satirlari(liste, max_n=6):
    html = ""
    for zaman, kaynak, baslik, link in liste[:max_n]:
        baslik_safe = baslik.replace("<","&lt;").replace(">","&gt;")
        if link and link.startswith("http"):
            baslik_html = (f"<a href='{link}' target='_blank' "
                           f"style='color:#1e293b;text-decoration:none;font-weight:600;"
                           f"border-bottom:1px dashed #94a3b8;'>{baslik_safe} "
                           f"<span style='font-size:10px;color:#2563eb;'>↗</span></a>")
        else:
            baslik_html = f"<span style='font-weight:500;color:#1e293b;'>{baslik_safe}</span>"
        html += (
            f"<div style='display:flex;align-items:flex-start;gap:10px;"
            f"padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<span style='font-family:IBM Plex Mono,monospace;font-size:11px;font-weight:700;"
            f"color:#dc2626;min-width:70px;flex-shrink:0;margin-top:1px;'>{zaman}</span>"
            f"<div style='font-size:13px;line-height:1.5;'>"
            f"<span style='font-size:10px;font-weight:700;background:#eff6ff;color:#1d4ed8;"
            f"padding:1px 6px;border-radius:3px;margin-right:5px;white-space:nowrap;'>{kaynak}</span>"
            f"{baslik_html}</div>"
            f"</div>"
        )
    return html or "<div style='color:#94a3b8;font-size:12px;padding:12px 0;'>Yükleniyor…</div>"

def trend_satirlari(liste, max_n=6):
    html = ""
    for zaman, icon, baslik, link in liste[:max_n]:
        baslik_safe = baslik.replace("<","&lt;").replace(">","&gt;")
        if link and link.startswith("http"):
            baslik_html = (f"<a href='{link}' target='_blank' "
                           f"style='color:#1e293b;text-decoration:none;font-weight:600;"
                           f"border-bottom:1px dashed #94a3b8;'>{baslik_safe} "
                           f"<span style='font-size:10px;color:#7c3aed;'>↗</span></a>")
        else:
            baslik_html = f"<span style='font-weight:500;color:#1e293b;'>{baslik_safe}</span>"
        html += (
            f"<div style='display:flex;align-items:flex-start;gap:10px;"
            f"padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<span style='font-family:IBM Plex Mono,monospace;font-size:11px;font-weight:700;"
            f"color:#7c3aed;min-width:70px;flex-shrink:0;margin-top:1px;'>{zaman}</span>"
            f"<div style='font-size:13px;line-height:1.5;'>"
            f"<span style='font-size:12px;margin-right:5px;'>{icon}</span>"
            f"{baslik_html}</div>"
            f"</div>"
        )
    return html or "<div style='color:#94a3b8;font-size:12px;padding:12px 0;'>Yükleniyor…</div>"

if haberler:
    def zaman_sort_key(item):
        try: return item[0]
        except: return "00:00"
    haberler_sorted = sorted(haberler, key=zaman_sort_key, reverse=True)
    haber_html_str = haber_satirlari(haberler_sorted, 7)
else:
    haber_html_str = (
        "<div style='background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;"
        "padding:10px 14px;font-size:12px;color:#92400e;'>"
        "⚠️ Haberler alınamıyor. 60s sonra yenileniyor.<br>"
        "<a href='https://www.kap.org.tr/tr/bildirim-sorgu' target='_blank' style='color:#1d4ed8;'>KAP</a> · "
        "<a href='https://bigpara.hurriyet.com.tr' target='_blank' style='color:#1d4ed8;'>Bigpara</a>"
        "</div>"
    )

trend_html_str = trend_satirlari(sosyal_lst, 7)

haber_news_html = (
    "<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>"

    "<div style='background:#fff;border:1.5px solid #dde3ec;border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#1d4ed8;"
    "margin-bottom:12px;padding-bottom:11px;border-bottom:1.5px solid #e2e8f0;'>"
    "🌍 Borsa & Ekonomi Haberleri</div>"
    + haber_html_str +
    "</div>"

    "<div style='background:#fff;border:1.5px solid #dde3ec;border-left:3px solid #7c3aed;"
    "border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;"
    "margin-bottom:6px;padding-bottom:6px;border-bottom:1.5px solid #e2e8f0;'>"
    "🐦 Gündemdekiler — BIST100 Finans Gündemi</div>"
    "<div style='font-size:11px;color:#94a3b8;margin-bottom:10px;'>"
    "Bugünkü haberler · Tarih filtreli · Saat sırası (yeniden eskiye)</div>"
    + trend_html_str +
    "</div>"

    "</div></div>"
)
st.markdown(haber_news_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class='footer'>
  <span>PAPRIKA.AI © 2026 — Elite Terminal v6.0-fix</span>
  <span>Güncelleme: {now.strftime('%d.%m.%Y %H:%M:%S')} | ⏱ 60s oto-yenileme</span>
  <span>Hisse: yfinance ~15dk · Döviz/Altın: TCMB · Kripto: CoinGecko · Haber: G.News · ⚠️ Yatırım tavsiyesi değildir</span>
</div>
""", unsafe_allow_html=True)
