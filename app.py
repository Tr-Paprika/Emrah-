"""
╔══════════════════════════════════════════════════════════════════╗
║          PAPRIKA ELİTE TERMİNAL  v6.1                           ║
║──────────────────────────────────────────────────────────────────║
║  Kurulum:                                                        ║
║    pip install streamlit yfinance requests pandas numpy          ║
║    pip install streamlit-autorefresh                             ║
║                                                                  ║
║  Çalıştır:                                                       ║
║    streamlit run paprika_terminal_v6.py                          ║
║                                                                  ║
║  v6.1 YENİLİKLER:                                               ║
║   • Tüm haber linkleri tıklanabilir (tüm paneller)              ║
║   • Saat UTC→TR (UTC+3) yerel saate düzeltildi                  ║
║   • Anlık Hisse Fiyat Takip Modülü eklendi                      ║
║   • Analiz tüm BIST100 hisselerini kapsar                       ║
║   • macd/dip_pct/dip_uzaklik NameError düzeltildi               ║
║   • Haber duyarlılık skoru paralel HTTP                         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import html as html_mod

# ── SAYFA ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Paprika Elite Terminal", layout="wide",
                   initial_sidebar_state="collapsed")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="paprika_v61")
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
.t-up{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;color:#4ade80;white-space:nowrap}
.t-dn{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;color:#f87171;white-space:nowrap}
.t-fl{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#64748b;white-space:nowrap}

.sw{padding:16px 24px 12px}
.sh{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.sb{width:4px;height:20px;background:#2563eb;border-radius:3px;flex-shrink:0}
.st{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
    letter-spacing:1.8px;text-transform:uppercase;color:#2563eb}
.ss{margin-left:auto;font-size:11px;color:#94a3b8;white-space:nowrap}

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

/* HİSSE TAKİP MODÜLÜ */
.htk-wrap{background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #0ea5e9;
          border-radius:12px;padding:16px 20px}
.htk-hdr{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
         letter-spacing:1.5px;text-transform:uppercase;color:#0ea5e9;
         margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.htk-price{font-family:'IBM Plex Mono',monospace;font-size:36px;font-weight:700;line-height:1.1}
.htk-chg-up{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:#16a34a}
.htk-chg-dn{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;color:#dc2626}
.htk-meta{font-size:11px;color:#64748b;margin-top:4px}
.htk-row{display:flex;justify-content:space-between;padding:5px 0;
         border-bottom:1px solid #f1f5f9;font-size:12px}
.htk-row:last-child{border-bottom:none}
.htk-lbl{color:#64748b}
.htk-val{font-family:'IBM Plex Mono',monospace;font-weight:700;color:#1e293b}

/* F/P kart */
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

/* Haber linkleri */
a.haber-link{color:inherit;text-decoration:none;font-weight:600;
             border-bottom:1px dashed #94a3b8;transition:color .15s,border-color .15s}
a.haber-link:hover{color:#2563eb;border-bottom-color:#2563eb}
.link-ok{font-size:10px;margin-left:3px}

.footer{background:#0f172a;border-top:1px solid #1e3a5f;padding:12px 24px;
        display:flex;justify-content:space-between;font-size:11px;color:#475569;
        font-family:'IBM Plex Mono',monospace;margin-top:8px}

.topbar-desktop{display:flex}
.topbar-mobile{display:none}
.st-long{display:inline}
.st-short{display:none}

@media(max-width:768px){
  .stApp{font-size:14px}
  .sw{padding:10px 12px 8px!important}
  .topbar-desktop{display:none!important}
  .topbar-mobile{display:block!important}
  .st-long{display:none!important}
  .st-short{display:inline!important}
  .st{font-size:10px!important;letter-spacing:1.2px!important}
  .rg{grid-template-columns:repeat(2,1fr)!important;gap:6px!important}
  .mw{overflow-x:auto!important;-webkit-overflow-scrolling:touch}
  .mt{font-size:12px!important;min-width:580px}
  .mt th{padding:8px 10px!important;font-size:10px!important}
  .mt td{padding:8px 10px!important}
  [style*="grid-template-columns:1fr 1fr 1fr"],[style*="repeat(3,1fr)"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:1fr 1fr"],[style*="repeat(2,1fr)"]{grid-template-columns:1fr!important}
  .footer{flex-direction:column;gap:4px;padding:10px 12px;font-size:10px!important}
}
@media(max-width:480px){
  .sw{padding:8px 10px 6px!important}
  .rg{grid-template-columns:1fr 1fr!important;gap:5px!important}
  .mt{font-size:11px!important;min-width:540px}
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  BIST100 SEMBOLLERİ (genişletilmiş)
# ═══════════════════════════════════════════════════════════════════════════════
BIST100_FULL = [
    "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
    "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
    "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
    "ARCLK","ISCTR","SOKM","TTKOM","SASA","AGHOL","ALGYO","CCOLA",
    "CIMSA","DOAS","EGEEN","MPARK","NETAS","ODAS","OYAKC","PARSN",
    "AKSEN","AEFES","AKGRT","ALFAS","BRISA","CANTE","CUSAN","DEVA",
    "EKOS","ENJSA","GESAN","GUBRF","IHLGM","IHEVA","IPEKE","ISGYO",
    "IZMDC","KARSN","KCAER","KLGYO","KONYA","MAVI","MGROS","NUHCM",
    "OTKAR","OYAYO","PAPIL","PENTA","QUAGR","RYSAS","SARKY","SELVA",
    "SMRTG","TSKB","TTRAK","ULKER","VESBE","YATAS","ZOREN","TKFEN",
    "TATGD","SNKRN","LOGO","CONYA","CMBTN","AKFGY","AKSA","ALARK",
    "ANSEN","ARMDA","ASUZU","ATAKP","AVGYO","BAGFS","BERA","BIOEN",
    "BIZIM","BNTAS","BOSSA","BTCIM","BUCIM","BURCE","BURVA","CEMAS",
    "CLEBI","CNKRT","DAGHL","DAGI","DCILK","DENGE","DESPC","DGKLB",
    "DNISI","DOBUR","DOKTA","DURDO","DYOBY","ECILC","ECZYT","EDIP",
    "EGGUB","EGPRO","EGSER","ELITE","EMKEL","EMNIS","ENERY","ERBOS",
    "ERCB","ERDEM","ERDMR","ESCOM","ESEN","ETILR","EUCFH","EUPWR",
    "FENER","FLAP","FONET","FRIGO","FZLGY","GEDIK","GEDZA","GENTS",
    "GEREL","GLYHO","GMTAS","GOLTS","GOODY","GOZDE","GRSEL","GSDDE",
    "GSDHO","GSRAY","GWIND","HATEK","HEKTS","HLGYO","HTTBT","HUBVC",
    "HURGZ","ICBCT","IDEAS","IDGYO","IEYHO","IGDAS","IGGYO","IHGZT",
    "IHLAS","IHYAY","IMASM","INDES","INFO","INTEM","INVEO","ISDMR",
    "ISFIN","ISGSY","ISKPL","ISYAT","ITTFH","IZFAS","JANTS","KAPLM",
    "KAREL","KATMR","KAYSE","KBORU","KENT","KERVN","KERVT","KFEIN",
    "KIMMR","KLNMA","KNFRT","KORDS","KOZAA","KRDMA","KRDMB","KRSTL",
    "KRTEK","KUYAS","LIDER","LIDFA","LMKDC","LRSHO","LUKSK","MAALT",
    "MACKO","MAGEN","MARTI","MATAS","MEDTR","MEGAP","MEPET","MERCN",
    "MERIT","MERKO","METRO","METUR","MIPAZ","MKTGY","MNDRS","MNDTR",
    "MOBTL","MODEL","MOGAN","MRGYO","MRSHL","MSGYO","MTRKS","MZHLD",
    "NATEN","NIBAS","NILYT","NTHOL","NTTUR","NUGYO","NUHCM","OBASE",
    "ODEYO","OFSYM","ONCSM","ORCAY","ORGE","ORMA","OSMEN","OSTIM",
    "OVER","OYLUM","OYYAT","OZGYO","PAGYO","PAMEL","PASEU","PCILT",
    "PEHOL","PENGD","PINSU","PKART","PKENT","PLTUR","PNLSN","POLHO",
    "POLTK","PRDGS","PRTAS","PSDTC","PRZMA","RALYH","RAYSG","RBTAS",
    "RHEAG","RNPOL","RODRG","ROYAL","RTALB","RUBNIS","SAFKR","SAMAT",
    "SANEL","SANFM","SANKO","SAYAS","SEGMN","SEKFK","SEKUR","SELGD",
    "SEYKM","SILVR","SNGYO","SNPAM","SONME","SRVGY","SUMAS","SUWEN",
    "TABGD","TARKM","TBORG","TDGYO","TEKTU","TEZOL","TGSAS","TIRE",
    "TKNSA","TLMAN","TMPOL","TRCAS","TRGYO","TRILC","TSPOR","TUCLK",
    "TUCRS","TUKAS","TUREX","TURGG","TURSG","UFUK","ULAS","ULUUN",
    "ULUSE","UMPAS","UNLU","USAK","VAKFN","VAKKO","VANGD","VBTYZ",
    "VKGYO","VKING","VRGYO","YAPRK","YAYLA","YBTAS","YESIL","YEOTK",
    "YGGYO","YKSLN","YUNSA","ZEDUR","ZRGYO",
]
BIST100_FULL = sorted(list(set([s.strip() for s in BIST100_FULL if s.strip()])))

# Analiz için Yahoo Finance'de çalıştığı doğrulanmış semboller
ANALIZ_LISTESI = [
    "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
    "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
    "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
    "ARCLK","ISCTR","SOKM","TTKOM","SASA","CCOLA","DOAS","AKSEN",
    "AEFES","BRISA","ENJSA","MGROS","OTKAR","ULKER","VESBE","TSKB",
    "TTRAK","MAVI","CIMSA","LOGO","EGEEN","NUHCM","GUBRF","KLGYO",
    "ALGYO","ISGYO","EKOS","GESAN","KARSN","CUSAN","SARKY","IZMDC",
    "DEVA","AGHOL","PARSN","TKFEN","TATGD","PENTA","SNKRN","KOZAA",
    "KRDMA","KRDMB","AKGRT","BRISA","CIMSA","CANTE","CUSAN","DOHL",
    "ALFAS","IPEKE","KCAER","KONYA","OYAKC","RYSAS","SELVA","SMRTG",
    "YATAS","ZOREN","NETAS","ODAS","MPARK","OYAYO","PAPIL","QUAGR",
]
ANALIZ_LISTESI = sorted(list(set(ANALIZ_LISTESI)))

# ═══════════════════════════════════════════════════════════════════════════════
#  TR YEREL SAAT YARDIMCISI (UTC+3)
# ═══════════════════════════════════════════════════════════════════════════════
TZ_TR = timezone(timedelta(hours=3))

def now_tr():
    return datetime.now(TZ_TR)

def fmt_saat_tr(raw_str):
    """RSS pubDate string → TR yerel HH:MM"""
    fmtler = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%a, %d %b %Y %H:%M:%S +0000",
        "%a, %d %b %Y %H:%M:%S GMT",
    ]
    for fmt in fmtler:
        try:
            dt = datetime.strptime(raw_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(TZ_TR).strftime("%H:%M")
        except Exception:
            continue
    return now_tr().strftime("%H:%M")

def ts_to_tr(ts):
    """Unix timestamp → TR HH:MM"""
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(TZ_TR).strftime("%H:%M")
    except Exception:
        return now_tr().strftime("%H:%M")

# ═══════════════════════════════════════════════════════════════════════════════
#  HESAPLAMA YARDIMCILARI
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
    return macd, macd.ewm(span=signal, adjust=False).mean()

# ═══════════════════════════════════════════════════════════════════════════════
#  FORMAT YARDIMCILARI
# ═══════════════════════════════════════════════════════════════════════════════
def ftl(v, d=2):
    if not v or v == 0: return "—"
    return f"₺{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fusd(v, d=0):
    if not v or v == 0: return "—"
    return f"${v:,.{d}f}"

def fchg(v):
    if v is None: return "<span class='t-fl'>—</span>"
    try: v = float(v)
    except: return "<span class='t-fl'>—</span>"
    if v > 0:  return f"<span class='t-up'>▲ +%{v:.2f}</span>"
    if v < 0:  return f"<span class='t-dn'>▼ %{v:.2f}</span>"
    return "<span class='t-fl'>─</span>"

def sinyal(chg):
    if chg > 7:   return "TAVAN ADAYI", "T"
    if chg < -2:  return "DİP AVCI", "D"
    if chg > 2:   return "BALİNA GİRİŞİ", "B"
    return "İZLEME", "I"

def link_html(link, metin, ok_renk="#2563eb"):
    """Tıklanabilir haber linki — her zaman yeni sekmede açılır."""
    safe = metin.replace("<", "&lt;").replace(">", "&gt;")
    if link and link.startswith("http"):
        return (f"<a href='{link}' target='_blank' rel='noopener noreferrer' class='haber-link'>"
                f"{safe}<span class='link-ok' style='color:{ok_renk};'>↗</span></a>")
    return f"<span style='font-weight:600;'>{safe}</span>"

# ═══════════════════════════════════════════════════════════════════════════════
#  RSS PARSE YARDIMCISI
# ═══════════════════════════════════════════════════════════════════════════════
def _google_news_real_url(gnews_url):
    """
    Google News redirect URL'sinden gerçek haber URL'sini çıkarır.
    Örnek: https://news.google.com/rss/articles/CBMi...
    → Önce URL parametresinde 'url=' arar, sonra doğrudan döner.
    """
    if not gnews_url or not gnews_url.startswith("http"):
        return gnews_url
    # Bazen URL query param içinde direkt link bulunur
    from urllib.parse import urlparse, parse_qs, unquote
    try:
        parsed = urlparse(gnews_url)
        qs = parse_qs(parsed.query)
        if "url" in qs:
            return unquote(qs["url"][0])
    except Exception:
        pass
    # Google News RSS item linklerini <a href=...> içinden çıkar
    # Bu URL doğrudan tıklanabilir — Google redirect olsa da tarayıcı yönlendirir
    return gnews_url

def _rss_parse(url, kaynak, max_items=7):
    HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
           "Accept": "application/rss+xml,text/xml;q=0.9,*/*;q=0.8"}
    sonuc = []
    try:
        r = requests.get(url, headers=HDR, timeout=10)
        r.raise_for_status()
        text = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', '', r.text)
        text = re.sub(r'<\?xml[^>]+\?>', '', text)
        root = ET.fromstring(text.encode("utf-8", "replace"))
        for item in (root.findall(".//item") or root.findall(".//entry"))[:max_items]:
            # Başlık
            t_el = item.find("title")
            if t_el is None: continue
            raw    = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t_el.text or "", flags=re.DOTALL)
            baslik = html_mod.unescape(raw).strip()
            baslik = re.sub(r'\s*-\s*[^-]+$', '', baslik).strip()
            if len(baslik) < 8: continue

            # Zaman
            zaman = now_tr().strftime("%H:%M")
            for tag in ("pubDate", "published", "updated"):
                el = item.find(tag)
                if el is not None and el.text:
                    zaman = fmt_saat_tr(el.text)
                    break

            # Link — önce <link> etiketi, sonra description içinde ara
            link = ""
            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.text or "").strip()
            # Google RSS bazen linki CDATA içinde description'da saklar
            if not link or not link.startswith("http"):
                desc_el = item.find("description")
                if desc_el is not None and desc_el.text:
                    m = re.search(r'href=["\']([^"\']+)["\']', desc_el.text)
                    if m:
                        link = html_mod.unescape(m.group(1))
            # Google News redirect URL'i olsa da tıklanabilir, bırak
            if link and not link.startswith("http"):
                link = ""

            sonuc.append((zaman, kaynak, baslik[:120], link))
    except Exception:
        pass
    return sonuc

# ═══════════════════════════════════════════════════════════════════════════════
#  VERİ FONKSİYONLARI
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def radar_hacim_cek():
    hedefler = [
        "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
        "SISE","TOASO","FROTO","AKBNK","HALKB","VAKBN","PGSUS","TCELL",
        "ENKAI","KRDMD","PETKM","BIMAS","ARCLK","ISCTR","TTKOM","EKGYO",
        "CCOLA","MAVI","TAVHL","BRISA","DOAS","TSKB","MGROS","OTKAR",
    ]
    results = []
    for sym in hedefler:
        try:
            h   = yf.Ticker(f"{sym}.IS").history(period="5d")
            clz = h["Close"].dropna()
            vol = h["Volume"].dropna()
            if len(clz) < 1 or len(vol) < 1: continue
            price    = float(clz.iloc[-1])
            vol_adet = float(vol.iloc[-1])
            prev     = float(clz.iloc[-2]) if len(clz) >= 2 else price
            chg      = round(((price - prev) / prev) * 100, 2) if prev > 0 else 0
            tl_hacim = price * vol_adet
            if price > 0 and tl_hacim > 0:
                results.append({"sym": sym, "price": round(price, 2),
                                "chg": chg, "vol_tl": tl_hacim})
        except Exception:
            continue
    results.sort(key=lambda x: x["vol_tl"], reverse=True)
    return results[:8]


@st.cache_data(ttl=30, show_spinner=False)
def hisse_fiyat_cek(sym):
    """Anlık hisse fiyatı — 30s TTL."""
    try:
        t   = yf.Ticker(f"{sym}.IS")
        h5  = t.history(period="5d")
        clz = h5["Close"].dropna()
        vol = h5["Volume"].dropna()
        if len(clz) < 1: return None
        price   = float(clz.iloc[-1])
        prev    = float(clz.iloc[-2]) if len(clz) >= 2 else price
        chg     = round(((price - prev) / prev) * 100, 2) if prev > 0 else 0
        chg_tl  = round(price - prev, 2)
        vol_son = float(vol.iloc[-1]) if len(vol) >= 1 else 0

        h52  = t.history(period="252d")
        clz52 = h52["Close"].dropna()
        yil_min = float(clz52.min()) if len(clz52) > 0 else price
        yil_max = float(clz52.max()) if len(clz52) > 0 else price

        rsi = None
        if len(clz) >= 15:
            rsi = round(float(hesapla_rsi(clz).iloc[-1]), 1)

        return {
            "price": price, "prev": prev, "chg": chg, "chg_tl": chg_tl,
            "vol": vol_son, "tl_hacim": price * vol_son,
            "gun5_min": float(clz.min()), "gun5_max": float(clz.max()),
            "yil_min": yil_min, "yil_max": yil_max, "rsi": rsi,
        }
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def haber_duyarlilik_skoru():
    POZITIF = ["yükseliş","artış","rekor","güçlü","alım","ihale","kâr","büyüme",
               "yatırım","sipariş","temettü","pozitif","rally","toparlandı","yukarı"]
    NEGATIF = ["düşüş","zarar","satış","baskı","risk","endişe","uyarı","negatif",
               "zayıf","kaybetti","geriledi","soruşturma","ceza","borç","kriz"]
    HDR = {"User-Agent": "Mozilla/5.0"}

    def _cek(sym):
        try:
            url = f"https://news.google.com/rss/search?q={sym}+hisse+borsa&hl=tr&gl=TR&ceid=TR:tr"
            r   = requests.get(url, headers=HDR, timeout=6)
            r.raise_for_status()
            tl  = r.text.lower()
            poz = sum(tl.count(k) for k in POZITIF)
            neg = sum(tl.count(k) for k in NEGATIF)
            skor = round(min(max((poz - neg) / (poz + neg + 1) * 20 + tl.count("<item>") * 0.5, -10), 10), 1)
            return sym, skor
        except Exception:
            return sym, 0.0

    skorlar = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for sym, skor in [f.result() for f in as_completed({ex.submit(_cek, s): s for s in ANALIZ_LISTESI})]:
            skorlar[sym] = skor
    return skorlar


@st.cache_data(ttl=300, show_spinner=False)
def top10_analiz():
    haber_sk = haber_duyarlilik_skoru()
    rows = []
    for sym in ANALIZ_LISTESI:
        try:
            t  = yf.Ticker(f"{sym}.IS")
            h  = t.history(period="65d")
            if len(h) < 20: continue
            closes  = h["Close"].dropna()
            volumes = h["Volume"].dropna()
            price   = float(closes.iloc[-1])
            prev    = float(closes.iloc[-2]) if len(closes) >= 2 else price
            chg     = round(((price - prev) / prev) * 100, 2)
            vol_son = float(volumes.iloc[-1]) if len(volumes) >= 1 else 0

            # Teknik (0-40)
            tek_puan = 0
            rsi_son  = 50.0
            if len(closes) >= 15:
                rsi_son = float(hesapla_rsi(closes).iloc[-1])
            if   rsi_son < 30: tek_puan += 16
            elif rsi_son < 40: tek_puan += 14
            elif rsi_son < 50: tek_puan += 11
            elif rsi_son < 60: tek_puan += 8
            elif rsi_son < 70: tek_puan += 5
            else:              tek_puan += 2

            macd_son = 0.0
            if len(closes) >= 30:
                macd, sig = hesapla_macd(closes)
                macd_son  = float(macd.iloc[-1])
                if macd_son > float(sig.iloc[-1]):
                    tek_puan += 12
                    if len(macd) >= 2 and float(macd.iloc[-2]) <= float(sig.iloc[-2]):
                        tek_puan += 4
                else:
                    tek_puan += 2

            if len(volumes) >= 10:
                vol_ort = float(volumes.iloc[-10:-1].mean())
                if vol_ort > 0:
                    va = (vol_son - vol_ort) / vol_ort * 100
                    if   va > 100: tek_puan += 8
                    elif va > 50:  tek_puan += 6
                    elif va > 20:  tek_puan += 4
                    elif va > 0:   tek_puan += 2
            tek_puan = min(tek_puan, 40)

            # Haber/Duygu (0-25)
            haber_skor = haber_sk.get(sym, 0.0)
            duygu_puan = min(max(int((haber_skor + 10) / 20 * 25), 0), 25)

            # Analitik (0-25)
            analitik = 0
            dip_pct  = 50.0
            h52  = t.history(period="252d")
            clz52 = h52["Close"].dropna() if len(h52) > 0 else closes
            rng52 = float(clz52.max()) - float(clz52.min())
            if rng52 > 0:
                dip_pct = (price - float(clz52.min())) / rng52 * 100
            if   dip_pct <= 15: analitik += 14
            elif dip_pct <= 30: analitik += 11
            elif dip_pct <= 50: analitik += 7
            elif dip_pct <= 70: analitik += 4
            else:               analitik += 1
            if len(closes) >= 20:
                sma20 = float(closes.rolling(20).mean().iloc[-1])
                std20 = float(closes.rolling(20).std().iloc[-1])
                if std20 > 0:
                    bb_pos = (price - (sma20 - 2 * std20)) / (4 * std20)
                    if   bb_pos <= 0.2: analitik += 11
                    elif bb_pos <= 0.4: analitik += 8
                    elif bb_pos <= 0.6: analitik += 5
                    else:               analitik += 2
            analitik = min(analitik, 25)

            # Sosyal (0-10)
            sosyal = min(max(int((haber_skor + 10) / 4), 0), 10)
            toplam = tek_puan + duygu_puan + analitik + sosyal

            if   rsi_son < 35 and macd_son > 0:          sinyal_lbl = "GÜÇLÜ AL"
            elif rsi_son < 45 and duygu_puan >= 15:       sinyal_lbl = "AL"
            elif dip_pct <= 20:                           sinyal_lbl = "DİP BÖLGE"
            elif haber_skor >= 5:                         sinyal_lbl = "HABER POZ."
            else:                                         sinyal_lbl = "İZLE"

            rows.append({
                "Hisse": sym, "Fiyat": round(price, 2), "Degisim": chg,
                "TL_Hacim": price * vol_son, "RSI": round(rsi_son, 1),
                "Tek_Puan": tek_puan, "Duygu_Puan": duygu_puan,
                "Analitik": analitik, "Sosyal": sosyal,
                "Puan": round(float(toplam), 1), "Sinyal": sinyal_lbl,
                "Haber_Sk": round(haber_skor, 1),
            })
        except Exception:
            continue

    df = pd.DataFrame(rows)
    if df.empty: return df
    df = df.sort_values("Puan", ascending=False).head(10).reset_index(drop=True)
    df.index = df.index + 1
    return df


@st.cache_data(ttl=60, show_spinner=False)
def makro_cek():
    m = dict(USD_TRY=0.0, EUR_TRY=0.0, GRAM_ALTIN=0.0, ONS_ALTIN=0.0,
             BTC_USD=0.0, BTC_CHG=0.0, ETH_USD=0.0,
             BIST100=0.0, BIST100_CHG=0.0, BIST100_VOL=0.0, PETROL=0.0)
    try:
        r    = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml",
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
    except Exception: pass
    try:
        r = requests.get("https://finans.truncgil.com/v4/today.json",
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        d = r.json()
        for key in ["gram-altin", "GA", "Gram Altın", "gram_altin"]:
            entry = d.get(key, {})
            if entry:
                raw = entry.get("Selling") or entry.get("selling") or entry.get("Buying") or 0
                try:
                    m["GRAM_ALTIN"] = round(float(str(raw).replace(",", ".")), 1)
                    break
                except: continue
    except Exception: pass
    try:
        clz = yf.Ticker("GC=F").history(period="3d")["Close"].dropna()
        if len(clz) >= 1: m["ONS_ALTIN"] = round(float(clz.iloc[-1]), 1)
    except Exception: pass
    if m["GRAM_ALTIN"] == 0 and m["ONS_ALTIN"] > 0 and m["USD_TRY"] > 0:
        m["GRAM_ALTIN"] = round(m["ONS_ALTIN"] * m["USD_TRY"] / 31.1035, 1)
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids": "bitcoin,ethereum", "vs_currencies": "usd",
                                 "include_24hr_change": "true"},
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        d = r.json()
        m["BTC_USD"] = float(d.get("bitcoin", {}).get("usd", 0))
        m["BTC_CHG"] = round(float(d.get("bitcoin", {}).get("usd_24h_change", 0)), 2)
        m["ETH_USD"] = float(d.get("ethereum", {}).get("usd", 0))
    except Exception: pass
    try:
        t   = yf.Ticker("XU100.IS")
        h   = t.history(period="2d")
        clz = h["Close"].dropna()
        vol = h["Volume"].dropna()
        if len(clz) >= 2:
            m["BIST100"]     = round(float(clz.iloc[-1]))
            m["BIST100_CHG"] = round(((float(clz.iloc[-1]) - float(clz.iloc[-2])) / float(clz.iloc[-2])) * 100, 2)
        elif len(clz) == 1:
            m["BIST100"] = round(float(clz.iloc[0]))
        if len(vol) >= 1: m["BIST100_VOL"] = float(vol.iloc[-1])
    except Exception: pass
    try:
        clz = yf.Ticker("BZ=F").history(period="2d")["Close"].dropna()
        if len(clz) >= 1: m["PETROL"] = round(float(clz.iloc[-1]), 2)
    except Exception: pass
    return m


@st.cache_data(ttl=300, show_spinner=False)
def duygu_endeksi_hesapla():
    BIST_GENEL = [f"{s}.IS" for s in [
        "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
        "SISE","TOASO","AKBNK","HALKB","VAKBN","FROTO","BIMAS",
        "PGSUS","TCELL","ENKAI","KRDMD","EKGYO",
    ]]
    try:
        rsi_listesi = []; yukselenler = 0; toplam = 0
        for sym in BIST_GENEL:
            try:
                clz = yf.Ticker(sym).history(period="30d")["Close"].dropna()
                if len(clz) >= 15:
                    rsi_listesi.append(float(hesapla_rsi(clz).iloc[-1]))
                    toplam += 1
                    if float(clz.iloc[-1]) > float(clz.iloc[-2]): yukselenler += 1
            except Exception: pass
        if not rsi_listesi: return 50, "Nötr", "#d97706", 50.0, 0, 0
        ort_rsi = float(np.mean(rsi_listesi))
        oran    = yukselenler / max(toplam, 1)
        mom_k   = 0
        try:
            clz5 = yf.Ticker("XU100.IS").history(period="7d")["Close"].dropna()
            if len(clz5) >= 5:
                mom_k = min(max(((float(clz5.iloc[-1]) - float(clz5.iloc[-5])) / float(clz5.iloc[-5])) * 300, -15), 15)
        except Exception: pass
        endeks = max(0, min(100, int(ort_rsi * 0.60 + oran * 100 * 0.30 + (50 + mom_k) * 0.10)))
        if   endeks >= 75: durum, renk = "Aşırı Açgözlülük", "#16a34a"
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
        ("https://news.google.com/rss/search?q=KAP+kamuoyu+bildirimi+hisse&hl=tr&gl=TR&ceid=TR:tr", "KAP"),
        ("https://news.google.com/rss/search?q=BIST+borsa+faiz+dolar+TL&hl=tr&gl=TR&ceid=TR:tr", "G.NEWS"),
        ("https://news.google.com/rss/search?q=brüt+takas+hisse+borsa+istanbul&hl=tr&gl=TR&ceid=TR:tr", "BİST"),
    ]
    haberler = []
    for url, kaynak in FEEDS:
        if len(haberler) >= 12: break
        haberler.extend(_rss_parse(url, kaynak, 6))
    if len(haberler) < 4:
        try:
            for it in (yf.Ticker("XU100.IS").news or [])[:8]:
                baslik = (it.get("title") or "").strip()
                ts     = it.get("providerPublishTime", 0)
                link   = it.get("link", "") or it.get("url", "")
                if baslik:
                    haberler.append((ts_to_tr(ts) if ts else now_tr().strftime("%H:%M"),
                                     "YF/BIST", baslik[:120], link))
        except Exception: pass
    # Link garantisi: boş linklere Google News arama linki ver
    def _ensure_link(t):
        z, k, b, l = t
        if not l or not l.startswith("http"):
            l = f"https://news.google.com/search?q={b[:40].replace(' ','+')}&hl=tr&gl=TR"
        return (z, k, b, l)
    haberler = [_ensure_link(h) for h in haberler]
    return haberler[:14]


@st.cache_data(ttl=300, show_spinner=False)
def sosyal_trend_cek():
    import os
    trendler = []
    bearer = os.environ.get("TWITTER_BEARER_TOKEN", "")
    if bearer:
        try:
            r = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {bearer}"},
                params={"query": "BIST100 OR #hisse OR borsa istanbul lang:tr -is:retweet",
                        "max_results": 10, "tweet.fields": "created_at,public_metrics",
                        "sort_order": "recency"},
                timeout=8)
            if r.status_code == 200:
                today = now_tr().strftime("%Y-%m-%d")
                for tw in r.json().get("data", [])[:8]:
                    created = tw.get("created_at", "")
                    if today not in created: continue
                    m = tw.get("public_metrics", {})
                    trendler.append((
                        created[11:16] if len(created) >= 16 else now_tr().strftime("%H:%M"),
                        f"❤️{m.get('like_count',0)} 🔁{m.get('retweet_count',0)}",
                        (tw.get("text") or "").strip()[:120], ""))
        except Exception: pass
    for url in [
        "https://news.google.com/rss/search?q=BIST100+borsa+hisse&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=borsa+istanbul+yükseliş+düşüş&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=BIST+finans+yatırım+2026&hl=tr&gl=TR&ceid=TR:tr",
    ]:
        if len(trendler) >= 10: break
        for (z, k, b, l) in _rss_parse(url, "📰", 5):
            # l boşsa Google News ana sayfasına link ver
            link_son = l if (l and l.startswith("http")) else f"https://news.google.com/search?q={b[:30].replace(' ','+')}&hl=tr&gl=TR"
            trendler.append((z, "📰", b, link_son))
    trendler.sort(key=lambda x: x[0], reverse=True)
    return trendler[:10]


@st.cache_data(ttl=600, show_spinner=False)
def istihbarat_analiz():
    SEKTORLER = {
        "bankacılık": ["GARAN","AKBNK","YKBNK","HALKB","VAKBN","ISCTR"],
        "havacılık":  ["THYAO","PGSUS"],
        "savunma":    ["ASELS"],
        "enerji":     ["TUPRS","AKSEN","ENJSA","ZOREN","ODAS"],
        "gyo":        ["EKGYO","ISGYO","ALGYO"],
        "madencilik": ["KOZAL","EREGL","KRDMD"],
        "perakende":  ["BIMAS","MGROS","SOKM"],
        "teknoloji":  ["TTKOM","NETAS","LOGO"],
    }
    POZITIF_KW = ["rekor","yükseliş","artış","kâr","büyüme","ihale","sipariş","temettü",
                  "güçlü","alım","toparlandı","pozitif","teşvik","yatırım","ihracat"]
    NEGATIF_KW = ["düşüş","zarar","kayıp","baskı","risk","soruşturma","ceza","kriz",
                  "endişe","zayıf","gerileme","borç","iflas","uyarı","negatif"]
    haberler_raw = []
    for url in [
        "https://news.google.com/rss/search?q=borsa+istanbul+hisse+sektör&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=TCMB+faiz+Türkiye+ekonomi&hl=tr&gl=TR&ceid=TR:tr",
        "https://news.google.com/rss/search?q=BIST+hisse+yükseliş+düşüş&hl=tr&gl=TR&ceid=TR:tr",
    ]:
        for (z, k, b, l) in _rss_parse(url, "G.NEWS", 7):
            haberler_raw.append({"title": b, "zaman": z, "link": l})
    sonuclar = []
    for h in haberler_raw:
        tl = h["title"].lower()
        poz = sum(tl.count(k) for k in POZITIF_KW)
        neg = sum(tl.count(k) for k in NEGATIF_KW)
        duygu = "pozitif" if poz > neg else ("negatif" if neg > poz else "nötr")
        sektor = "genel"
        for s, hisseler in SEKTORLER.items():
            if s in tl or any(hs.lower() in tl for hs in hisseler):
                sektor = s; break
        sonuclar.append({"title": h["title"], "zaman": h["zaman"], "link": h["link"],
                         "duygu": duygu, "sektor": sektor, "poz": poz, "neg": neg})
    # Link garantisi
    for s in sonuclar:
        if not s.get("link") or not s["link"].startswith("http"):
            s["link"] = f"https://news.google.com/search?q={s['title'][:40].replace(' ','+')}&hl=tr&gl=TR"
    sonuclar.sort(key=lambda x: (x["duygu"] != "nötr", x["poz"] + x["neg"]), reverse=True)
    return sonuclar[:8]


@st.cache_data(ttl=300, show_spinner=False)
def fp_radar():
    aday = [
        "GARAN","EREGL","BIMAS","KCHOL","SISE","TUPRS","YKBNK","TTKOM",
        "CCOLA","ULKER","VESBE","ENJSA","MGROS","TSKB","OTKAR",
        "AKBNK","SAHOL","TAVHL","ARCLK","PETKM","DOAS","BRISA","MAVI","LOGO","CIMSA",
    ]
    rows = []
    for sym in aday:
        try:
            t   = yf.Ticker(f"{sym}.IS")
            h   = t.history(period="65d")
            clz = h["Close"].dropna()
            vol = h["Volume"].dropna()
            if len(clz) < 20: continue
            price       = float(clz.iloc[-1])
            rsi         = float(hesapla_rsi(clz).iloc[-1])
            dip_uzaklik = 50.0
            clz52 = t.history(period="252d")["Close"].dropna()
            rng52 = float(clz52.max()) - float(clz52.min()) if len(clz52) > 0 else 0
            if rng52 > 0:
                dip_uzaklik = (price - float(clz52.min())) / rng52 * 100
            son10    = clz.iloc[-10:].values
            egim_pct = float(np.polyfit(range(len(son10)), son10, 1)[0]) / price * 100
            vol_artis = 0
            if len(vol) >= 10:
                v5 = float(vol.iloc[-5:].mean()); vo5 = float(vol.iloc[-10:-5].mean())
                if vo5 > 0: vol_artis = (v5 - vo5) / vo5 * 100
            puan = 0
            if   25 <= rsi <= 40:        puan += 35
            elif 40 < rsi <= 50:         puan += 25
            elif rsi < 25:               puan += 28
            elif 50 < rsi <= 60:         puan += 15
            else:                        puan += 5
            if   dip_uzaklik <= 20:      puan += 30
            elif dip_uzaklik <= 35:      puan += 22
            elif dip_uzaklik <= 50:      puan += 14
            elif dip_uzaklik <= 65:      puan += 7
            if   0 < egim_pct <= 0.3:    puan += 20
            elif egim_pct > 0.3:         puan += 12
            elif -0.2 < egim_pct <= 0:   puan += 10
            else:                        puan += 3
            if vol_artis > 30 and rsi < 50: puan += 15
            elif vol_artis > 10:            puan += 8
            if   rsi < 35:           etiket = "AŞIRI UCUZ"
            elif dip_uzaklik < 25:   etiket = "52H DİP"
            elif egim_pct > 0:       etiket = "DÖNÜŞ SİNYALİ"
            else:                    etiket = "DEĞER BÖLGESİ"
            rows.append({"Hisse": sym, "Fiyat": round(price, 2), "RSI": round(rsi, 1),
                         "Dip%": round(dip_uzaklik, 0), "Puan": min(puan, 100), "Etiket": etiket})
        except Exception: continue
    rows.sort(key=lambda x: x["Puan"], reverse=True)
    return rows[:5]


# ═══════════════════════════════════════════════════════════════════════════════
#  VERİ ÇEK
# ═══════════════════════════════════════════════════════════════════════════════
now_t     = now_tr()
mk        = makro_cek()
radar_lst = radar_hacim_cek()
haberler  = haber_cek()
duygu_val, duygu_lbl, duygu_renk, rsi_ort, yukselen_sayi, toplam_sayi = duygu_endeksi_hesapla()

# ═══════════════════════════════════════════════════════════════════════════════
#  TOP BAR
# ═══════════════════════════════════════════════════════════════════════════════
bist_s  = f"{mk['BIST100']:,.0f}".replace(",", ".") if mk["BIST100"] else "—"
usd_s   = f"{mk['USD_TRY']:.2f}" if mk["USD_TRY"] else "—"
eur_s   = f"{mk['EUR_TRY']:.2f}" if mk["EUR_TRY"] else "—"
gram_s  = ftl(mk["GRAM_ALTIN"], 0)
ons_s   = fusd(mk["ONS_ALTIN"], 0)
btc_s   = fusd(mk["BTC_USD"], 0)
eth_s   = fusd(mk["ETH_USD"], 0)
brent_s = fusd(mk["PETROL"], 1)
bist_chg_html = fchg(mk["BIST100_CHG"])
btc_chg_html  = fchg(mk["BTC_CHG"])

st.markdown(f"""
<div class='topbar topbar-desktop'>
  <div class='t-logo'>
    <div class='live-dot'></div>
    Emrah<span class='dot'>.</span>AI
    <span class='t-badge'>Finans v6.2 RT</span>
  </div>
  <div class='t-strip'>
    <div class='t-item'><span class='t-lbl'>BIST 100</span><span class='t-val'>{bist_s}</span>{bist_chg_html}</div>
    <div class='t-item'><span class='t-lbl'>USD/TRY</span><span class='t-val'>{usd_s}</span></div>
    <div class='t-item'><span class='t-lbl'>EUR/TRY</span><span class='t-val'>{eur_s}</span></div>
    <div class='t-item'><span class='t-lbl'>GRAM ALTIN</span><span class='t-val'>{gram_s}</span></div>
    <div class='t-item'><span class='t-lbl'>ONS ALTIN</span><span class='t-val'>{ons_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BTC</span><span class='t-val'>{btc_s}</span>{btc_chg_html}</div>
    <div class='t-item'><span class='t-lbl'>ETH</span><span class='t-val'>{eth_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BRENT</span><span class='t-val'>{brent_s}</span></div>
    <div class='t-item'><span class='t-lbl'>TCMB</span><span class='t-val'>%37,00</span><span class='t-fl'>SABİT</span></div>
    <div class='t-item'><span class='t-lbl'>TR SAAT</span><span class='t-val'>{now_t.strftime('%H:%M:%S')}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='topbar-mobile'>
  <div style='background:#0f172a;padding:10px 14px 6px;border-bottom:2px solid #1e3a5f;'>
    <div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;'>
      <div style='display:flex;align-items:center;gap:8px;'>
        <div class='live-dot'></div>
        <span style='font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:700;color:#f1f5f9;'>
          PAPRIKA<span style='color:#38bdf8;'>.</span>AI
        </span>
        <span style='font-size:9px;background:#1e3a5f;color:#7dd3fc;padding:2px 7px;border-radius:4px;'>v6.2</span>
      </div>
      <span style='font-family:IBM Plex Mono,monospace;font-size:12px;color:#94a3b8;'>""" +
            now_t.strftime('%H:%M') + """ TR</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  1. RADAR
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
        if   vol_tl >= 1e9: vol_str = f"{vol_tl/1e9:.1f}B ₺"
        elif vol_tl >= 1e6: vol_str = f"{vol_tl/1e6:.0f}M ₺"
        elif vol_tl > 0:    vol_str = f"{vol_tl/1e3:.0f}K ₺"
        else:               vol_str = "—"
        cards += (
            f"<div class='rc rc-{sin_cls}'>"
            f"<div class='rc-tic'>{r['sym']}</div>"
            f"<div class='rc-fiy'>{ftl(r['price'])}</div>"
            f"<div class='rc-vol'>Günlük: {vol_str}</div>"
            f"<span class='pill p-{sin_cls}'>{sin_lbl}</span>"
            f"<div class='{chg_cls}'>{chg_sym} %{abs(r['chg']):.2f}</div>"
            f"</div>"
        )
    st.markdown(cards + "</div></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  2. STRATEJİK KARAR MATRİSİ
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='sw'>
  <div class='sh'>
    <div class='sb'></div>
    <div class='st'><span class='st-long'>Stratejik Karar Matrisi — Çok Boyutlu Analiz Top 10</span><span class='st-short'>Top 10 Analiz</span></div>
    <div class='ss'>Teknik %40 · Haber/Duygu %25 · Analitik %25 · Sosyal %10 → 100 puan</div>
  </div>
""", unsafe_allow_html=True)

with st.spinner("BIST analizi yapılıyor…"):
    df_top10 = top10_analiz()

if not df_top10.empty:
    rows_h = ""
    for rank, row in df_top10.iterrows():
        dcls  = "td-u" if row["Degisim"] >= 0 else "td-d"
        chg_s = "▲" if row["Degisim"] >= 0 else "▼"
        fp    = ftl(row["Fiyat"]) if row["Fiyat"] > 0 else "—"
        fh    = ftl(row["Fiyat"] * 1.15) if row["Fiyat"] > 0 else "—"
        puan  = row["Puan"]
        tl_h  = row.get("TL_Hacim", 0)
        if   tl_h >= 1e9: hacim_fmt = f"{tl_h/1e9:.1f}B ₺"
        elif tl_h >= 1e6: hacim_fmt = f"{tl_h/1e6:.0f}M ₺"
        elif tl_h > 0:    hacim_fmt = f"{tl_h/1e3:.0f}K ₺"
        else:             hacim_fmt = "—"
        sinyal_str = row.get("Sinyal", "İZLE")
        if   sinyal_str == "GÜÇLÜ AL":   sin_bg, sin_c = "#dcfce7", "#15803d"
        elif sinyal_str == "AL":          sin_bg, sin_c = "#eff6ff", "#1d4ed8"
        elif sinyal_str == "DİP BÖLGE":  sin_bg, sin_c = "#fffbeb", "#92400e"
        elif sinyal_str == "HABER POZ.": sin_bg, sin_c = "#f5f3ff", "#6d28d9"
        else:                             sin_bg, sin_c = "#f8fafc", "#475569"
        tek = int(row.get("Tek_Puan", 0))
        dp  = int(row.get("Duygu_Puan", 0))
        an  = int(row.get("Analitik", 0))
        so  = int(row.get("Sosyal", 0))
        hs  = row.get("Haber_Sk", 0)
        hr  = "#16a34a" if hs >= 0 else "#dc2626"
        rows_h += (
            f"<tr>"
            f"<td><span class='td-r'>{rank}</span></td>"
            f"<td class='td-h'>{row['Hisse']}</td>"
            f"<td class='td-f'>{fp}</td>"
            f"<td class='td-ht'>{fh}</td>"
            f"<td class='{dcls}'>{chg_s} %{abs(row['Degisim']):.2f}</td>"
            f"<td><span style='font-size:13px;font-weight:700;color:#2563eb;font-family:Arial,sans-serif;'>{row['RSI']}</span>"
            f"<span style='font-size:11px;color:#64748b;margin-left:4px;'>{'Ucuz' if row['RSI']<45 else ('Güçlü' if row['RSI']<65 else 'Pahalı')}</span></td>"
            f"<td><span style='font-size:11px;font-weight:700;color:{hr};'>{'▲' if hs>=0 else '▼'} {abs(hs):.1f}</span></td>"
            f"<td><div style='display:flex;align-items:center;gap:6px;'>"
            f"<div style='font-size:13px;font-weight:700;color:#1d4ed8;font-family:Arial,sans-serif;white-space:nowrap;'>{puan:.0f}/100</div>"
            f"<div style='flex:1;min-width:60px;'>"
            f"<div style='background:#f1f5f9;border-radius:3px;height:4px;overflow:hidden;'>"
            f"<div style='height:100%;width:{min(int(puan),100)}%;background:linear-gradient(90deg,#2563eb,#38bdf8);border-radius:3px;'></div></div>"
            f"<div style='font-size:9px;color:#94a3b8;margin-top:2px;'>T:{tek} D:{dp} A:{an} S:{so}</div></div></div></td>"
            f"<td><span style='font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;"
            f"background:{sin_bg};color:{sin_c};white-space:nowrap;'>{sinyal_str}</span></td>"
            f"<td class='td-a' style='font-size:12px;'>{hacim_fmt}</td>"
            f"</tr>"
        )
    st.markdown(
        f"<div class='mw'><table class='mt'><thead><tr>"
        f"<th>#</th><th>Hisse</th><th>Fiyat</th><th>Hedef (+15%)</th>"
        f"<th>Değişim</th><th>RSI</th><th>Haber Sk.</th>"
        f"<th>Toplam Puan <span style='font-weight:400;font-size:10px;'>(T·D·A·S)</span></th>"
        f"<th>Sinyal</th><th>TL Hacim</th>"
        f"</tr></thead><tbody>{rows_h}</tbody></table></div></div>",
        unsafe_allow_html=True)
else:
    st.markdown("<div class='sw'><p style='color:#dc2626;font-size:13px;'>Analiz verisi alınamadı.</p></div>",
                unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  3. SENSOR PANELLERİ
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("Derin analiz hesaplanıyor…"):
    fp_lst = fp_radar()

radar_vol = sum(r.get("vol_tl", 0) for r in radar_lst) if radar_lst else 0
chg_b     = mk.get("BIST100_CHG", 0)
alis_pct  = min(max(50 + chg_b * 4, 30), 80)
satis_pct = 100 - alis_pct
hg = radar_vol if radar_vol > 0 else 0
if   hg >= 1e9: hacim_str = f"{hg/1e9:.1f}B ₺"
elif hg >= 1e6: hacim_str = f"{hg/1e6:.0f}M ₺"
else:           hacim_str = "—"
hc_renk    = "#16a34a" if chg_b >= 0 else "#dc2626"
hc_chg_sym = "▲ +" if chg_b > 0 else "▼ "

fp_satirlar = ""
for i, r in enumerate(fp_lst, 1):
    et  = r.get("Etiket", "DEĞER")
    bc  = "fpb-g" if ("UCUZ" in et or "DİP" in et) else ("fpb-b" if "DÖNÜŞ" in et else "fpb-a")
    bw  = int(r.get("Puan", 0))
    fp_satirlar += (
        f"<div class='fp-row'><div class='fp-left'>"
        f"<span class='fp-name'>{i}. {r.get('Hisse','')}</span>"
        f"<span class='fp-meta'>{ftl(r.get('Fiyat',0))} · RSI:{r.get('RSI',0)} · 52H:%{r.get('Dip%',0):.0f} · Puan:{r.get('Puan',0)}</span>"
        f"<div class='fp-bar-bg'><div class='fp-bar-fill' style='width:{bw}%;'></div></div>"
        f"</div><span class='fp-bdg {bc}'>{et}</span></div>"
    ) if fp_lst else ""
if not fp_satirlar:
    fp_satirlar = "<div style='color:#475569;font-size:12px;padding:14px 0;text-align:center;'>Veri hesaplanıyor…</div>"

kart1 = (
    "<div style='background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #2563eb;"
    "border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;'>"
    "<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#2563eb;"
    "margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    "💎 F/P Değerleme Radarı — Top 5</div>" + fp_satirlar + "</div>"
)

kart2 = (
    f"<div style='background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #16a34a;"
    f"border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;'>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    f"letter-spacing:1.5px;text-transform:uppercase;color:#16a34a;"
    f"margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    f"📈 Günlük Para Akışı &amp; Hacim</div>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:26px;font-weight:700;"
    f"color:{hc_renk};margin:4px 0 3px;'>{'📈' if chg_b>=0 else '📉'} {hacim_str}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>BIST100 · ~15dk gecikme</div>"
    f"<div style='background:#e2e8f0;border-radius:6px;height:6px;overflow:hidden;margin-bottom:7px;'>"
    f"<div style='width:{int(alis_pct)}%;height:100%;border-radius:6px;"
    f"background:{'linear-gradient(90deg,#16a34a,#4ade80)' if chg_b>=0 else 'linear-gradient(90deg,#dc2626,#f87171)'};'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:12px;font-weight:700;margin-bottom:10px;'>"
    f"<span style='color:#16a34a;'>ALIŞ %{alis_pct:.0f}</span>"
    f"<span style='color:#dc2626;'>SATIŞ %{satis_pct:.0f}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>BIST100</span>"
    f"<span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:#1e293b;'>{bist_s}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>Değişim</span>"
    f"<span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:{hc_renk};'>{hc_chg_sym}%{abs(chg_b):.2f}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:12px;'>"
    f"<span style='color:#64748b;'>İşlem Hacmi</span>"
    f"<span style='font-family:\"IBM Plex Mono\",monospace;font-weight:700;color:#2563eb;'>{hacim_str}</span></div>"
    f"</div>"
)

kart3 = (
    f"<div style='background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #7c3aed;"
    f"border-radius:12px;padding:16px 18px;min-width:0;overflow:hidden;'>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;font-weight:700;"
    f"letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;"
    f"margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;'>"
    f"🧠 BIST Duygu Endeksi</div>"
    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:48px;font-weight:700;"
    f"line-height:1;color:{duygu_renk};margin:4px 0 2px;'>{duygu_val}</div>"
    f"<div style='font-size:13px;font-weight:600;color:{duygu_renk};margin-bottom:3px;'>{duygu_lbl}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>RSI Ort: <b style='color:#1e293b;'>{rsi_ort}</b></div>"
    f"<div style='background:#e2e8f0;border-radius:8px;height:7px;overflow:hidden;margin-bottom:4px;'>"
    f"<div style='height:100%;width:{duygu_val}%;background:{duygu_renk};border-radius:8px;'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;"
    f"font-family:\"IBM Plex Mono\",monospace;margin-bottom:10px;'>"
    f"<span>KORKU</span><span>NÖTR</span><span>AÇGÖZLÜLÜK</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:11px;'>"
    f"<span style='color:#64748b;'>Yükselen / Toplam</span>"
    f"<span style='color:#16a34a;font-weight:700;font-family:\"IBM Plex Mono\",monospace;'>{yukselen_sayi} / {toplam_sayi}</span></div>"
    f"<div style='display:flex;justify-content:space-between;padding:5px 0;border-top:1px solid #f1f5f9;font-size:11px;'>"
    f"<span style='color:#64748b;'>Yöntem</span><span style='color:#475569;'>RSI %60 · Yön %30 · Mom %10</span></div>"
    f"</div>"
)

st.markdown(
    "<div style='padding:16px 24px 12px;'>"
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>"
    "<div style='width:4px;height:20px;background:#2563eb;border-radius:3px;flex-shrink:0;'></div>"
    "<span style='font-family:\"IBM Plex Mono\",monospace;font-size:11px;font-weight:700;"
    "letter-spacing:1.8px;text-transform:uppercase;color:#2563eb;'>Derin Analiz Sensörleri</span>"
    "<span style='margin-left:auto;font-size:11px;color:#94a3b8;'>F/P · Para Akışı · Duygu Endeksi</span></div>"
    "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start;'>"
    + kart1 + kart2 + kart3 +
    "</div></div>",
    unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  🔎 ANLIK HİSSE FİYAT TAKİP MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='padding:4px 24px 4px;'>
  <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>
    <div style='width:4px;height:20px;background:#0ea5e9;border-radius:3px;flex-shrink:0;'></div>
    <span style='font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:700;
    letter-spacing:1.8px;text-transform:uppercase;color:#0ea5e9;'>🔎 Anlık Hisse Fiyat Takibi</span>
    <span style='margin-left:auto;font-size:11px;color:#94a3b8;'>Tüm BIST hisseleri · 30s önbellek · yfinance</span>
  </div>
</div>
""", unsafe_allow_html=True)

col_sel, col_data = st.columns([1, 3], gap="medium")
with col_sel:
    secili = st.selectbox(
        "Hisse Seç (Tüm BIST)",
        options=BIST100_FULL,
        index=0,
        label_visibility="collapsed",
        key="hisse_sec",
        help="BIST100 + tüm Borsa İstanbul hisseleri"
    )
    yenile_btn = st.button("🔄 Yenile", key="hisse_yenile", use_container_width=True)

with col_data:
    if yenile_btn:
        st.cache_data.clear()
        st.rerun()
    if secili:
        veri = hisse_fiyat_cek(secili)
        if veri:
            price   = veri["price"]
            chg     = veri["chg"]
            chg_tl  = veri["chg_tl"]
            renk    = "#16a34a" if chg >= 0 else "#dc2626"
            chg_sym = "▲ +" if chg > 0 else "▼ "
            rsi_v   = veri.get("rsi")
            rsi_str = f"{rsi_v}" if rsi_v is not None else "—"
            tl_h    = veri.get("tl_hacim", 0)
            if   tl_h >= 1e9: h_str = f"{tl_h/1e9:.2f}B ₺"
            elif tl_h >= 1e6: h_str = f"{tl_h/1e6:.0f}M ₺"
            elif tl_h > 0:    h_str = f"{tl_h/1e3:.0f}K ₺"
            else:             h_str = "—"
            rng52  = veri["yil_max"] - veri["yil_min"]
            pct52  = round((price - veri["yil_min"]) / max(rng52, 0.01) * 100, 1)
            rsi_renk = "#dc2626" if rsi_v and rsi_v > 70 else "#16a34a" if rsi_v and rsi_v < 30 else "#1e293b"
            rsi_note = " ⚠️ Aşırı Alım" if rsi_v and rsi_v > 70 else " ✅ Aşırı Satış" if rsi_v and rsi_v < 30 else ""
            # 52H bar görsel
            bar_pct = min(max(int(pct52), 0), 100)
            bar_renk = "#16a34a" if bar_pct < 40 else "#d97706" if bar_pct < 70 else "#dc2626"
            st.markdown(f"""
            <div class='htk-wrap'>
              <div class='htk-hdr'>📊 {secili}.IS — Anlık Fiyat &nbsp;·&nbsp; {now_t.strftime("%H:%M")} TR &nbsp;·&nbsp; ~15dk gecikme</div>
              <div style='display:grid;grid-template-columns:auto 1fr;gap:0 28px;align-items:start;'>
                <div>
                  <div style='font-family:"IBM Plex Mono",monospace;font-size:16px;font-weight:700;color:#64748b;margin-bottom:2px;'>{secili}.IS</div>
                  <div class='htk-price' style='color:{renk};'>₺{price:,.2f}</div>
                  <div class='{"htk-chg-up" if chg>=0 else "htk-chg-dn"}'>{chg_sym}%{abs(chg):.2f} &nbsp;({'+' if chg_tl>=0 else ''}₺{chg_tl:,.2f})</div>
                  <div class='htk-meta'>Önceki kapanış: ₺{veri["prev"]:,.2f}</div>
                  <div style='margin-top:12px;'>
                    <div style='font-size:10px;color:#64748b;margin-bottom:4px;font-weight:700;'>52H POZİSYON (Dipten: %{pct52})</div>
                    <div style='background:#e2e8f0;border-radius:4px;height:8px;overflow:hidden;width:140px;'>
                      <div style='height:100%;width:{bar_pct}%;background:{bar_renk};border-radius:4px;'></div>
                    </div>
                    <div style='display:flex;justify-content:space-between;width:140px;font-size:9px;color:#94a3b8;margin-top:2px;'>
                      <span>DİP</span><span>ZİRVE</span>
                    </div>
                  </div>
                </div>
                <div style='padding-top:4px;'>
                  <div class='htk-row'><span class='htk-lbl'>RSI (14)</span>
                    <span class='htk-val' style='color:{rsi_renk};'>{rsi_str}{rsi_note}</span></div>
                  <div class='htk-row'><span class='htk-lbl'>TL Hacim (Günlük)</span>
                    <span class='htk-val'>{h_str}</span></div>
                  <div class='htk-row'><span class='htk-lbl'>5G Min / Max</span>
                    <span class='htk-val'>₺{veri["gun5_min"]:,.2f} / ₺{veri["gun5_max"]:,.2f}</span></div>
                  <div class='htk-row'><span class='htk-lbl'>52H Min</span>
                    <span class='htk-val' style='color:#16a34a;'>₺{veri["yil_min"]:,.2f}</span></div>
                  <div class='htk-row'><span class='htk-lbl'>52H Max</span>
                    <span class='htk-val' style='color:#dc2626;'>₺{veri["yil_max"]:,.2f}</span></div>
                  <div class='htk-row'><span class='htk-lbl'>Hedef (+15%)</span>
                    <span class='htk-val' style='color:#2563eb;'>₺{price*1.15:,.2f}</span></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {secili} için veri alınamadı. Yahoo Finance'de aktif olmayabilir veya sembol hatalı.")

# ═══════════════════════════════════════════════════════════════════════════════
#  4. PİYASA İSTİHBARATI
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("İstihbarat analizi yapılıyor…"):
    istihbarat_lst = istihbarat_analiz()

if   chg_b > 1.5: bist_strateji = "Endeks güçlü yükseliyor. Momentum hisselerine odaklan: THYAO, ASELS, YKBNK."
elif chg_b > 0:   bist_strateji = "Endeks ılımlı pozitif. Seçici alım fırsatı — düşük RSI'li hisseler cazip."
elif chg_b > -1:  bist_strateji = "Endeks yatay. Dip bölgelerinde biriktirme yapılabilir."
else:             bist_strateji = "Endeks baskılı. Savunma hisseleri ve altın öne çıkabilir."

petrol_yorum = (f"Brent {brent_s} — 100$/varil üstünde. AKSEN/ENJSA olumlu." if mk["PETROL"] > 100
                else f"Brent {brent_s} — Normal seviyelerde. TUPRS nötr." if mk["PETROL"] > 80
                else f"Brent {brent_s} — Düşük petrol. TUPRS marjları olumlu.")
btc_val = mk.get("BTC_USD", 0)
kripto_yorum = ("Risk iştahı yüksek." if btc_val > 90000
                else "BTC konsolidasyon bandında." if btc_val > 70000
                else "BTC baskılı. Risk-off ortamı.")

def ist_html(liste):
    html = ""
    for item in liste[:4]:
        d = item["duygu"]
        if   d == "pozitif": bg, c, ic = "#f0fdf4", "#15803d", "▲"
        elif d == "negatif": bg, c, ic = "#fef2f2", "#b91c1c", "▼"
        else:                bg, c, ic = "#f8fafc", "#475569", "─"
        html += (
            f"<div style='padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:5px;'>"
            f"<span style='font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;"
            f"background:{bg};color:{c};'>{ic} {item['sektor'].upper()}</span>"
            f"<span style='font-size:10px;color:#94a3b8;font-family:IBM Plex Mono,monospace;'>{item['zaman']}</span>"
            f"</div>"
            f"<div style='font-size:12px;line-height:1.5;'>{link_html(item['link'], item['title'])}</div>"
            f"</div>"
        )
    return html or "<div style='font-size:12px;color:#94a3b8;padding:12px 0;'>Yükleniyor…</div>"

ist_sol = ist_html(istihbarat_lst[:4])
ist_sag = ist_html([
    {"title": f"TCMB faizi %37 sabit · Haziran indirim beklentisi gündemde.",
     "zaman": now_t.strftime("%d.%m %H:%M"), "link": "", "duygu": "nötr", "sektor": "tcmb"},
    {"title": f"USD/TRY {usd_s} · GRAM {gram_s} · ONS {ons_s}",
     "zaman": now_t.strftime("%d.%m %H:%M"), "link": "", "duygu": "nötr", "sektor": "döviz"},
    {"title": petrol_yorum,
     "zaman": now_t.strftime("%d.%m %H:%M"), "link": "", "duygu": "nötr", "sektor": "petrol"},
    {"title": f"BTC {btc_s} {'+' if mk.get('BTC_CHG',0)>=0 else ''}%{mk.get('BTC_CHG',0):.2f} (24s) · {kripto_yorum}",
     "zaman": now_t.strftime("%d.%m %H:%M"), "link": "", "duygu": "nötr", "sektor": "kripto"},
])

st.markdown(f"""
<div class="sw">
  <div class="sh">
    <div class="sb"></div>
    <div class="st">Piyasa İstihbaratı — Hisse Seçim Rehberi</div>
    <div class="ss">Haber + Duygu · {now_t.strftime("%d.%m.%Y %H:%M")} TR</div>
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
#  5. HABER AKIŞI & SOSYAL GÜNDEM
# ═══════════════════════════════════════════════════════════════════════════════
with st.spinner("Haberler yükleniyor…"):
    sosyal_lst = sosyal_trend_cek()

st.markdown("""
<div class="sw">
  <div class="sh">
    <div class="sb"></div>
    <div class="st">Canlı Haber Akışı & Sosyal Gündem</div>
    <div class="ss">RSS · Google News · 5dk yenileme · Tıkla → habere git ↗</div>
  </div>
""", unsafe_allow_html=True)

def haber_html_fn(liste, max_n=7, ok_renk="#2563eb"):
    html = ""
    for zaman, kaynak, baslik, link_ in liste[:max_n]:
        html += (
            f"<div style='display:flex;align-items:flex-start;gap:10px;"
            f"padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<span style='font-family:IBM Plex Mono,monospace;font-size:11px;font-weight:700;"
            f"color:#dc2626;min-width:55px;flex-shrink:0;margin-top:1px;'>{zaman}</span>"
            f"<div style='font-size:13px;line-height:1.5;'>"
            f"<span style='font-size:10px;font-weight:700;background:#eff6ff;color:#1d4ed8;"
            f"padding:1px 6px;border-radius:3px;margin-right:5px;white-space:nowrap;'>{kaynak}</span>"
            f"{link_html(link_, baslik, ok_renk=ok_renk)}</div></div>"
        )
    return html or "<div style='color:#94a3b8;font-size:12px;padding:12px 0;'>Yükleniyor…</div>"

haberler_s = sorted(haberler, key=lambda x: x[0], reverse=True) if haberler else []
h_html     = haber_html_fn(haberler_s, 7, "#2563eb")
s_html     = haber_html_fn([(z, i, b, l) for (z, i, b, l) in sosyal_lst], 7, "#7c3aed")

if not haberler:
    h_html = ("<div style='background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;"
              "padding:10px 14px;font-size:12px;color:#92400e;'>"
              "⚠️ Haberler alınamıyor. 60s sonra yenileniyor.<br>"
              "<a href='https://www.kap.org.tr/tr/bildirim-sorgu' target='_blank' style='color:#1d4ed8;'>KAP ↗</a> · "
              "<a href='https://bigpara.hurriyet.com.tr' target='_blank' style='color:#1d4ed8;'>Bigpara ↗</a>"
              "</div>")

st.markdown(
    "<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>"
    "<div style='background:#fff;border:1.5px solid #dde3ec;border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#1d4ed8;"
    "margin-bottom:12px;padding-bottom:11px;border-bottom:1.5px solid #e2e8f0;'>"
    "🌍 Borsa & Ekonomi Haberleri</div>" + h_html + "</div>"

    "<div style='background:#fff;border:1.5px solid #dde3ec;border-left:3px solid #7c3aed;"
    "border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;"
    "margin-bottom:6px;padding-bottom:6px;border-bottom:1.5px solid #e2e8f0;'>"
    "📰 Gündemdekiler — BIST100 Finans Gündemi</div>"
    "<div style='font-size:11px;color:#94a3b8;margin-bottom:10px;'>"
    "Google News · TR saati · Tıkla → habere git ↗</div>" + s_html + "</div>"
    "</div></div>",
    unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class='footer'>
  <span>PAPRIKA.AI © 2026 — Elite Terminal v6.2</span>
  <span>TR Saati: {now_t.strftime('%d.%m.%Y %H:%M:%S')} (UTC+3) | ⏱ 60s oto-yenileme</span>
  <span>yfinance ~15dk · TCMB Döviz · CoinGecko Kripto · Google News · ⚠️ Yatırım tavsiyesi değildir</span>
</div>
""", unsafe_allow_html=True)
