import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Strategic Market Radar", page_icon="🧠", layout="wide")
st.title("🧠 Strategic Market Radar: Porter & Rationale Erwartungen")

# --- DATEN DEFINITIONEN (ALLE SEKTOREN) ---
SECTORS = {
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
        'Pfizer': 'PFE', 'Johnson & Johnson': 'JNJ', 'Merck': 'MRK'
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

# --- ANALYSE LOGIK ---

def calculate_porter_score(info):
    """Berechnet Score (0-10) basierend auf Wettbewerbsvorteilen."""
    score = 0
    # 1. Pricing Power (Gross Margin)
    gm = info.get('grossMargins', 0)
    if gm and gm > 0.50: score += 3
    elif gm and gm > 0.30: score += 2
    elif gm and gm < 0.10: score -= 1

    # 2. Barriers to Entry (ROE)
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

def get_trend_signal(price_series):
    """Bestimmt den Trend (Bullish/Bearish) anhand SMA200."""
    if len(price_series) < 200: return "Neutral"
    sma200 = price_series.rolling(200).mean().iloc[-1]
    current = price_series.iloc[-1]
    return "Bullish" if current > sma200 else "Bearish"

def get_special_indicator(porter_score, trend):
    """Die strategische Matrix-Logik."""
    if porter_score >= 8 and trend == "Bullish":
        return "🚀 SWEET SPOT", "Qualität wird erkannt (Momentum)"
    elif porter_score >= 7 and trend == "Bearish":
        return "💎 VALUE CHANCE", "Qualität irrational abgestraft?"
    elif porter_score <= 4 and trend == "Bullish":
        return "⚠️ JUNK RALLY", "Vorsicht: Hype bei schlechter Qualität"
    else:
        return "⚪ Neutral", "Beobachten"

# --- DATEN LADEN (BATCH) ---
@st.cache_data
def scan_whole_market():
    # 1. Alle Ticker sammeln
    all_tickers = []
    ticker_map = {}
    for sector, companies in SECTORS.items():
        for name, ticker in companies.items():
            all_tickers.append(ticker)
            ticker_map[ticker] = {'name': name, 'sector': sector}
            
    # 2. Preisdaten laden (Schnell via Batch)
    start = datetime.now() - timedelta(days=400)
    prices = yf.download(all_tickers, start=start, progress=False)['Close']
    
    # 3. Fundamentaldaten & Analyse (Schleife)
    results = []
    
    # Hinweis: Wir iterieren hier, da wir 'info' brauchen. 
    # Um es schnell zu halten, nutzen wir Ticker-Objekte.
    for ticker in all_tickers:
        try:
            # Info laden
            stock = yf.Ticker(ticker)
            info = stock.info # Das dauert am längsten
            
            # Analysen
            score = calculate_porter_score(info)
            
            # Trend prüfen
            if ticker in prices.columns:
                trend = get_trend_signal(prices[ticker].dropna())
            else:
                trend = "Neutral"
                
            # Spezial-Indikator
            signal_title, signal_desc = get_special_indicator(score, trend)
            
            # Daten für Tabelle
            results.append({
                "Unternehmen": ticker_map[ticker]['name'],
                "Sektor": ticker_map[ticker]['sector'],
                "Porter Score": score,
                "Trend (SMA200)": trend,
                "Strategie-Signal": signal_title,
                "Info": signal_desc,
                "KGV": info.get('trailingPE', 0),
                "Marge": info.get('grossMargins', 0)
            })
        except:
            continue
            
    return pd.DataFrame(results), prices

# --- UI STARTSEITE ---

st.markdown("""
### 🔍 Der Markt-Scanner (Gesamtüberblick)
Diese Tabelle filtert **alle Unternehmen** nach der Kombination aus **Qualität (Porter)** und **Marktpsychologie (Trend)**.
""")

# Spinner, da der erste Load 30-60sek dauern kann (wegen yfinance API Limits)
with st.spinner("Scanne den globalen Markt... (Dies dauert beim ersten Mal ca. 30 Sekunden)"):
    market_df, price_data = scan_whole_market()

# --- KPI KARTEN (ZUSAMMENFASSUNG) ---
col1, col2, col3 = st.columns(3)
sweet_spots = market_df[market_df['Strategie-Signal'].str.contains("SWEET")]
value_plays = market_df[market_df['Strategie-Signal'].str.contains("VALUE")]
junk_rallys = market_df[market_df['Strategie-Signal'].str.contains("JUNK")]

col1.metric("🚀 Sweet Spots", len(sweet_spots), "Kaufen & Laufen lassen")
col2.metric("💎 Value Chancen", len(value_plays), "Antizyklisch prüfen")
col3.metric("⚠️ Junk Rallys", len(junk_rallys), "Vorsicht geboten", delta_color="inverse")

# --- DIE GROSSE TABELLE ---
st.subheader("📋 Strategische Matrix")

# Styling Funktion für die Tabelle
def highlight_signal(val):
    color = ''
    if 'SWEET' in val: color = 'background-color: #1f77b4; color: white' # Blau
    elif 'VALUE' in val: color = 'background-color: #2ca02c; color: white' # Grün
    elif 'JUNK' in val: color = 'background-color: #d62728; color: white' # Rot
    return color

# DataFrame anzeigen
st.dataframe(
    market_df.style.applymap(highlight_signal, subset=['Strategie-Signal']),
    column_config={
        "Porter Score": st.column_config.ProgressColumn(
            "Porter Qualität",
            help="Score 0-10 basierend auf Margen, ROE & Bilanz",
            format="%d",
            min_value=0,
            max_value=10,
        ),
        "Marge": st.column_config.NumberColumn("Brutto-Marge", format="%.1f%%"),
        "KGV": st.column_config.NumberColumn("KGV", format="%.1f"),
    },
    use_container_width=True,
    height=500
)

st.divider()

# --- SEKTOR DETAILS (WIE VORHER) ---
st.subheader("📂 Sektor-Deep-Dive")
selected_sector = st.selectbox("Sektor für Detail-Chart wählen:", list(SECTORS.keys()))

# Chart Logik
if selected_sector:
    sector_tickers = list(SECTORS[selected_sector].values())
    # Filtern der Preisdaten
    valid_tickers = [t for t in sector_tickers if t in price_data.columns]
    
    if valid_tickers:
        subset = price_data[valid_tickers].dropna(how='all')
        # Rebase auf 100
        normalized = subset / subset.iloc[0] * 100
        
        st.line_chart(normalized)
        
        # Kleine Liste der Firmen im Sektor mit Score
        st.write("Werte im Sektor:")
        sector_df = market_df[market_df['Sektor'] == selected_sector][['Unternehmen', 'Porter Score', 'Strategie-Signal']]
        st.dataframe(sector_df, use_container_width=True)
