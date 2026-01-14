import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Radar", page_icon="📡", layout="wide")
st.title("📡 Global Market Radar: Aktien & ETFs")

# --- 2. DATEN DEFINITIONEN ---

# A) AKTIEN SEKTOREN
STOCK_SECTORS = {
    "✈️ Luft- & Raumfahrt": {
        'Airbus': 'AIR.PA', 'Boeing': 'BA', 'Lockheed Martin': 'LMT',
        'Rheinmetall': 'RHM.DE', 'Safran': 'SAF.PA', 'MTU Aero': 'MTX.DE',
        'Rolls-Royce': 'RR.L', 'Thales': 'HO.PA', 'General Dynamics': 'GD'
    },
    "🤖 KI & Halbleiter": {
        'Nvidia': 'NVDA', 'TSMC': 'TSM', 'ASML': 'ASML', 'AMD': 'AMD',
        'Intel': 'INTC', 'Broadcom': 'AVGO', 'Qualcomm': 'QCOM', 'Infineon': 'IFX.DE'
    },
    "☁️ Big Tech & Software": {
        'Microsoft': 'MSFT', 'Apple': 'AAPL', 'Google': 'GOOGL', 'Amazon': 'AMZN',
        'Meta': 'META', 'SAP': 'SAP', 'Palantir': 'PLTR', 'Salesforce': 'CRM'
    },
    "🧬 Healthcare": {
        'Novo Nordisk': 'NVO', 'Eli Lilly': 'LLY', 'Intuitive Surgical': 'ISRG',
        'Pfizer': 'PFE', 'Johnson & Johnson': 'JNJ', 'Merck US': 'MRK'
    },
    "🚗 Auto & E-Mobility": {
        'Tesla': 'TSLA', 'BYD': 'BYDDF', 'VW': 'VOW3.DE', 'Mercedes': 'MBG.DE',
        'BMW': 'BMW.DE', 'Ferrari': 'RACE', 'Toyota': 'TM'
    },
    "⚡ Energie & GreenTech": {
        'Siemens Energy': 'ENR.DE', 'NextEra': 'NEE', 'First Solar': 'FSLR',
        'Schneider Electric': 'SU.PA', 'Vestas': 'VWS.CO', 'Enphase': 'ENPH'
    },
    "🌏 Emerging Markets": {
        'MercadoLibre': 'MELI', 'LVMH': 'MC.PA', 'Alibaba': 'BABA', 'HDFC Bank': 'HDB'
    },
    "💰 Finanzen": {
        'JPMorgan': 'JPM', 'Visa': 'V', 'Allianz': 'ALV.DE', 'BlackRock': 'BLK'
    }
}

# B) ETF SEKTOREN
ETF_SECTORS = {
    "🌍 Welt & Broad Market": {
        'S&P 500': 'VOO', 'MSCI World': 'URTH', 'Nasdaq 100': 'QQQ',
        'Total World': 'VT', 'Europe Stoxx 600': 'EXSA.DE', 'DAX 40': 'GDAXI'
    },
    "🚀 Tech & Innovation": {
        'Semiconductor': 'SOXX', 'Cyber Security': 'CIBR', 'AI & Robotics': 'BOTZ',
        'Clean Energy': 'ICLN', 'Ark Innovation': 'ARKK'
    },
    "💰 Dividenden & Value": {
        'High Dividend': 'VYM', 'Div. Aristocrats': 'NOBL', 'JPMorgan Premium': 'JEPI'
    },
    "🌏 Regionen": {
        'Emerging Markets': 'VWO', 'China Large-Cap': 'FXI', 'India': 'EPI', 'Japan': 'EWJ'
    },
    "🛡️ Bonds & Gold": {
        'US Treasury 20+Y': 'TLT', 'Corp Bonds': 'LQD', 'Gold': 'GLD', 'Silver': 'SLV'
    },
    "₿ Crypto": {
        'Bitcoin Strategy': 'BITO', 'Ether Strategy': 'EETH'
    }
}

# --- 3. ANALYSE LOGIKEN ---

# --- LOGIK FÜR AKTIEN ---
def calculate_porter_score(info):
    score = 0
    # 1. Pricing Power
    gm = info.get('grossMargins', 0)
    if gm and gm > 0.50: score += 3
    elif gm and gm > 0.30: score += 2
    elif gm and gm < 0.10: score -= 1
    # 2. Barriers (ROE)
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0.20: score += 3
    elif roe and roe > 0.12: score += 1
    # 3. Operative Effizienz
    om = info.get('operatingMargins', 0)
    if om and om > 0.15: score += 2
    # 4. Finanzielle Stärke
    de = info.get('debtToEquity', 100)
    if de and de < 80: score += 2
    return max(0, min(10, score))

def get_stock_trend_signal(price_series):
    if len(price_series) < 200: return "Neutral"
    sma200 = price_series.rolling(200).mean().iloc[-1]
    return "Bullish" if price_series.iloc[-1] > sma200 else "Bearish"

def get_stock_strategy_signal(porter_score, trend):
    if porter_score >= 8 and trend == "Bullish": return "🚀 SWEET SPOT", "Qualität wird erkannt"
    elif porter_score >= 7 and trend == "Bearish": return "💎 VALUE CHANCE", "Qualität irrational abgestraft"
    elif porter_score <= 4 and trend == "Bullish": return "⚠️ JUNK RALLY", "Hype ohne Qualität"
    else: return "⚪ Neutral", "Beobachten"

# --- LOGIK FÜR ETFS ---
def analyze_etf_metrics(name, ticker, history):
    if history.empty or len(history) < 200: return None
    
    curr = history.iloc[-1]
    sma200 = history.rolling(200).mean().iloc[-1]
    trend_dist = (curr - sma200) / sma200
    
    volatility = history.pct_change().tail(30).std() * (252**0.5)
    
    start_p = history.iloc[0]
    perf_1y = (curr - start_p) / start_p
    
    dd = (curr - history.max()) / history.max()
    
    signal = "⚪ Neutral"
    if trend_dist > 0.05 and perf_1y > 0.10:
        if volatility < 0.15: signal = "🚀 COMPOUNDER"
        else: signal = "🔥 MOMENTUM"
    elif trend_dist < -0.05:
        if dd < -0.20: signal = "⚠️ DIP / CRASH"
        else: signal = "❄️ COOLING"
        
    return {
        "Name": name, "Ticker": ticker, "Preis": curr, "Signal": signal,
        "Trend": trend_dist, "Vola": volatility, "Perf 1Y": perf_1y, "Drawdown": dd
    }

# --- 4. DATA LOADER FUNCTIONS ---

@st.cache_data
def scan_stocks_market():
    all_tickers = []
    t_map = {}
    for sec, comps in STOCK_SECTORS.items():
        for n, t in comps.items():
            all_tickers.append(t)
            t_map[t] = {'name': n, 'sector': sec}
            
    start = datetime.now() - timedelta(days=400)
    prices = yf.download(all_tickers, start=start, progress=False)['Close']
    
    results = []
    for t in all_tickers:
        try:
            stock = yf.Ticker(t)
            info = stock.info
            score = calculate_porter_score(info)
            trend = get_stock_trend_signal(prices[t].dropna()) if t in prices.columns else "Neutral"
            sig, desc = get_stock_strategy_signal(score, trend)
            
            results.append({
                "Unternehmen": t_map[t]['name'], 
                "Ticker": t, # <--- NEU
                "Sektor": t_map[t]['sector'],
                "Porter Score": score, "Trend": trend, "Signal": sig, "Info": desc,
                "KGV": info.get('trailingPE', 0), "Marge": info.get('grossMargins', 0)
            })
        except: continue
    return pd.DataFrame(results), prices

@st.cache_data
def scan_etfs_market():
    all_tickers = []
    t_map = {}
    for sec, comps in ETF_SECTORS.items():
        for n, t in comps.items():
            all_tickers.append(t)
            t_map[t] = {'name': n, 'sector': sec}
            
    prices = yf.download(all_tickers, period="1y", progress=False)['Close']
    results = []
    for t in all_tickers:
        try:
            if t in prices.columns:
                res = analyze_etf_metrics(t_map[t]['name'], t, prices[t].dropna())
                if res:
                    res['Sektor'] = t_map[t]['sector']
                    results.append(res)
        except: continue
    return pd.DataFrame(results), prices

# --- 5. HAUPTNAVIGATION ---

mode = st.sidebar.radio("🔍 Modus wählen:", ["🏢 Aktien (Porter & Strategie)", "🌐 ETFs (Trend & Risiko)"])

st.sidebar.markdown("---")
st.sidebar.caption("Datenquelle: Yahoo Finance")

# --- 6. VIEW: AKTIEN ---

if "Aktien" in mode:
    st.markdown("### 🏢 Aktien-Scanner: Qualität & Marktpsychologie")
    st.markdown("Kombination aus **Michael Porters Wettbewerbsstrategie** (Moat) und **Rationalen Erwartungen** (Trend).")
    
    with st.spinner("Analysiere Aktienmarkt (Porter-Score & Trends)..."):
        stock_df, stock_prices = scan_stocks_market()
        
    # KPI Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("🚀 Sweet Spots", len(stock_df[stock_df['Signal'].str.contains("SWEET")]), "Qualität + Trend")
    c2.metric("💎 Value Chancen", len(stock_df[stock_df['Signal'].str.contains("VALUE")]), "Qualität günstig")
    c3.metric("⚠️ Junk Rallys", len(stock_df[stock_df['Signal'].str.contains("JUNK")]), "Schlechte Qualität steigt")
    
    # Tabelle
    def style_stock(v):
        if 'SWEET' in v: return 'background-color: #1f77b4; color: white'
        if 'VALUE' in v: return 'background-color: #2ca02c; color: white'
        if 'JUNK' in v: return 'background-color: #d62728; color: white'
        return ''

    # Spaltenauswahl für die Anzeige
    display_cols = ['Unternehmen', 'Ticker', 'Signal', 'Porter Score', 'Trend', 'KGV', 'Marge', 'Sektor']
    
    st.dataframe(
        stock_df[display_cols].style.applymap(style_stock, subset=['Signal']),
        column_config={
            "Ticker": st.column_config.TextColumn("Kürzel", width="small"),
            "Porter Score": st.column_config.ProgressColumn("Porter Score", min_value=0, max_value=10, format="%d"),
            "Marge": st.column_config.NumberColumn("Bruttomarge", format="%.1f%%"),
            "KGV": st.column_config.NumberColumn("KGV", format="%.1f"),
        }, use_container_width=True, height=500, hide_index=True
    )
    
    st.divider()
    
    # Detail Section
    st.subheader("🔍 Sektor Deep-Dive")
    sec_select = st.selectbox("Sektor wählen:", list(STOCK_SECTORS.keys()))
    
    # Chart
    tickers = list(STOCK_SECTORS[sec_select].values())
    valid = [t for t in tickers if t in stock_prices.columns]
    
    if valid:
        subset = stock_prices[valid].dropna(how='all')
        if not subset.empty:
            norm = subset / subset.iloc[0] * 100
            st.line_chart(norm)
    
    # Erklärung
    with st.expander("ℹ️ Wie funktioniert der Porter-Score?"):
        st.write("""
        Der Score (0-10) misst die strategische Stärke:
        * **Pricing Power:** Hohe Bruttomarge (>50%) = 3 Punkte.
        * **Burggraben (Moat):** Hoher ROE (>20%) = 3 Punkte.
        * **Effizienz:** Hohe operative Marge = 2 Punkte.
        * **Sicherheit:** Geringe Schulden = 2 Punkte.
        """)

# --- 7. VIEW: ETFS ---

elif "ETFs" in mode:
    st.markdown("### 🌐 ETF-Scanner: Trend & Risiko")
    st.markdown("Fokus auf **Momentum, Volatilität und Drawdowns**, da ETFs keine klassischen Bilanzen haben.")
    
    with st.spinner("Analysiere ETF Universum..."):
        etf_df, etf_prices = scan_etfs_market()
        
    # KPI Cards
    c1, c2, c3 = st.columns(3)
    best = etf_df.loc[etf_df['Perf 1Y'].idxmax()]
    safe = etf_df.loc[etf_df['Vola'].idxmin()]
    dip = etf_df.loc[etf_df['Drawdown'].idxmin()]
    
    # Zeige Name + Ticker in der Metric
    c1.metric(f"🏆 Top Perf: {best['Name']} ({best['Ticker']})", f"{best['Perf 1Y']:.1%}")
    c2.metric(f"🛡️ Sicherster: {safe['Name']} ({safe['Ticker']})", f"Vola: {safe['Vola']:.1%}")
    c3.metric(f"📉 Tiefster Dip: {dip['Name']} ({dip['Ticker']})", f"{dip['Drawdown']:.1%}")
    
    # Tabelle
    def style_etf(v):
        if 'COMPOUNDER' in v: return 'background-color: #2ca02c; color: white'
        if 'MOMENTUM' in v: return 'background-color: #1f77b4; color: white'
        if 'CRASH' in v: return 'background-color: #d62728; color: white'
        if 'COOLING' in v: return 'background-color: orange; color: black'
        return ''

    display_cols_etf = ['Name', 'Ticker', 'Signal', 'Preis', 'Perf 1Y', 'Trend', 'Vola', 'Drawdown', 'Sektor']

    st.dataframe(
        etf_df[display_cols_etf].style.applymap(style_etf, subset=['Signal']),
        column_config={
            "Ticker": st.column_config.TextColumn("Kürzel", width="small"),
            "Perf 1Y": st.column_config.ProgressColumn("Perf (1J)", min_value=-0.5, max_value=0.5, format="%.1f%%"),
            "Trend": st.column_config.NumberColumn("Trend (SMA200)", format="%.1f%%"),
            "Vola": st.column_config.NumberColumn("Risiko (Vola)", format="%.1f%%"),
            "Drawdown": st.column_config.NumberColumn("Max Drawdown", format="%.1f%%"),
            "Preis": st.column_config.NumberColumn("Kurs", format="%.2f"),
        }, use_container_width=True, height=600, hide_index=True
    )
    
    st.divider()
    
    # Detail Section
    st.subheader("📈 Vergleichs-Chart")
    
    # Hier bauen wir eine Liste "Name (Ticker)" für die Auswahlbox
    etf_df['Display_Name'] = etf_df['Name'] + " (" + etf_df['Ticker'] + ")"
    
    compare_select = st.multiselect(
        "ETFs vergleichen:", 
        etf_df['Display_Name'].unique(), 
        default=etf_df['Display_Name'].head(3).tolist()
    )
    
    # Chart Logic
    if compare_select:
        # Rückübersetzung Display_Name -> Ticker
        sel_tickers = etf_df[etf_df['Display_Name'].isin(compare_select)]['Ticker'].tolist()
        
        chart_data = etf_prices[sel_tickers].dropna()
        if not chart_data.empty:
            norm_chart = chart_data / chart_data.iloc[0] * 100
            st.line_chart(norm_chart)
            
    # Erklärung
    with st.expander("ℹ️ Erklärung der ETF-Signale"):
        st.write("""
        * **🚀 COMPOUNDER:** Stetiger Aufwärtstrend bei geringem Risiko (Vola < 15%).
        * **🔥 MOMENTUM:** Starker Anstieg, aber hohe Schwankung.
        * **❄️ COOLING:** Trend leicht gebrochen, abwarten.
        * **⚠️ DIP / CRASH:** Tief im Minus (>20% vom Hoch).
        """)
