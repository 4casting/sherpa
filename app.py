import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- 1. SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Radar", page_icon="📡", layout="wide")
st.title("📡 Global Market Radar: Porter & Psychologie Simulator")

# --- 2. DATEN DEFINITIONEN ---
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

# --- 3. ANALYSE LOGIK (SCORES) ---

def calculate_porter_score(info):
    """Strategische Stärke (0-10)"""
    score = 0
    # 1. Pricing Power (Gross Margin)
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
    
    # 4. Finanzielle Stärke (Schulden)
    de = info.get('debtToEquity', 100)
    if de and de < 80: score += 2
    
    return max(0, min(10, score))

def calculate_psychology_score(price_series, info=None, asset_type="Stock"):
    """Marktstimmung & Trendstärke (0-10)"""
    score = 0
    if len(price_series) < 200: return 5 # Neutral bei fehlenden Daten
    
    current = price_series.iloc[-1]
    sma200 = price_series.rolling(200).mean().iloc[-1]
    sma50 = price_series.rolling(50).mean().iloc[-1]
    
    # 1. Langfristiger Trend (Rationaler Aufwärtstrend)
    if current > sma200: score += 4
    
    # 2. Mittelfristiges Momentum (Behavioral)
    if current > sma50: score += 3
    
    # 3. Stabilität / Angst-Faktor
    if asset_type == "Stock" and info:
        beta = info.get('beta', 1.0)
        if beta and beta < 1.2: score += 3 # Weniger volatil als der Markt
    else:
        # Bei ETFs nutzen wir Vola als Stabilitätsfaktor
        vola = price_series.pct_change().tail(30).std() * (252**0.5)
        if vola < 0.20: score += 3
        
    return max(0, min(10, score))

def get_combined_signal(porter, psych):
    # Logik-Matrix
    if porter >= 7 and psych >= 7: return "🚀 SWEET SPOT", "Top Qualität + Trend"
    if porter >= 7 and psych <= 4: return "💎 VALUE CHANCE", "Qualität wird abgestraft"
    if porter <= 4 and psych >= 7: return "⚠️ JUNK RALLY", "Hype ohne Substanz"
    if psych <= 3: return "❄️ BEAR MARKET", "Negatives Sentiment"
    return "⚪ Neutral", "Beobachten"

def calculate_simulation(price_series, start_date, invest_amount):
    if price_series.empty: return 0, 0
    subset = price_series[price_series.index >= pd.to_datetime(start_date)]
    if subset.empty: return 0, 0
    
    start_price = subset.iloc[0]
    current_price = price_series.iloc[-1]
    
    shares = invest_amount / start_price
    current_value = shares * current_price
    profit = current_value - invest_amount
    return current_value, profit

# --- 4. DATA LOADER ---

@st.cache_data
def load_market_data(mode_string):
    """
    Lädt Daten basierend auf dem Modus-String.
    ACHTUNG: mode_string enthält Emojis (z.B. "🏢 Aktien"), daher nutzen wir 'in'.
    """
    all_tickers = []
    t_map = {}
    
    # KORREKTUR: Prüfe auf Enthaltensein des Strings
    if "Aktien" in mode_string:
        sectors = STOCK_SECTORS
    else:
        sectors = ETF_SECTORS
    
    for sec, comps in sectors.items():
        for n, t in comps.items():
            all_tickers.append(t)
            t_map[t] = {'name': n, 'sector': sec}
            
    prices = yf.download(all_tickers, period="5y", progress=False)['Close']
    return prices, t_map

# --- 5. GUI & INPUTS ---

st.sidebar.header("🔍 Modus")
mode = st.sidebar.radio("Ansicht wählen:", ["🏢 Aktien", "🌐 ETFs"])

st.sidebar.markdown("---")
st.sidebar.header("💰 Simulator")
sim_start_date = st.sidebar.date_input("Startdatum:", value=datetime.now() - timedelta(days=365))
sim_amount = st.sidebar.number_input("Invest (€):", value=1000, step=100)

# --- 6. BERECHNUNG ---

# Daten laden
prices, ticker_map = load_market_data(mode)
results = []
is_stock_mode = "Aktien" in mode

with st.spinner(f"Berechne Daten für {mode}..."):
    for ticker in ticker_map.keys():
        try:
            if ticker not in prices.columns: continue
            series = prices[ticker].dropna()
            if series.empty: continue
            
            # Simulation
            curr_val, profit = calculate_simulation(series, sim_start_date, sim_amount)
            
            # Scores berechnen
            porter_score = 0
            psych_score = 0
            
            if is_stock_mode:
                # Aktien Logik: Info laden für Porter
                try:
                    info = yf.Ticker(ticker).info
                    porter_score = calculate_porter_score(info)
                    psych_score = calculate_psychology_score(series, info, "Stock")
                except:
                    # Fallback
                    psych_score = calculate_psychology_score(series, None, "Stock")
            else:
                # ETF Logik: Kein klassischer Porter, wir nutzen Vola-Stabilität
                # Wir 'simulieren' Porter als Stabilitäts-Metrik für die Matrix
                vola = series.pct_change().tail(30).std() * (252**0.5)
                porter_score = max(0, min(10, int(10 - vola*20))) 
                psych_score = calculate_psychology_score(series, None, "ETF")
            
            sig_title, sig_desc = get_combined_signal(porter_score, psych_score)
            
            results.append({
                "Unternehmen": ticker_map[ticker]['name'],
                "Ticker": ticker,
                "Sektor": ticker_map[ticker]['sector'],
                "Wert heute": curr_val,
                "Gewinn": profit,
                "Porter Score": porter_score,
                "Psycho Score": psych_score,
                "Signal": sig_title
            })
        except: continue

df = pd.DataFrame(results)

# --- 7. ANZEIGE ---

st.markdown(f"### {mode}-Simulator & Analyse")

# Top KPI
if not df.empty:
    best = df.loc[df['Gewinn'].idxmax()]
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Bester Invest", f"{best['Unternehmen']} ({best['Ticker']})", f"+{best['Gewinn']:.2f} €")
    c2.metric("Ø Portfolio Wert", f"{df['Wert heute'].mean():.2f} €", f"{df['Gewinn'].mean():.2f} €")
    
    # Zähle Signale
    sweet_spots = len(df[df['Signal'].str.contains("SWEET")])
    c3.metric("🚀 Sweet Spots (Score 7+)", sweet_spots, "Hohe Scores")

st.divider()

# TABELLE
def color_signal(val):
    if 'SWEET' in val: return 'background-color: #1f77b4; color: white' # Blau
    if 'VALUE' in val: return 'background-color: #2ca02c; color: white' # Grün
    if 'JUNK' in val: return 'background-color: #d62728; color: white'  # Rot
    return ''

# Spalten Konfiguration
col_config = {
    "Ticker": st.column_config.TextColumn("Symbol", width="small"),
    "Wert heute": st.column_config.NumberColumn("Wert", format="%.2f €"),
    "Gewinn": st.column_config.NumberColumn("G/V", format="%.2f €"),
    "Psycho Score": st.column_config.ProgressColumn("Psycho (Trend)", min_value=0, max_value=10, format="%d"),
}

# Dynamische Spalten-Namen je nach Modus
if is_stock_mode:
    col_config["Porter Score"] = st.column_config.ProgressColumn("Porter (Qualität)", min_value=0, max_value=10, format="%d", help="Fundamentale Stärke")
else:
    col_config["Porter Score"] = st.column_config.ProgressColumn("Stabilität (Risiko)", min_value=0, max_value=10, format="%d", help="Niedrige Volatilität = Hoher Score")

# Spalten Reihenfolge
cols = ['Unternehmen', 'Ticker', 'Signal', 'Wert heute', 'Gewinn', 'Porter Score', 'Psycho Score', 'Sektor']

st.dataframe(
    df[cols].style.applymap(color_signal, subset=['Signal']),
    column_config=col_config,
    use_container_width=True,
    height=700,
    hide_index=True
)

# CHART
st.divider()
st.subheader("Simulations-Verlauf")
sel = st.multiselect("Vergleich:", df['Unternehmen'].unique(), default=df['Unternehmen'].head(3).tolist())
if sel:
    ts = df[df['Unternehmen'].isin(sel)]['Ticker'].tolist()
    # Chart bauen
    cd = prices[ts].copy()
    cd = cd[cd.index >= pd.to_datetime(sim_start_date)]
    if not cd.empty:
        # Rebase auf Invest
        st.line_chart((cd / cd.iloc[0]) * sim_amount)
        st.caption("Verlauf des investierten Kapitals über die Zeit.")
