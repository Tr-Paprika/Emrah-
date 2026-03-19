"""
╔══════════════════════════════════════════════════════════════════╗
║          PAPRIKA ELİTE TERMİNAL  v6.2                           ║
║──────────────────────────────────────────────────────────────────║
║  pip install streamlit yfinance requests pandas numpy            ║
║  pip install streamlit-autorefresh                               ║
║  streamlit run paprika_terminal_v6.py                            ║
║                                                                  ║
║  v6.2 DEĞİŞİKLİKLER:                                           ║
║   • Tüm haber linkleri tıklanabilir — ↗ yeni sekme              ║
║   • Google News redirect linkleri çözüldü                        ║
║   • Boş linkler Google News araması ile dolduruldu               ║
║   • Saat UTC+3 TR yerel saatine düzeltildi                       ║
║   • Hisse Fiyat Takip Modülü — tüm BIST hisseleri               ║
║   • Analiz tüm BIST100 listesinden yapılıyor                     ║
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
from urllib.parse import urlparse, parse_qs, unquote, quote_plus
import re
import html as html_mod

# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Paprika Elite Terminal v6.2",
                   layout="wide", initial_sidebar_state="collapsed")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="pap62")
except ImportError:
    st.warning("⚠️ Otomatik yenileme kapalı — pip install streamlit-autorefresh")

# ══════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════
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

.topbar{background:#0f172a;padding:0 24px;height:54px;display:flex;
        align-items:center;justify-content:space-between;border-bottom:2px solid #1e3a5f}
.t-logo{font-family:'IBM Plex Mono',monospace;font-size:16px;font-weight:700;
        color:#f1f5f9;display:flex;align-items:center;gap:10px}
.t-dot{color:#38bdf8}
.t-badge{font-size:10px;font-weight:600;background:#1e3a5f;color:#7dd3fc;
         padding:3px 9px;border-radius:4px;letter-spacing:.4px}
.live-dot{width:8px;height:8px;background:#4ade80;border-radius:50%;
          box-shadow:0 0 0 2px rgba(74,222,128,.2);animation:pulse 2s ease infinite}
@keyframes pulse{50%{opacity:.3}}
.t-strip{display:flex;align-items:center;height:100%}
.t-item{display:flex;align-items:center;gap:6px;padding:0 13px;
        border-left:1px solid #1e3a5f;height:100%}
.t-lbl{font-size:10px;font-weight:700;color:#64748b;letter-spacing:.5px;
       text-transform:uppercase;white-space:nowrap}
.t-val{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;
       color:#e2e8f0;white-space:nowrap}
.t-up{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;
      color:#4ade80;white-space:nowrap}
.t-dn{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:600;
      color:#f87171;white-space:nowrap}
.t-fl{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#64748b;white-space:nowrap}

.sw{padding:14px 24px 10px}
.sh{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.sb{width:4px;height:20px;background:#2563eb;border-radius:3px;flex-shrink:0}
.stitle{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
        letter-spacing:1.8px;text-transform:uppercase;color:#2563eb}
.ssub{margin-left:auto;font-size:11px;color:#94a3b8;white-space:nowrap}

.rg{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}
.rc{background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;padding:14px 10px;
    text-align:center;position:relative;overflow:hidden;
    transition:box-shadow .2s,transform .15s}
.rc:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.1)}
.rc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.rc-B::before{background:#7c3aed}.rc-T::before{background:#dc2626}
.rc-D::before{background:#d97706}.rc-I::before{background:#94a3b8}
.rc-B{border-color:rgba(124,58,237,.2)}.rc-T{border-color:rgba(220,38,38,.2)}
.rc-D{border-color:rgba(217,119,6,.2)}
.rc-tic{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;
        color:#0f172a;margin-bottom:2px}
.rc-fiy{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;
        color:#1e40af;margin-bottom:4px}
.rc-vol{font-size:10px;color:#64748b;margin-bottom:7px}
.pill{display:inline-block;padding:3px 7px;border-radius:20px;
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
.mt th{padding:11px 14px;text-align:left;font-size:11px;font-weight:700;
       letter-spacing:.5px;color:#1d4ed8;text-transform:uppercase;border-bottom:2px solid #dde3ec}
.mt tbody tr{border-bottom:1px solid #f1f5f9;transition:background .12s}
.mt tbody tr:last-child{border-bottom:none}
.mt tbody tr:hover{background:#f5f8ff}
.mt td{padding:11px 14px;vertical-align:middle;font-size:13px}
.td-r{font-size:13px;font-weight:700;color:#1e40af;background:#eff6ff;
      border-radius:6px;padding:2px 8px;display:inline-block}
.td-u{font-weight:700;color:#16a34a}
.td-d{font-weight:700;color:#dc2626}

/* ═══ HABER LİNKİ — her durumda tıklanabilir ═══ */
a.hl{color:#1e293b !important;text-decoration:none !important;
     font-weight:600;border-bottom:1px dashed #94a3b8;
     cursor:pointer !important;pointer-events:all !important;
     transition:color .15s,border-color .15s}
a.hl:hover{color:#2563eb !important;border-bottom-color:#2563eb !important}
a.hl:visited{color:#374151 !important}
.lok{font-size:10px;margin-left:3px}

.htk{background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #0ea5e9;
     border-radius:12px;padding:18px 22px}
.htk-hdr{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
         letter-spacing:1.5px;text-transform:uppercase;color:#0ea5e9;
         margin-bottom:14px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.htk-price{font-family:'IBM Plex Mono',monospace;font-size:38px;font-weight:700;line-height:1.05}
.htk-cu{font-family:'IBM Plex Mono',monospace;font-size:17px;font-weight:700;color:#16a34a}
.htk-cd{font-family:'IBM Plex Mono',monospace;font-size:17px;font-weight:700;color:#dc2626}
.htk-meta{font-size:11px;color:#64748b;margin-top:3px}
.htk-row{display:flex;justify-content:space-between;padding:6px 0;
         border-bottom:1px solid #f1f5f9;font-size:12px}
.htk-row:last-child{border-bottom:none}
.htk-lbl{color:#64748b}
.htk-val{font-family:'IBM Plex Mono',monospace;font-weight:700;color:#1e293b;font-size:12px}

.kart{background:#fff;border:1.5px solid #dde3ec;border-radius:12px;
      padding:16px 18px;min-width:0;overflow:hidden}
.kart-hdr{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;
          letter-spacing:1.5px;text-transform:uppercase;
          margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0}
.fprow{display:flex;justify-content:space-between;align-items:center;
       padding:9px 0;border-bottom:1px solid #f1f5f9}
.fprow:last-child{border-bottom:none}
.fpname{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;color:#0f172a}
.fpmeta{font-size:11px;color:#64748b}
.fpbdg{font-size:9px;font-weight:700;padding:3px 9px;border-radius:20px;
       letter-spacing:.4px;text-transform:uppercase;flex-shrink:0;margin-left:8px}
.fpbdg-g{background:#f0fdf4;color:#15803d;border:1px solid #86efac}
.fpbdg-b{background:#eff6ff;color:#1d4ed8;border:1px solid #93c5fd}
.fpbdg-a{background:#fffbeb;color:#92400e;border:1px solid #fcd34d}
.krow{display:flex;justify-content:space-between;padding:5px 0;
      border-top:1px solid #f1f5f9;font-size:12px}
.klbl{color:#64748b}
.kval{font-family:'IBM Plex Mono',monospace;font-weight:700;color:#1e293b;font-size:12px}

.footer{background:#0f172a;border-top:1px solid #1e3a5f;padding:12px 24px;
        display:flex;justify-content:space-between;font-size:11px;color:#475569;
        font-family:'IBM Plex Mono',monospace;margin-top:8px}

.topbar-d{display:flex}
.topbar-m{display:none}
@media(max-width:768px){
  .sw{padding:10px 12px 8px!important}
  .topbar-d{display:none!important}
  .topbar-m{display:block!important}
  .rg{grid-template-columns:repeat(2,1fr)!important;gap:6px!important}
  .mw{overflow-x:auto!important}
  .mt{font-size:12px!important;min-width:560px}
  [style*="grid-template-columns:1fr 1fr 1fr"]{grid-template-columns:1fr!important}
  [style*="grid-template-columns:1fr 1fr"]{grid-template-columns:1fr!important}
  .footer{flex-direction:column;gap:4px;font-size:10px!important}
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  ZAMAN — UTC+3
# ══════════════════════════════════════════════════════════════════
TZ_TR = timezone(timedelta(hours=3))

def now_tr():
    return datetime.now(TZ_TR)

def rss_saat(raw):
    for fmt in (
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S +0000",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
    ):
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(TZ_TR).strftime("%H:%M")
        except Exception:
            pass
    return now_tr().strftime("%H:%M")

def ts_tr(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).astimezone(TZ_TR).strftime("%H:%M")
    except Exception:
        return now_tr().strftime("%H:%M")

# ══════════════════════════════════════════════════════════════════
#  BIST LİSTELERİ
# ══════════════════════════════════════════════════════════════════
BIST_FULL = sorted(set([
    "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
    "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
    "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
    "ARCLK","ISCTR","SOKM","TTKOM","SASA","AGHOL","ALGYO","CCOLA",
    "CIMSA","DOAS","EGEEN","MPARK","NETAS","ODAS","OYAKC","PARSN",
    "AKSEN","AEFES","AKGRT","ALFAS","BRISA","CANTE","CUSAN","DEVA",
    "EKOS","ENJSA","GESAN","GUBRF","IHLGM","IPEKE","ISGYO","IZMDC",
    "KARSN","KCAER","KLGYO","KONYA","MAVI","MGROS","NUHCM","OTKAR",
    "RYSAS","SARKY","SELVA","SMRTG","TSKB","TTRAK","ULKER","VESBE",
    "YATAS","ZOREN","TKFEN","TATGD","LOGO","AKSA","ALARK","PENTA",
    "KOZAA","KRDMA","KRDMB","DENGE","DESPC","DNISI","ERCB","ERDEM",
    "ESEN","ETILR","EUCFH","EUPWR","FENER","FONET","GEREL","GLYHO",
    "GOLTS","GOODY","GSDDE","GSDHO","GSRAY","HATEK","HEKTS","HUBVC",
    "HURGZ","ICBCT","IGGYO","IHLAS","INDES","INFO","INVEO","ISDMR",
    "ISFIN","ISGSY","ISKPL","ISYAT","JANTS","KAREL","KATMR","KBORU",
    "KENT","KERVT","KORDS","KRSTL","KRTEK","LIDER","LUKSK","MAALT",
    "MAGEN","MARTI","MATAS","MEDTR","MEGAP","MEPET","MERCN","MERIT",
    "MERKO","METRO","MIPAZ","MOBTL","MODEL","MOGEN","MRSHL","MSGYO",
    "MTRKS","MZHLD","NIBAS","NILYT","NTHOL","NTTUR","OBASE","ODEYO",
    "ONCSM","ORGE","ORMA","OSMEN","OSTIM","OVER","OYLUM","OZGYO",
    "PAGYO","PAMEL","PCILT","PEHOL","PENGD","PINSU","PKART","PKENT",
    "PLTUR","PNLSN","POLHO","POLTK","PRDGS","PRTAS","PSDTC","PRZMA",
    "RALYH","RAYSG","RBTAS","RHEAG","RNPOL","ROYAL","RTALB","SAFKR",
    "SANEL","SANFM","SANKO","SAYAS","SEGMN","SEKUR","SELGD","SEYKM",
    "SILVR","SNGYO","SNPAM","SONME","SRVGY","SUMAS","SUWEN","TABGD",
    "TARKM","TDGYO","TEKTU","TEZOL","TGSAS","TIRE","TKNSA","TLMAN",
    "TMPOL","TRCAS","TRGYO","TRILC","TSPOR","TUCLK","TUKAS","TUREX",
    "TURGG","TURSG","ULAS","ULUUN","ULUSE","UMPAS","UNLU","USAK",
    "VAKFN","VAKKO","VANGD","VBTYZ","VKGYO","VKING","VRGYO","YAPRK",
    "YAYLA","YBTAS","YESIL","YEOTK","YGGYO","YKSLN","YUNSA","ZEDUR","ZRGYO",
]))

ANALIZ = sorted(set([
    "GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
    "SISE","TOASO","FROTO","KOZAL","BIMAS","AKBNK","HALKB","VAKBN",
    "PGSUS","TCELL","DOHOL","EKGYO","ENKAI","KRDMD","PETKM","TAVHL",
    "ARCLK","ISCTR","SOKM","TTKOM","SASA","CCOLA","DOAS","AKSEN",
    "AEFES","BRISA","ENJSA","MGROS","OTKAR","ULKER","VESBE","TSKB",
    "TTRAK","MAVI","CIMSA","LOGO","EGEEN","NUHCM","GUBRF","KLGYO",
    "ALGYO","ISGYO","EKOS","GESAN","KARSN","CUSAN","SARKY","IZMDC",
    "DEVA","AGHOL","PARSN","TKFEN","TATGD","PENTA","KOZAA","KRDMA",
    "KRDMB","AKGRT","CANTE","ALFAS","IPEKE","KCAER","KONYA","OYAKC",
    "RYSAS","SELVA","SMRTG","YATAS","ZOREN","NETAS","ODAS","MPARK",
]))

# ══════════════════════════════════════════════════════════════════
#  FORMAT
# ══════════════════════════════════════════════════════════════════
def ftl(v, d=2):
    if not v or v == 0: return "—"
    return f"₺{v:,.{d}f}".replace(",","X").replace(".",",").replace("X",".")

def fusd(v, d=0):
    if not v or v == 0: return "—"
    return f"${v:,.{d}f}"

def fchg(v):
    if v is None: return "<span class='t-fl'>—</span>"
    try: v = float(v)
    except: return "<span class='t-fl'>—</span>"
    if v > 0: return f"<span class='t-up'>▲ +%{v:.2f}</span>"
    if v < 0: return f"<span class='t-dn'>▼ %{v:.2f}</span>"
    return "<span class='t-fl'>─</span>"

def sinyal(chg):
    if chg > 7:  return "TAVAN ADAYI","T"
    if chg < -2: return "DİP AVCI","D"
    if chg > 2:  return "BALİNA GİRİŞİ","B"
    return "İZLEME","I"

def hfmt(v):
    if v >= 1e9: return f"{v/1e9:.1f}B ₺"
    if v >= 1e6: return f"{v/1e6:.0f}M ₺"
    if v > 0:    return f"{v/1e3:.0f}K ₺"
    return "—"

# ══════════════════════════════════════════════════════════════════
#  LINK FONKSİYONU — merkezi, her zaman tıklanabilir
# ══════════════════════════════════════════════════════════════════
def safe_link(url, metin, renk="#2563eb"):
    """
    Tıklanabilir haber linki.
    - Google News redirect çözülür
    - Boşsa başlığa göre Google News araması açılır
    - target=_blank + pointer-events:all
    """
    txt = (metin or "").replace("<","&lt;").replace(">","&gt;")
    lnk = (url or "").strip()

    # Google redirect çöz
    if lnk and "news.google.com" in lnk:
        try:
            qs = parse_qs(urlparse(lnk).query)
            if "url" in qs:
                lnk = unquote(qs["url"][0])
        except Exception:
            pass

    # Hâlâ geçersizse → Google News arama
    if not lnk or not lnk.startswith("http"):
        q = quote_plus((metin or "")[:60])
        lnk = f"https://news.google.com/search?q={q}&hl=tr&gl=TR&ceid=TR:tr"

    return (
        f"<a href='{lnk}' target='_blank' rel='noopener noreferrer' "
        f"class='hl' style='pointer-events:all !important;'>"
        f"{txt}<span class='lok' style='color:{renk};'>↗</span></a>"
    )

# ══════════════════════════════════════════════════════════════════
#  RSS YARDIMCISI
# ══════════════════════════════════════════════════════════════════
_HDR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml,text/xml;q=0.9,*/*;q=0.8"}

def rss_parse(url, kaynak="", n=8):
    """Döner: list of (saat, kaynak, baslik, link)  — link her zaman http"""
    out = []
    try:
        r = requests.get(url, headers=_HDR, timeout=10)
        r.raise_for_status()
        txt = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', '', r.text)
        txt = re.sub(r'<\?xml[^>]+\?>', '', txt)
        root = ET.fromstring(txt.encode("utf-8","replace"))
        items = root.findall(".//item") or root.findall(".//entry")
        for item in items[:n]:
            # Başlık
            te = item.find("title")
            if te is None: continue
            raw = re.sub(r'<!\[CDATA\[(.*?)\]\]>',r'\1',te.text or "",flags=re.DOTALL)
            baslik = html_mod.unescape(raw).strip()
            baslik = re.sub(r'\s*[-|]\s*[^-|]+$','',baslik).strip()
            if len(baslik) < 8: continue

            # Saat
            saat = now_tr().strftime("%H:%M")
            for tag in ("pubDate","published","updated"):
                el = item.find(tag)
                if el is not None and el.text:
                    saat = rss_saat(el.text); break

            # Link — 4 farklı kaynaktan dene
            lnk = ""
            le = item.find("link")
            if le is not None:
                lnk = (le.text or le.get("href","")).strip()
            if not lnk or not lnk.startswith("http"):
                ge = item.find("guid")
                if ge is not None and ge.text and ge.text.startswith("http"):
                    lnk = ge.text.strip()
            if not lnk or not lnk.startswith("http"):
                de = item.find("description")
                if de is not None and de.text:
                    m = re.search(r'href=["\']([^"\']+)["\']', de.text)
                    if m: lnk = html_mod.unescape(m.group(1))
            # Google redirect çöz
            if lnk and "news.google.com" in lnk:
                try:
                    qs = parse_qs(urlparse(lnk).query)
                    if "url" in qs: lnk = unquote(qs["url"][0])
                except Exception: pass
            # Fallback
            if not lnk or not lnk.startswith("http"):
                lnk = f"https://news.google.com/search?q={quote_plus(baslik[:60])}&hl=tr&gl=TR&ceid=TR:tr"

            out.append((saat, kaynak, baslik[:120], lnk))
    except Exception:
        pass
    return out

# ══════════════════════════════════════════════════════════════════
#  TEKNİK HESAPLAMALAR
# ══════════════════════════════════════════════════════════════════
def calc_rsi(c, p=14):
    d = c.diff()
    g = d.clip(lower=0).rolling(p).mean()
    l = (-d.clip(upper=0)).rolling(p).mean()
    return 100 - (100 / (1 + g / l.replace(0,np.nan)))

def calc_macd(c, fast=12, slow=26, sig=9):
    m = c.ewm(span=fast,adjust=False).mean() - c.ewm(span=slow,adjust=False).mean()
    return m, m.ewm(span=sig,adjust=False).mean()

# ══════════════════════════════════════════════════════════════════
#  VERİ FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def makro_cek():
    m = dict(USD=0.,EUR=0.,GRAM=0.,ONS=0.,
             BTC=0.,BTC_CHG=0.,ETH=0.,
             BIST=0.,BIST_CHG=0.,BIST_VOL=0.,PETROL=0.)
    try:
        r = requests.get("https://www.tcmb.gov.tr/kurlar/today.xml",
                         timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        root = ET.fromstring(r.content)
        for cur in root.findall("Currency"):
            kod = cur.get("CurrencyCode","")
            def vv(tag,c=cur):
                el=c.find(tag)
                try: return float(el.text.replace(",",".")) if el is not None and el.text else 0.
                except: return 0.
            if   kod=="USD": m["USD"]=vv("ForexSelling") or vv("ForexBuying")
            elif kod=="EUR": m["EUR"]=vv("ForexSelling") or vv("ForexBuying")
    except: pass
    try:
        d = requests.get("https://finans.truncgil.com/v4/today.json",
                         timeout=8,headers={"User-Agent":"Mozilla/5.0"}).json()
        for k in ("gram-altin","GA","Gram Altın","gram_altin"):
            e=d.get(k,{})
            if e:
                raw=e.get("Selling") or e.get("selling") or e.get("Buying") or 0
                try: m["GRAM"]=round(float(str(raw).replace(",",".")),1); break
                except: pass
    except: pass
    try:
        gc=yf.Ticker("GC=F").history(period="3d")["Close"].dropna()
        if len(gc): m["ONS"]=round(float(gc.iloc[-1]),1)
    except: pass
    if m["GRAM"]==0 and m["ONS"]>0 and m["USD"]>0:
        m["GRAM"]=round(m["ONS"]*m["USD"]/31.1035,1)
    try:
        d=requests.get("https://api.coingecko.com/api/v3/simple/price",
            params={"ids":"bitcoin,ethereum","vs_currencies":"usd","include_24hr_change":"true"},
            timeout=8,headers={"User-Agent":"Mozilla/5.0"}).json()
        m["BTC"]=float(d.get("bitcoin",{}).get("usd",0))
        m["BTC_CHG"]=round(float(d.get("bitcoin",{}).get("usd_24h_change",0)),2)
        m["ETH"]=float(d.get("ethereum",{}).get("usd",0))
    except: pass
    try:
        h=yf.Ticker("XU100.IS").history(period="2d")
        c=h["Close"].dropna()
        if len(c)>=2:
            m["BIST"]=round(float(c.iloc[-1]))
            m["BIST_CHG"]=round(((float(c.iloc[-1])-float(c.iloc[-2]))/float(c.iloc[-2]))*100,2)
        elif len(c)==1: m["BIST"]=round(float(c.iloc[0]))
        v=h["Volume"].dropna()
        if len(v): m["BIST_VOL"]=float(v.iloc[-1])
    except: pass
    try:
        b=yf.Ticker("BZ=F").history(period="2d")["Close"].dropna()
        if len(b): m["PETROL"]=round(float(b.iloc[-1]),2)
    except: pass
    return m


@st.cache_data(ttl=60, show_spinner=False)
def radar_cek():
    SYM=["GARAN","THYAO","ASELS","EREGL","TUPRS","KCHOL","YKBNK","SAHOL",
         "SISE","TOASO","FROTO","AKBNK","HALKB","VAKBN","PGSUS","TCELL",
         "ENKAI","KRDMD","PETKM","BIMAS","ARCLK","ISCTR","TTKOM","EKGYO",
         "CCOLA","MAVI","TAVHL","BRISA","DOAS","TSKB","MGROS","OTKAR"]
    out=[]
    for s in SYM:
        try:
            h=yf.Ticker(f"{s}.IS").history(period="5d")
            c=h["Close"].dropna(); v=h["Volume"].dropna()
            if len(c)<1 or len(v)<1: continue
            price=float(c.iloc[-1]); vol=float(v.iloc[-1])
            prev=float(c.iloc[-2]) if len(c)>=2 else price
            chg=round(((price-prev)/prev)*100,2) if prev>0 else 0
            tl=price*vol
            if price>0 and tl>0:
                out.append({"sym":s,"price":round(price,2),"chg":chg,"vol_tl":tl})
        except: pass
    out.sort(key=lambda x:x["vol_tl"],reverse=True)
    return out[:8]


@st.cache_data(ttl=30, show_spinner=False)
def hisse_cek(sym):
    try:
        t=yf.Ticker(f"{sym}.IS")
        h5=t.history(period="5d")
        c=h5["Close"].dropna(); v=h5["Volume"].dropna()
        if len(c)<1: return None
        price=float(c.iloc[-1])
        prev=float(c.iloc[-2]) if len(c)>=2 else price
        chg=round(((price-prev)/prev)*100,2) if prev>0 else 0
        h52=t.history(period="252d")["Close"].dropna()
        rsi14=None
        if len(c)>=15: rsi14=round(float(calc_rsi(c).iloc[-1]),1)
        vol=float(v.iloc[-1]) if len(v)>=1 else 0
        return {"price":price,"prev":prev,"chg":chg,"chg_tl":round(price-prev,2),
                "vol":vol,"tl_hacim":price*vol,
                "min5":float(c.min()),"max5":float(c.max()),
                "min52":float(h52.min()) if len(h52)>0 else price,
                "max52":float(h52.max()) if len(h52)>0 else price,
                "rsi":rsi14}
    except: return None


@st.cache_data(ttl=600, show_spinner=False)
def haber_sk():
    POZ=["yükseliş","artış","rekor","güçlü","alım","ihale","kâr","büyüme",
         "yatırım","sipariş","temettü","pozitif","rally","toparlandı","yukarı"]
    NEG=["düşüş","zarar","satış","baskı","risk","endişe","uyarı","negatif",
         "zayıf","kaybetti","geriledi","soruşturma","ceza","borç","kriz"]
    def _f(sym):
        try:
            r=requests.get(
                f"https://news.google.com/rss/search?q={sym}+hisse+borsa&hl=tr&gl=TR&ceid=TR:tr",
                headers={"User-Agent":"Mozilla/5.0"},timeout=6)
            t=r.text.lower()
            p=sum(t.count(k) for k in POZ); n=sum(t.count(k) for k in NEG)
            return sym,round(min(max((p-n)/(p+n+1)*20+t.count("<item>")*0.5,-10),10),1)
        except: return sym,0.
    sk={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for sym,s in [f.result() for f in as_completed({ex.submit(_f,s):s for s in ANALIZ})]:
            sk[sym]=s
    return sk


@st.cache_data(ttl=300, show_spinner=False)
def top10():
    hs=haber_sk()
    rows=[]
    for sym in ANALIZ:
        try:
            t=yf.Ticker(f"{sym}.IS"); h=t.history(period="65d")
            if len(h)<20: continue
            c=h["Close"].dropna(); vol=h["Volume"].dropna()
            price=float(c.iloc[-1]); prev=float(c.iloc[-2]) if len(c)>=2 else price
            chg=round(((price-prev)/prev)*100,2)
            vsn=float(vol.iloc[-1]) if len(vol)>=1 else 0

            tp=0; rs=50.
            if len(c)>=15: rs=float(calc_rsi(c).iloc[-1])
            if   rs<30: tp+=16
            elif rs<40: tp+=14
            elif rs<50: tp+=11
            elif rs<60: tp+=8
            elif rs<70: tp+=5
            else:       tp+=2
            ms=0.
            if len(c)>=30:
                mv,sv=calc_macd(c); ms=float(mv.iloc[-1])
                if ms>float(sv.iloc[-1]):
                    tp+=12
                    if len(mv)>=2 and float(mv.iloc[-2])<=float(sv.iloc[-2]): tp+=4
                else: tp+=2
            if len(vol)>=10:
                vo=float(vol.iloc[-10:-1].mean())
                if vo>0:
                    va=(vsn-vo)/vo*100
                    if   va>100: tp+=8
                    elif va>50:  tp+=6
                    elif va>20:  tp+=4
                    elif va>0:   tp+=2
            tp=min(tp,40)

            hsk=hs.get(sym,0.)
            dp=min(max(int((hsk+10)/20*25),0),25)

            ap=0; dip=50.
            h52=t.history(period="252d"); c52=h52["Close"].dropna() if len(h52)>0 else c
            rng=float(c52.max())-float(c52.min())
            if rng>0: dip=(price-float(c52.min()))/rng*100
            if   dip<=15: ap+=14
            elif dip<=30: ap+=11
            elif dip<=50: ap+=7
            elif dip<=70: ap+=4
            else:         ap+=1
            if len(c)>=20:
                s20=float(c.rolling(20).mean().iloc[-1])
                std=float(c.rolling(20).std().iloc[-1])
                if std>0:
                    bp=(price-(s20-2*std))/(4*std)
                    if   bp<=0.2: ap+=11
                    elif bp<=0.4: ap+=8
                    elif bp<=0.6: ap+=5
                    else:         ap+=2
            ap=min(ap,25)
            sp=min(max(int((hsk+10)/4),0),10)
            total=tp+dp+ap+sp

            if   rs<35 and ms>0:   sn="GÜÇLÜ AL"
            elif rs<45 and dp>=15: sn="AL"
            elif dip<=20:          sn="DİP BÖLGE"
            elif hsk>=5:           sn="HABER POZ."
            else:                  sn="İZLE"

            rows.append({"Hisse":sym,"Fiyat":round(price,2),"Deg":chg,
                         "TLH":price*vsn,"RSI":round(rs,1),
                         "TP":tp,"DP":dp,"AP":ap,"SP":sp,
                         "Puan":round(float(total),1),"Sinyal":sn,"HSk":round(hsk,1)})
        except: continue
    df=pd.DataFrame(rows)
    if df.empty: return df
    df=df.sort_values("Puan",ascending=False).head(10).reset_index(drop=True)
    df.index=df.index+1
    return df


@st.cache_data(ttl=300, show_spinner=False)
def duygu():
    B20=["GARAN.IS","THYAO.IS","ASELS.IS","EREGL.IS","TUPRS.IS",
         "KCHOL.IS","YKBNK.IS","SAHOL.IS","SISE.IS","TOASO.IS",
         "AKBNK.IS","HALKB.IS","VAKBN.IS","FROTO.IS","BIMAS.IS",
         "PGSUS.IS","TCELL.IS","ENKAI.IS","KRDMD.IS","EKGYO.IS"]
    try:
        rl=[]; yk=0; tp=0
        for sym in B20:
            try:
                h=yf.Ticker(sym).history(period="30d")["Close"].dropna()
                if len(h)>=15:
                    rl.append(float(calc_rsi(h).iloc[-1])); tp+=1
                    if float(h.iloc[-1])>float(h.iloc[-2]): yk+=1
            except: pass
        if not rl: return 50,"Nötr","#d97706",50.,0,0
        ort=float(np.mean(rl)); oran=yk/max(tp,1); mk=0
        try:
            c5=yf.Ticker("XU100.IS").history(period="7d")["Close"].dropna()
            if len(c5)>=5: mk=min(max(((float(c5.iloc[-1])-float(c5.iloc[-5]))/float(c5.iloc[-5]))*300,-15),15)
        except: pass
        e=max(0,min(100,int(ort*0.60+oran*100*0.30+(50+mk)*0.10)))
        if   e>=75: d,r="Aşırı Açgözlülük","#16a34a"
        elif e>=60: d,r="Açgözlülük","#22c55e"
        elif e>=45: d,r="Nötr / Pozitif","#d97706"
        elif e>=30: d,r="Korku","#dc2626"
        else:       d,r="Aşırı Korku","#991b1b"
        return e,d,r,round(ort,1),yk,tp
    except: return 50,"Nötr","#d97706",50.,0,0


@st.cache_data(ttl=300, show_spinner=False)
def haberler_cek():
    FEEDS=[
        ("https://news.google.com/rss/search?q=borsa+istanbul+hisse+BIST&hl=tr&gl=TR&ceid=TR:tr","G.NEWS"),
        ("https://news.google.com/rss/search?q=KAP+kamuoyu+bildirimi+hisse&hl=tr&gl=TR&ceid=TR:tr","KAP"),
        ("https://news.google.com/rss/search?q=BIST+borsa+faiz+dolar+TL&hl=tr&gl=TR&ceid=TR:tr","G.NEWS"),
        ("https://news.google.com/rss/search?q=hisse+borsa+istanbul+finans&hl=tr&gl=TR&ceid=TR:tr","BİST"),
    ]
    lst=[]
    for url,k in FEEDS:
        if len(lst)>=14: break
        lst.extend(rss_parse(url,k,6))
    if len(lst)<4:
        try:
            for it in (yf.Ticker("XU100.IS").news or [])[:8]:
                b=(it.get("title") or "").strip()
                ts=it.get("providerPublishTime",0)
                lk=it.get("link","") or it.get("url","")
                if not lk or not lk.startswith("http"):
                    lk=f"https://news.google.com/search?q={quote_plus(b[:60])}&hl=tr&gl=TR&ceid=TR:tr"
                if b: lst.append((ts_tr(ts) if ts else now_tr().strftime("%H:%M"),"YF/BIST",b[:120],lk))
        except: pass
    return lst[:14]


@st.cache_data(ttl=300, show_spinner=False)
def sosyal_cek():
    import os
    tr=[]
    bearer=os.environ.get("TWITTER_BEARER_TOKEN","")
    if bearer:
        try:
            r=requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization":f"Bearer {bearer}"},
                params={"query":"BIST100 OR #hisse OR borsa istanbul lang:tr -is:retweet",
                        "max_results":10,"tweet.fields":"created_at,public_metrics","sort_order":"recency"},
                timeout=8)
            if r.status_code==200:
                today=now_tr().strftime("%Y-%m-%d")
                for tw in r.json().get("data",[])[:8]:
                    cr=tw.get("created_at","")
                    if today not in cr: continue
                    m2=tw.get("public_metrics",{})
                    txt=(tw.get("text") or "").strip()[:120]
                    lk=f"https://news.google.com/search?q={quote_plus(txt[:60])}&hl=tr&gl=TR&ceid=TR:tr"
                    tr.append((cr[11:16] if len(cr)>=16 else now_tr().strftime("%H:%M"),
                               f"❤️{m2.get('like_count',0)} 🔁{m2.get('retweet_count',0)}",txt,lk))
        except: pass
    FEEDS2=["https://news.google.com/rss/search?q=BIST100+borsa+hisse&hl=tr&gl=TR&ceid=TR:tr",
            "https://news.google.com/rss/search?q=borsa+istanbul+yükseliş+düşüş&hl=tr&gl=TR&ceid=TR:tr",
            "https://news.google.com/rss/search?q=BIST+finans+yatırım+2026&hl=tr&gl=TR&ceid=TR:tr"]
    for url in FEEDS2:
        if len(tr)>=10: break
        for z,k,b,l in rss_parse(url,"📰",5):
            tr.append((z,"📰",b,l))
    tr.sort(key=lambda x:x[0],reverse=True)
    return tr[:10]


@st.cache_data(ttl=600, show_spinner=False)
def istihbarat():
    SEKT={"bankacılık":["GARAN","AKBNK","YKBNK","HALKB","VAKBN","ISCTR"],
           "havacılık":["THYAO","PGSUS"],"savunma":["ASELS"],
           "enerji":["TUPRS","AKSEN","ENJSA","ZOREN"],"gyo":["EKGYO","ISGYO","ALGYO"],
           "madencilik":["KOZAL","EREGL","KRDMD"],"perakende":["BIMAS","MGROS","SOKM"],
           "teknoloji":["TTKOM","NETAS","LOGO"]}
    POZ=["rekor","yükseliş","artış","kâr","büyüme","ihale","sipariş","temettü",
         "güçlü","alım","toparlandı","pozitif","teşvik","yatırım","ihracat"]
    NEG=["düşüş","zarar","kayıp","baskı","risk","soruşturma","ceza","kriz",
         "endişe","zayıf","gerileme","borç","iflas","uyarı","negatif"]
    haml=[]
    for url in ["https://news.google.com/rss/search?q=borsa+istanbul+hisse+sektör&hl=tr&gl=TR&ceid=TR:tr",
                "https://news.google.com/rss/search?q=TCMB+faiz+Türkiye+ekonomi&hl=tr&gl=TR&ceid=TR:tr",
                "https://news.google.com/rss/search?q=BIST+hisse+yükseliş+düşüş&hl=tr&gl=TR&ceid=TR:tr"]:
        for z,k,b,l in rss_parse(url,"G.NEWS",7):
            haml.append({"title":b,"zaman":z,"link":l})
    sonuc=[]
    for h in haml:
        tl=h["title"].lower()
        p=sum(tl.count(k) for k in POZ); n=sum(tl.count(k) for k in NEG)
        d="pozitif" if p>n else ("negatif" if n>p else "nötr")
        s="genel"
        for sk,hs in SEKT.items():
            if sk in tl or any(x.lower() in tl for x in hs): s=sk; break
        sonuc.append({"title":h["title"],"zaman":h["zaman"],"link":h["link"],
                      "duygu":d,"sektor":s,"poz":p,"neg":n})
    sonuc.sort(key=lambda x:(x["duygu"]!="nötr",x["poz"]+x["neg"]),reverse=True)
    return sonuc[:8]


@st.cache_data(ttl=300, show_spinner=False)
def fp_radar():
    ADY=["GARAN","EREGL","BIMAS","KCHOL","SISE","TUPRS","YKBNK","TTKOM",
         "CCOLA","ULKER","VESBE","ENJSA","MGROS","TSKB","OTKAR",
         "AKBNK","SAHOL","TAVHL","ARCLK","PETKM","DOAS","BRISA","MAVI","LOGO","CIMSA"]
    rows=[]
    for sym in ADY:
        try:
            t=yf.Ticker(f"{sym}.IS"); h=t.history(period="65d")
            c=h["Close"].dropna(); v=h["Volume"].dropna()
            if len(c)<20: continue
            price=float(c.iloc[-1]); rs=float(calc_rsi(c).iloc[-1])
            du=50.
            c52=t.history(period="252d")["Close"].dropna()
            rng=float(c52.max())-float(c52.min()) if len(c52)>0 else 0
            if rng>0: du=(price-float(c52.min()))/rng*100
            s10=c.iloc[-10:].values
            ep=float(np.polyfit(range(len(s10)),s10,1)[0])/price*100
            va=0
            if len(v)>=10:
                v5=float(v.iloc[-5:].mean()); vo5=float(v.iloc[-10:-5].mean())
                if vo5>0: va=(v5-vo5)/vo5*100
            p=0
            if   25<=rs<=40:     p+=35
            elif 40<rs<=50:      p+=25
            elif rs<25:          p+=28
            elif 50<rs<=60:      p+=15
            else:                p+=5
            if   du<=20:         p+=30
            elif du<=35:         p+=22
            elif du<=50:         p+=14
            elif du<=65:         p+=7
            if   0<ep<=0.3:      p+=20
            elif ep>0.3:         p+=12
            elif -0.2<ep<=0:     p+=10
            else:                p+=3
            if va>30 and rs<50:  p+=15
            elif va>10:          p+=8
            if   rs<35:          et="AŞIRI UCUZ"
            elif du<25:          et="52H DİP"
            elif ep>0:           et="DÖNÜŞ SİNYALİ"
            else:                et="DEĞER BÖLGESİ"
            rows.append({"Hisse":sym,"Fiyat":round(price,2),"RSI":round(rs,1),
                         "Dip":round(du,0),"Puan":min(p,100),"Etiket":et})
        except: continue
    rows.sort(key=lambda x:x["Puan"],reverse=True)
    return rows[:5]


# ══════════════════════════════════════════════════════════════════
#  VERİ ÇEK
# ══════════════════════════════════════════════════════════════════
now_t = now_tr()
mk    = makro_cek()
rdlst = radar_cek()
hbrl  = haberler_cek()
dv,dl,dr,ro,yk,tp2 = duygu()
chg_b = mk.get("BIST_CHG",0)

bist_s  = f"{mk['BIST']:,.0f}".replace(",",".") if mk["BIST"] else "—"
usd_s   = f"{mk['USD']:.2f}"  if mk["USD"]  else "—"
eur_s   = f"{mk['EUR']:.2f}"  if mk["EUR"]  else "—"
gram_s  = ftl(mk["GRAM"],0);   ons_s   = fusd(mk["ONS"],0)
btc_s   = fusd(mk["BTC"],0);   eth_s   = fusd(mk["ETH"],0)
brent_s = fusd(mk["PETROL"],1)
bist_ch = fchg(mk["BIST_CHG"]); btc_ch = fchg(mk["BTC_CHG"])

# ══════════════════════════════════════════════════════════════════
#  TOP BAR
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class='topbar topbar-d'>
  <div class='t-logo'>
    <div class='live-dot'></div>
    Emrah<span class='t-dot'>.</span>AI
    <span class='t-badge'>Finans v6.2 RT</span>
  </div>
  <div class='t-strip'>
    <div class='t-item'><span class='t-lbl'>BIST 100</span>
      <span class='t-val'>{bist_s}</span>{bist_ch}</div>
    <div class='t-item'><span class='t-lbl'>USD/TRY</span>
      <span class='t-val'>{usd_s}</span></div>
    <div class='t-item'><span class='t-lbl'>EUR/TRY</span>
      <span class='t-val'>{eur_s}</span></div>
    <div class='t-item'><span class='t-lbl'>GRAM ALTIN</span>
      <span class='t-val'>{gram_s}</span></div>
    <div class='t-item'><span class='t-lbl'>ONS ALTIN</span>
      <span class='t-val'>{ons_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BTC</span>
      <span class='t-val'>{btc_s}</span>{btc_ch}</div>
    <div class='t-item'><span class='t-lbl'>ETH</span>
      <span class='t-val'>{eth_s}</span></div>
    <div class='t-item'><span class='t-lbl'>BRENT</span>
      <span class='t-val'>{brent_s}</span></div>
    <div class='t-item'><span class='t-lbl'>TCMB</span>
      <span class='t-val'>%37,00</span><span class='t-fl'>SABİT</span></div>
    <div class='t-item'><span class='t-lbl'>TR SAAT</span>
      <span class='t-val'>{now_t.strftime('%H:%M:%S')}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Mobil bar
st.markdown(
    "<div class='topbar-m'><div style='background:#0f172a;padding:10px 14px 6px;"
    "border-bottom:2px solid #1e3a5f;'>"
    "<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>"
    "<div style='display:flex;align-items:center;gap:8px;'><div class='live-dot'></div>"
    "<span style='font-family:IBM Plex Mono,monospace;font-size:15px;font-weight:700;color:#f1f5f9;'>"
    "PAPRIKA<span style='color:#38bdf8;'>.</span>AI</span>"
    "<span style='font-size:9px;background:#1e3a5f;color:#7dd3fc;padding:2px 7px;border-radius:4px;'>v6.2</span>"
    "</div>"
    f"<span style='font-family:IBM Plex Mono,monospace;font-size:12px;color:#94a3b8;'>"
    f"{now_t.strftime('%H:%M')} TR</span></div>"
    "<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:1px;"
    "background:#1e3a5f;border-radius:8px;overflow:hidden;'>"
    f"<div style='background:#0d1b2e;padding:7px 8px;'><div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>BIST</div><div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{bist_s}</div><div style='font-size:10px;'>{bist_ch}</div></div>"
    f"<div style='background:#0d1b2e;padding:7px 8px;'><div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>USD/TL</div><div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{usd_s}</div></div>"
    f"<div style='background:#0d1b2e;padding:7px 8px;'><div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>GRAM</div><div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{gram_s}</div></div>"
    f"<div style='background:#0d1b2e;padding:7px 8px;'><div style='font-size:9px;color:#64748b;font-weight:700;text-transform:uppercase;margin-bottom:2px;'>BTC</div><div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;'>{btc_s}</div></div>"
    "</div></div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  1. RADAR
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='sw'><div class='sh'><div class='sb'></div>"
            "<div class='stitle'>En Yüksek Hacimli 8 Hisse — Para Akışı Radarı</div>"
            "<div class='ssub'>yfinance · ~15dk · 60s yenileme</div></div>",
            unsafe_allow_html=True)
if rdlst:
    cards="<div class='rg'>"
    for r in rdlst:
        sl,sc=sinyal(r["chg"])
        cc="rc-up" if r["chg"]>=0 else "rc-dn"
        cs="▲" if r["chg"]>=0 else "▼"
        cards+=(f"<div class='rc rc-{sc}'>"
                f"<div class='rc-tic'>{r['sym']}</div>"
                f"<div class='rc-fiy'>{ftl(r['price'])}</div>"
                f"<div class='rc-vol'>Günlük: {hfmt(r['vol_tl'])}</div>"
                f"<span class='pill p-{sc}'>{sl}</span>"
                f"<div class='{cc}'>{cs} %{abs(r['chg']):.2f}</div></div>")
    st.markdown(cards+"</div></div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  2. STRATEJİK KARAR MATRİSİ
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='sw'><div class='sh'><div class='sb'></div>"
            "<div class='stitle'>Stratejik Karar Matrisi — Çok Boyutlu Analiz Top 10</div>"
            "<div class='ssub'>Teknik %40 · Duygu %25 · Analitik %25 · Sosyal %10</div></div>",
            unsafe_allow_html=True)
with st.spinner("BIST analizi yapılıyor…"):
    df=top10()

if not df.empty:
    tbody=""
    for rank,row in df.iterrows():
        dc="td-u" if row["Deg"]>=0 else "td-d"
        cs="▲" if row["Deg"]>=0 else "▼"
        bw=min(int(row["Puan"]),100)
        if   row["Sinyal"]=="GÜÇLÜ AL":  sb,sc2="#dcfce7","#15803d"
        elif row["Sinyal"]=="AL":         sb,sc2="#eff6ff","#1d4ed8"
        elif row["Sinyal"]=="DİP BÖLGE": sb,sc2="#fffbeb","#92400e"
        elif row["Sinyal"]=="HABER POZ.":sb,sc2="#f5f3ff","#6d28d9"
        else:                             sb,sc2="#f8fafc","#475569"
        hr="#16a34a" if row["HSk"]>=0 else "#dc2626"
        tbody+=(f"<tr><td><span class='td-r'>{rank}</span></td>"
                f"<td style='font-weight:700;color:#0f172a;'>{row['Hisse']}</td>"
                f"<td style='font-weight:700;color:#1e293b;'>{ftl(row['Fiyat'])}</td>"
                f"<td style='font-weight:700;color:#15803d;'>{ftl(row['Fiyat']*1.15)}</td>"
                f"<td class='{dc}'>{cs} %{abs(row['Deg']):.2f}</td>"
                f"<td><b style='color:#2563eb;'>{row['RSI']}</b> "
                f"<span style='font-size:11px;color:#64748b;'>{'Ucuz' if row['RSI']<45 else ('Güçlü' if row['RSI']<65 else 'Pahalı')}</span></td>"
                f"<td><span style='font-weight:700;color:{hr};'>{'▲' if row['HSk']>=0 else '▼'} {abs(row['HSk']):.1f}</span></td>"
                f"<td><div style='display:flex;align-items:center;gap:6px;'>"
                f"<b style='color:#1d4ed8;white-space:nowrap;'>{row['Puan']:.0f}/100</b>"
                f"<div style='flex:1;min-width:55px;'>"
                f"<div style='background:#f1f5f9;border-radius:3px;height:4px;overflow:hidden;'>"
                f"<div style='height:100%;width:{bw}%;background:linear-gradient(90deg,#2563eb,#38bdf8);border-radius:3px;'></div></div>"
                f"<div style='font-size:9px;color:#94a3b8;margin-top:1px;'>T:{row['TP']} D:{row['DP']} A:{row['AP']} S:{row['SP']}</div>"
                f"</div></div></td>"
                f"<td><span style='font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;"
                f"background:{sb};color:{sc2};white-space:nowrap;'>{row['Sinyal']}</span></td>"
                f"<td style='color:#475569;font-size:12px;'>{hfmt(row['TLH'])}</td></tr>")
    st.markdown(f"<div class='mw'><table class='mt'><thead><tr>"
                f"<th>#</th><th>Hisse</th><th>Fiyat</th><th>Hedef +15%</th>"
                f"<th>Değişim</th><th>RSI</th><th>Haber Sk.</th>"
                f"<th>Puan (T·D·A·S)</th><th>Sinyal</th><th>TL Hacim</th>"
                f"</tr></thead><tbody>{tbody}</tbody></table></div></div>",
                unsafe_allow_html=True)
else:
    st.markdown("<div class='sw'><p style='color:#dc2626;'>Veri alınamadı.</p></div>",
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  3. SENSOR PANELLERİ
# ══════════════════════════════════════════════════════════════════
with st.spinner("Sensörler hesaplanıyor…"):
    fplst=fp_radar()

rdvol = sum(r["vol_tl"] for r in rdlst) if rdlst else 0
hcm_s = hfmt(rdvol) if rdvol>0 else "—"
alp   = min(max(50+chg_b*4,30),80); satp=100-alp
hcr   = "#16a34a" if chg_b>=0 else "#dc2626"
hcs   = "▲ +" if chg_b>0 else "▼ "

fprows=""
for i,r in enumerate(fplst,1):
    bc="fpbdg-g" if ("UCUZ" in r["Etiket"] or "DİP" in r["Etiket"]) else ("fpbdg-b" if "DÖNÜŞ" in r["Etiket"] else "fpbdg-a")
    fprows+=(f"<div class='fprow'>"
             f"<div style='display:flex;flex-direction:column;gap:3px;flex:1;'>"
             f"<span class='fpname'>{i}. {r['Hisse']}</span>"
             f"<span class='fpmeta'>{ftl(r['Fiyat'])} · RSI:{r['RSI']} · 52H:%{r['Dip']:.0f} · Puan:{r['Puan']}</span>"
             f"<div style='background:#e2e8f0;border-radius:3px;height:3px;width:80px;overflow:hidden;margin-top:3px;'>"
             f"<div style='height:100%;width:{int(r['Puan'])}%;background:linear-gradient(90deg,#2563eb,#60a5fa);border-radius:3px;'></div></div>"
             f"</div><span class='fpbdg {bc}'>{r['Etiket']}</span></div>")
if not fprows:
    fprows="<div style='color:#475569;font-size:12px;padding:14px 0;text-align:center;'>Hesaplanıyor…</div>"

K1=(f"<div class='kart' style='border-left:4px solid #2563eb;'>"
    f"<div class='kart-hdr' style='color:#2563eb;'>💎 F/P Değerleme Radarı — Top 5</div>"
    f"{fprows}</div>")

K2=(f"<div class='kart' style='border-left:4px solid #16a34a;'>"
    f"<div class='kart-hdr' style='color:#16a34a;'>📈 Günlük Para Akışı &amp; Hacim</div>"
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:26px;font-weight:700;color:{hcr};margin:4px 0 3px;'>{'📈' if chg_b>=0 else '📉'} {hcm_s}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>BIST100 · ~15dk gecikme</div>"
    f"<div style='background:#e2e8f0;border-radius:6px;height:6px;overflow:hidden;margin-bottom:7px;'>"
    f"<div style='width:{int(alp)}%;height:100%;border-radius:6px;background:{'linear-gradient(90deg,#16a34a,#4ade80)' if chg_b>=0 else 'linear-gradient(90deg,#dc2626,#f87171)'};'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:12px;font-weight:700;margin-bottom:10px;'>"
    f"<span style='color:#16a34a;'>ALIŞ %{alp:.0f}</span><span style='color:#dc2626;'>SATIŞ %{satp:.0f}</span></div>"
    f"<div class='krow'><span class='klbl'>BIST100</span><span class='kval'>{bist_s}</span></div>"
    f"<div class='krow'><span class='klbl'>Değişim</span><span class='kval' style='color:{hcr};'>{hcs}%{abs(chg_b):.2f}</span></div>"
    f"<div class='krow'><span class='klbl'>İşlem Hacmi</span><span class='kval' style='color:#2563eb;'>{hcm_s}</span></div>"
    f"</div>")

K3=(f"<div class='kart' style='border-left:4px solid #7c3aed;'>"
    f"<div class='kart-hdr' style='color:#7c3aed;'>🧠 BIST Duygu Endeksi</div>"
    f"<div style='font-family:IBM Plex Mono,monospace;font-size:48px;font-weight:700;line-height:1;color:{dr};margin:4px 0 2px;'>{dv}</div>"
    f"<div style='font-size:13px;font-weight:600;color:{dr};margin-bottom:3px;'>{dl}</div>"
    f"<div style='font-size:11px;color:#64748b;margin-bottom:10px;'>RSI Ort: <b style='color:#1e293b;'>{ro}</b></div>"
    f"<div style='background:#e2e8f0;border-radius:8px;height:7px;overflow:hidden;margin-bottom:4px;'>"
    f"<div style='height:100%;width:{dv}%;background:{dr};border-radius:8px;'></div></div>"
    f"<div style='display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;font-family:IBM Plex Mono,monospace;margin-bottom:10px;'>"
    f"<span>KORKU</span><span>NÖTR</span><span>AÇGÖZLÜLÜK</span></div>"
    f"<div class='krow'><span class='klbl'>Yükselen / Toplam</span>"
    f"<span class='kval' style='color:#16a34a;'>{yk} / {tp2}</span></div>"
    f"<div class='krow'><span class='klbl'>Yöntem</span>"
    f"<span class='kval' style='color:#475569;font-size:11px;'>RSI %60 · Yön %30 · Mom %10</span></div>"
    f"</div>")

st.markdown(
    "<div style='padding:14px 24px 10px;'>"
    "<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>"
    "<div style='width:4px;height:20px;background:#2563eb;border-radius:3px;'></div>"
    "<span style='font-family:IBM Plex Mono,monospace;font-size:11px;font-weight:700;"
    "letter-spacing:1.8px;text-transform:uppercase;color:#2563eb;'>Derin Analiz Sensörleri</span>"
    "<span style='margin-left:auto;font-size:11px;color:#94a3b8;'>F/P · Para Akışı · Duygu</span></div>"
    "<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start;'>"
    +K1+K2+K3+"</div></div>",
    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  HİSSE FİYAT TAKİP MODÜLÜ
# ══════════════════════════════════════════════════════════════════
st.markdown(
    "<div class='sw'>"
    "<div class='sh'>"
    "<div class='sb' style='background:#0ea5e9;'></div>"
    "<div class='stitle' style='color:#0ea5e9;'>🔎 Anlık Hisse Fiyat Takibi</div>"
    "<div class='ssub'>Tüm Borsa İstanbul · 30s önbellek · yfinance ~15dk</div>"
    "</div>",
    unsafe_allow_html=True)

# Satır 1: selectbox + yenile butonu (küçük, solda)
col_sel, col_btn, col_bos = st.columns([1, 1, 4], gap="small")
with col_sel:
    secili = st.selectbox(
        "Hisse seç", options=BIST_FULL, index=0,
        key="hisse_sec", help="300+ Borsa İstanbul hissesi")
with col_btn:
    st.markdown("<div style='margin-top:28px;'>", unsafe_allow_html=True)
    if st.button("🔄 Yenile", key="htk_ynl", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Satır 2: veri kartı (tam genişlik)
veri = hisse_cek(secili)
if veri:
    price = veri["price"]; chg = veri["chg"]; ctl = veri["chg_tl"]
    rk    = "#16a34a" if chg >= 0 else "#dc2626"
    cs2   = "▲ +" if chg > 0 else "▼ "
    rv    = veri.get("rsi")
    rs2   = f"{rv}" if rv is not None else "—"
    th    = hfmt(veri.get("tl_hacim", 0))
    rng52 = veri["max52"] - veri["min52"]
    p52   = round((price - veri["min52"]) / max(rng52, 0.01) * 100, 1)
    rrk   = "#dc2626" if rv and rv > 70 else "#16a34a" if rv and rv < 30 else "#1e293b"
    rnt   = " ⚠️ Aşırı Alım" if rv and rv > 70 else " ✅ Aşırı Satış" if rv and rv < 30 else ""
    bp    = min(max(int(p52), 0), 100)
    brk   = "#16a34a" if bp < 40 else "#d97706" if bp < 70 else "#dc2626"
    rsi_w = min(max(int(rv or 50), 0), 100)
    rsi_r = "#dc2626" if (rv or 50) > 70 else "#16a34a" if (rv or 50) < 30 else "#d97706"

    # Fiyat değişim rengi/ikon
    chg_str = f"{cs2}%{abs(chg):.2f}"
    ctl_str = f"({'+' if ctl>=0 else ''}₺{ctl:,.2f})"

    card = (
        f"<div style='background:#fff;border:1.5px solid #dde3ec;"
        f"border-left:4px solid #0ea5e9;border-radius:12px;padding:20px 24px;margin-top:8px;'>"

        # Üst: sembol + saat
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"margin-bottom:14px;padding-bottom:12px;border-bottom:1.5px solid #e2e8f0;'>"
        f"<div style='display:flex;align-items:baseline;gap:8px;'>"
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:17px;font-weight:700;"
        f"color:#0f172a;'>{secili}.IS</span>"
        f"<span style='font-size:11px;color:#94a3b8;'>Borsa İstanbul</span>"
        f"</div>"
        f"<span style='font-size:10px;color:#94a3b8;font-family:IBM Plex Mono,monospace;'>"
        f"{now_t.strftime('%H:%M')} TR · ~15dk gecikme</span>"
        f"</div>"

        # Ana içerik: sol fiyat bloku, sağ metrikler
        f"<div style='display:grid;grid-template-columns:230px 1fr;gap:28px;align-items:start;'>"

        # SOL
        f"<div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:34px;font-weight:700;"
        f"color:{rk};line-height:1.1;margin-bottom:4px;'>₺{price:,.2f}</div>"
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>"
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:14px;font-weight:700;"
        f"color:{rk};'>{chg_str}</span>"
        f"<span style='font-size:12px;color:#64748b;'>{ctl_str}</span>"
        f"</div>"
        f"<div style='font-size:11px;color:#94a3b8;margin-bottom:16px;'>"
        f"Önceki kapanış: <b style='color:#475569;'>₺{veri['prev']:,.2f}</b></div>"

        # 52H çubuk
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
        f"border-radius:10px;padding:12px 14px;'>"
        f"<div style='font-size:10px;font-weight:700;color:#64748b;"
        f"letter-spacing:.5px;text-transform:uppercase;margin-bottom:7px;'>52H Pozisyon</div>"
        f"<div style='background:#e2e8f0;border-radius:6px;height:7px;overflow:hidden;margin-bottom:6px;'>"
        f"<div style='height:100%;width:{bp}%;background:{brk};border-radius:6px;'></div></div>"
        f"<div style='display:flex;justify-content:space-between;font-size:10px;'>"
        f"<span style='color:#16a34a;font-weight:700;font-family:IBM Plex Mono,monospace;"
        f"font-size:10px;'>DİP ₺{veri['min52']:,.2f}</span>"
        f"<span style='color:#64748b;font-weight:600;'>%{p52}</span>"
        f"<span style='color:#dc2626;font-weight:700;font-family:IBM Plex Mono,monospace;"
        f"font-size:10px;'>ZİRVE ₺{veri['max52']:,.2f}</span>"
        f"</div></div>"
        f"</div>"  # sol kapanış

        # SAĞ — metrik satırları
        f"<div>"
    )

    def mrow(lbl, val_html, border=True):
        b = "border-bottom:1px solid #f1f5f9;" if border else ""
        return (f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:8px 0;{b}'>"
                f"<span style='font-size:12px;color:#64748b;'>{lbl}</span>"
                f"<span style='font-family:IBM Plex Mono,monospace;font-size:12px;"
                f"font-weight:700;color:#1e293b;'>{val_html}</span>"
                f"</div>")

    card += mrow("RSI (14)",
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"<div style='background:#e2e8f0;border-radius:3px;height:4px;overflow:hidden;width:70px;'>"
        f"<div style='height:100%;width:{rsi_w}%;background:{rsi_r};border-radius:3px;'></div></div>"
        f"<span style='color:{rrk};'>{rs2}{rnt}</span></div>")
    card += mrow("TL Hacim", th)
    card += mrow("5G Min / Max",
        f"<span style='color:#16a34a;'>₺{veri['min5']:,.2f}</span>"
        f"<span style='color:#94a3b8;font-weight:400;'> / </span>"
        f"<span style='color:#dc2626;'>₺{veri['max5']:,.2f}</span>")
    card += mrow("52H Dip",
        f"<span style='color:#16a34a;'>₺{veri['min52']:,.2f}</span>")
    card += mrow("52H Zirve",
        f"<span style='color:#dc2626;'>₺{veri['max52']:,.2f}</span>")
    card += mrow("Hedef (+15%)",
        f"<span style='color:#2563eb;background:#eff6ff;"
        f"padding:2px 9px;border-radius:6px;'>₺{price*1.15:,.2f}</span>",
        border=False)

    card += "</div></div></div>"  # sağ + grid + kart kapanış
    st.markdown(card, unsafe_allow_html=True)

else:
    st.markdown(
        f"<div style='background:#fff;border:1.5px solid #dde3ec;"
        f"border-left:4px solid #f87171;border-radius:12px;"
        f"padding:18px 22px;margin-top:8px;color:#dc2626;"
        f"font-size:13px;font-weight:600;'>"
        f"⚠️ <b>{secili}</b> için veri alınamadı — "
        f"Yahoo Finance'de aktif olmayabilir.</div>",
        unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # sw kapanış

# ══════════════════════════════════════════════════════════════════
#  4. PİYASA İSTİHBARATI
# ══════════════════════════════════════════════════════════════════
with st.spinner("İstihbarat analizi yapılıyor…"):
    istlst=istihbarat()

if   chg_b>1.5: bsts="Endeks güçlü yükseliyor. Momentum hisselerine odaklan: THYAO, ASELS, YKBNK."
elif chg_b>0:   bsts="Endeks ılımlı pozitif. Seçici alım fırsatı — düşük RSI'li hisseler cazip."
elif chg_b>-1:  bsts="Endeks yatay. Dip bölgelerinde biriktirme yapılabilir."
else:           bsts="Endeks baskılı. Savunma hisseleri ve altın öne çıkabilir."

ptry=f"Brent {brent_s} — {'100$/v üstünde. AKSEN/ENJSA olumlu.' if mk['PETROL']>100 else 'Normal. TUPRS nötr.' if mk['PETROL']>80 else 'Düşük. TUPRS marjları olumlu.'}"
bv=mk.get("BTC",0)
ky="Risk iştahı yüksek." if bv>90000 else "BTC konsolidasyon." if bv>70000 else "BTC baskılı. Risk-off."

def ist_row(item):
    d=item["duygu"]
    if d=="pozitif": bg,c2,ic="#f0fdf4","#15803d","▲"
    elif d=="negatif": bg,c2,ic="#fef2f2","#b91c1c","▼"
    else: bg,c2,ic="#f8fafc","#475569","─"
    return (f"<div style='padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:5px;'>"
            f"<span style='font-size:10px;font-weight:700;padding:2px 7px;border-radius:5px;"
            f"background:{bg};color:{c2};'>{ic} {item['sektor'].upper()}</span>"
            f"<span style='font-size:10px;color:#94a3b8;font-family:IBM Plex Mono,monospace;'>{item['zaman']}</span>"
            f"</div><div style='font-size:12px;line-height:1.5;'>"
            f"{safe_link(item['link'],item['title'])}</div></div>")

makro_items=[
    {"title":f"TCMB faizi %37 sabit · Haziran indirim beklentisi gündemde.",
     "zaman":now_t.strftime("%d.%m %H:%M"),"link":"https://www.tcmb.gov.tr","duygu":"nötr","sektor":"tcmb"},
    {"title":f"USD/TRY {usd_s} · GRAM ALTIN {gram_s} · ONS {ons_s}",
     "zaman":now_t.strftime("%d.%m %H:%M"),"link":"https://www.tcmb.gov.tr/kurlar/today.xml","duygu":"nötr","sektor":"döviz"},
    {"title":ptry,"zaman":now_t.strftime("%d.%m %H:%M"),
     "link":"https://finance.yahoo.com/quote/BZ%3DF/","duygu":"nötr","sektor":"petrol"},
    {"title":f"BTC {btc_s} {'+' if mk.get('BTC_CHG',0)>=0 else ''}%{mk.get('BTC_CHG',0):.2f} (24s) · {ky}",
     "zaman":now_t.strftime("%d.%m %H:%M"),"link":"https://www.coingecko.com/en/coins/bitcoin","duygu":"nötr","sektor":"kripto"},
]
sol_h="".join(ist_row(x) for x in istlst[:4]) or "<div style='color:#94a3b8;font-size:12px;padding:12px;'>Yükleniyor…</div>"
sag_h="".join(ist_row(x) for x in makro_items)

st.markdown(f"""
<div class="sw">
  <div class="sh"><div class="sb"></div>
    <div class="stitle">Piyasa İstihbaratı — Hisse Seçim Rehberi</div>
    <div class="ssub">Haber + Duygu · {now_t.strftime("%d.%m.%Y %H:%M")} TR</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
    <div style="background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #2563eb;border-radius:12px;padding:18px 20px;">
      <div style="font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#2563eb;margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;">
        🔍 Borsa Haber Analizi — Canlı Duygu</div>
      {sol_h}
    </div>
    <div style="background:#fff;border:1.5px solid #dde3ec;border-left:4px solid #d97706;border-radius:12px;padding:18px 20px;">
      <div style="font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#d97706;margin-bottom:12px;padding-bottom:10px;border-bottom:1.5px solid #e2e8f0;">
        🌐 Makro & Strateji Rehberi</div>
      <div style="font-size:13px;font-weight:600;color:#1e293b;margin-bottom:8px;">
        BIST {bist_s} · {bsts}</div>
      {sag_h}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  5. HABER AKIŞI + SOSYAL GÜNDEM
# ══════════════════════════════════════════════════════════════════
with st.spinner("Haberler yükleniyor…"):
    svlst=sosyal_cek()

def hb_row(z, k, b, l, ok="#2563eb"):
    return (f"<div style='display:flex;align-items:flex-start;gap:10px;"
            f"padding:9px 0;border-bottom:1px solid #f1f5f9;'>"
            f"<span style='font-family:IBM Plex Mono,monospace;font-size:11px;font-weight:700;"
            f"color:#dc2626;min-width:52px;flex-shrink:0;margin-top:1px;'>{z}</span>"
            f"<div style='font-size:13px;line-height:1.5;'>"
            f"<span style='font-size:10px;font-weight:700;background:#eff6ff;color:#1d4ed8;"
            f"padding:1px 6px;border-radius:3px;margin-right:5px;white-space:nowrap;'>{k}</span>"
            f"{safe_link(l,b,ok)}</div></div>")

hbr_s=sorted(hbrl,key=lambda x:x[0],reverse=True) if hbrl else []
hh="".join(hb_row(z,k,b,l,"#2563eb") for z,k,b,l in hbr_s[:7])
if not hh:
    hh=(f"<div style='background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;"
        f"padding:10px 14px;font-size:12px;color:#92400e;'>⚠️ Haberler alınamıyor.<br>"
        f"{safe_link('https://www.kap.org.tr/tr/bildirim-sorgu','KAP')} · "
        f"{safe_link('https://bigpara.hurriyet.com.tr','Bigpara')}</div>")

sh="".join(hb_row(z,k,b,l,"#7c3aed") for z,k,b,l in svlst[:7])
if not sh:
    sh="<div style='color:#94a3b8;font-size:12px;padding:12px 0;'>Yükleniyor…</div>"

st.markdown(
    "<div class='sw'><div class='sh'><div class='sb'></div>"
    "<div class='stitle'>Canlı Haber Akışı & Sosyal Gündem</div>"
    "<div class='ssub'>RSS · Google News · Tıkla → habere git ↗</div></div>"
    "<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>"

    "<div style='background:#fff;border:1.5px solid #dde3ec;border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#1d4ed8;"
    "margin-bottom:12px;padding-bottom:11px;border-bottom:1.5px solid #e2e8f0;'>"
    "🌍 Borsa & Ekonomi Haberleri</div>"
    +hh+
    "</div>"

    "<div style='background:#fff;border:1.5px solid #dde3ec;border-left:3px solid #7c3aed;"
    "border-radius:12px;padding:18px 20px;'>"
    "<div style='font-family:IBM Plex Mono,monospace;font-size:10px;font-weight:700;"
    "letter-spacing:1.5px;text-transform:uppercase;color:#7c3aed;"
    "margin-bottom:6px;padding-bottom:6px;border-bottom:1.5px solid #e2e8f0;'>"
    "📰 Gündemdekiler — BIST100 Finans Gündemi</div>"
    "<div style='font-size:11px;color:#94a3b8;margin-bottom:10px;'>"
    "Google News · TR saati · Tıkla → habere git ↗</div>"
    +sh+
    "</div>"
    "</div></div>",
    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class='footer'>
  <span>PAPRIKA.AI © 2026 — Elite Terminal v6.2</span>
  <span>TR Saati: {now_t.strftime('%d.%m.%Y %H:%M:%S')} (UTC+3) | ⏱ 60s oto-yenileme</span>
  <span>yfinance ~15dk · TCMB Döviz · CoinGecko · G.News · ⚠️ Yatırım tavsiyesi değildir</span>
</div>
""", unsafe_allow_html=True)
