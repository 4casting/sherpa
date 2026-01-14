import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Radar", page_icon="📡", layout="wide")
st.title("📡 Global Market Radar: Analyse & Simulator")

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

# --- 3. ANALYSE & SIMULATION LOGIK ---

def calculate_porter_score(info):
    score = 0
    gm = info.get('grossMargins', 0)
    if gm and gm > 0.50: score += 3
    elif gm and gm > 0.30: score += 2
    elif gm and gm < 0.10: score -= 1
    
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0.20: score += 3
    elif roe and roe > 0.12: score += 1
    
    om = info.get('operatingMargins', 0)
    if om and om > 0.15: score += 2
    
    de = info.get('debtToEquity', 100)
    if de and de < 80: score += 2
    return max(0, min(10, score))

def get_trend_signal(price_series):
    if len(price_series) < 200: return "Neutral"
    sma200 = price_series.rolling(200).mean().iloc[-1]
    return "Bullish" if price_series.iloc[-1] > sma200 else "Bearish"

def get_strategy_signal(porter_score, trend):
    if porter_score >= 8 and trend == "Bullish": return "🚀 SWEET SPOT", "Qualität wird erkannt"
    elif porter_score >= 7 and trend == "Bearish": return "💎 VALUE CHANCE", "Qualität irrational abgestraft"
    elif porter_score <= 4 and trend == "Bullish": return "⚠️ JUNK RALLY", "Hype ohne Qualität"
    else: return "⚪ Neutral", "Beobachten"

def calculate_simulation(ticker, price_series, start_date, invest_amount):
    """Berechnet den heutigen Wert eines Investments."""
    if price_series.empty: return 0, 0
    
    # Finde den nächstgelegenen Preis zum Startdatum
    # Wir nehmen den ersten Preis, der >= start_date ist
    subset = price_series[price_series.index >= pd.to_datetime(start_date)]
    
    if subset.empty:
        return 0, 0 # Daten reichen nicht so weit zurück
        
    start_price = subset.iloc[0]
    current_price = price_series.iloc[-1]
    
    shares = invest_amount / start_price
    current_value = shares * current_price
    profit = current_value - invest_amount
    
    return current_value, profit

# --- 4. DATA LOADER ---

@st.cache_data
def load_market_data(mode_type):
    """Lädt Daten für Aktien oder ETFs für 5 Jahre (für Simulation)."""
    all_tickers = []
    t_map = {}
    
    sectors = STOCK_SECTORS if mode_type == "Aktien" else ETF_SECTORS
    
    for sec, comps in sectors.items():
        for n, t in comps.items():
            all_tickers.append(t)
            t_map[t] = {'name': n, 'sector': sec}
            
    # Wir laden 5 Jahre History für die Simulation
    prices = yf.download(all_tickers, period="5y", progress=False)['Close']
    
    # Helper DataFrame
    return prices, t_map

# --- 5. HAUPTNAVIGATION & SIMULATOR INPUTS ---

st.sidebar.header("🔍 Modus")
mode = st.sidebar.radio("Ansicht wählen:", ["🏢 Aktien", "🌐 ETFs"])

st.sidebar.markdown("---")
st.sidebar.header("💰 Zeitmaschine (Simulator)")
st.sidebar.caption("Prüfe: Was wäre aus meinem Geld geworden?")

# Simulator Inputs
max_date = datetime.now() - timedelta(days=1)
min_date = datetime.now() - timedelta(days=365*5) # Max 5 Jahre zurück

sim_start_date = st.sidebar.date_input(
    "Startdatum Investment:",
    value=datetime.now() - timedelta(days=365), # Default: 1 Jahr
    min_value=min_date,
    max_value=max_date
)

sim_amount = st.sidebar.number_input(
    "Investierter Betrag (€):",
    min_value=100,
    max_value=3000,
    value=500,
    step=100
)

# --- 6. DATENVERARBEITUNG & TABELLEN ERSTELLUNG ---

# Daten laden
prices, ticker_map = load_market_data(mode)

# Analyse DataFrame bauen
results = []

# Spinner nur beim ersten Laden
with st.spinner(f"Analysiere {mode} & berechne Simulation..."):
    
    for ticker in ticker_map.keys():
        try:
            if ticker not in prices.columns: continue
            
            # Preisreihe bereinigen
            series = prices[ticker].dropna()
            if series.empty: continue
            
            # 1. Simulation berechnen
            curr_val, profit = calculate_simulation(ticker, series, sim_start_date, sim_amount)
            
            # Basis Daten
            row = {
                "Unternehmen": ticker_map[ticker]['name'],
                "Ticker": ticker,
                "Sektor": ticker_map[ticker]['sector'],
                "Kurs aktuell": series.iloc[-1],
                "Invest Start": sim_amount,
                "Wert heute": curr_val,
                "Gewinn/Verlust": profit
            }

            # 2. Spezifische Analyse je nach Modus
            if mode == "Aktien":
                # Porter & Trend
                # Info laden (Achtung: macht es langsamer, daher try/except)
                try:
                    info = yf.Ticker(ticker).info
                    score = calculate_porter_score(info)
                    trend = get_trend_signal(series)
                    sig, desc = get_strategy_signal(score, trend)
                    
                    row.update({
                        "Porter Score": score,
                        "Trend": trend,
                        "Signal": sig,
                        "KGV": info.get('trailingPE', 0),
                        "Marge": info.get('grossMargins', 0)
                    })
                except:
                    # Fallback falls Info failt
                    row.update({"Signal": "⚪ Neutral", "Porter Score": 0})

            else: # ETFs
                # Trend & Risiko Metriken
                sma200 = series.rolling(200).mean().iloc[-1]
                trend_dist = (series.iloc[-1] - sma200) / sma200
                vola = series.pct_change().tail(30).std() * (252**0.5)
                dd = (series.iloc[-1] - series.max()) / series.max()
                
                # Einfaches Signal für ETF
                sig = "⚪ Neutral"
                if trend_dist > 0.05: sig = "🚀 Up-Trend"
                elif trend_dist < -0.05: sig = "❄️ Down-Trend"
                
                row.update({
                    "Signal": sig,
                    "Trend %": trend_dist,
                    "Vola": vola,
                    "Drawdown": dd
                })
            
            results.append(row)
            
        except Exception as e:
            continue

df = pd.DataFrame(results)

# --- 7. ANZEIGE LOGIK ---

st.markdown(f"### {mode}-Simulator")
st.markdown(f"**Szenario:** Du hättest am **{sim_start_date.strftime('%d.%m.%Y')}** genau **{sim_amount} €** investiert.")

# KPI Cards Global
if not df.empty:
    best_perf = df.loc[df['Gewinn/Verlust'].idxmax()]
    worst_perf = df.loc[df['Gewinn/Verlust'].idxmin()]
    
    c1, c2, c3 = st.columns(3)
    c1.metric(
        label=f"🏆 Bester: {best_perf['Unternehmen']}",
        value=f"{best_perf['Wert heute']:.2f} €",
        delta=f"{best_perf['Gewinn/Verlust']:.2f} €"
    )
    c2.metric(
        label=f"📉 Schlechtester: {worst_perf['Unternehmen']}",
        value=f"{worst_perf['Wert heute']:.2f} €",
        delta=f"{worst_perf['Gewinn/Verlust']:.2f} €"
    )
    
    # Portfolio Durchschnitt
    avg_val = df['Wert heute'].mean()
    avg_prof = df['Gewinn/Verlust'].mean()
    c3.metric(
        label="Ø Durchschnitts-Portfolio",
        value=f"{avg_val:.2f} €",
        delta=f"{avg_prof:.2f} €"
    )

st.divider()

# --- TABELLE ---

def highlight_signal(val):
    if 'SWEET' in str(val) or 'Up-Trend' in str(val): return 'background-color: #1f77b4; color: white'
    if 'VALUE' in str(val): return 'background-color: #2ca02c; color: white'
    if 'JUNK' in str(val) or 'Down-Trend' in str(val): return 'background-color: #d62728; color: white'
    return ''

if mode == "Aktien":
    cols = ['Unternehmen', 'Ticker', 'Signal', 'Wert heute', 'Gewinn/Verlust', 'Porter Score', 'Trend', 'KGV', 'Sektor']
    
    st.dataframe(
        df[cols].style.applymap(highlight_signal, subset=['Signal']),
        column_config={
            "Ticker": st.column_config.TextColumn("Kürzel", width="small"),
            "Wert heute": st.column_config.NumberColumn("Wert heute", format="%.2f €"),
            "Gewinn/Verlust": st.column_config.NumberColumn("G/V", format="%.2f €"),
            "Porter Score": st.column_config.ProgressColumn("Porter Score", min_value=0, max_value=10, format="%d"),
            "KGV": st.column_config.NumberColumn("KGV", format="%.1f"),
        },
        use_container_width=True,
        hide_index=True,
        height=600
    )

else: # ETFs
    cols = ['Unternehmen', 'Ticker', 'Signal', 'Wert heute', 'Gewinn/Verlust', 'Trend %', 'Vola', 'Drawdown', 'Sektor']
    
    st.dataframe(
        df[cols].style.applymap(highlight_signal, subset=['Signal']),
        column_config={
            "Ticker": st.column_config.TextColumn("Kürzel", width="small"),
            "Wert heute": st.column_config.NumberColumn("Wert heute", format="%.2f €"),
            "Gewinn/Verlust": st.column_config.NumberColumn("G/V", format="%.2f €"),
            "Trend %": st.column_config.NumberColumn("Trend", format="%.1f%%"),
            "Vola": st.column_config.NumberColumn("Vola", format="%.1f%%"),
            "Drawdown": st.column_config.NumberColumn("Max DD", format="%.1f%%"),
        },
        use_container_width=True,
        hide_index=True,
        height=600
    )

# --- CHART BEREICH ---
st.divider()
st.subheader("📈 Historischer Verlauf (Simulation)")

# Auswahlbox
comp_select = st.multiselect(
    "Vergleiche Entwicklung im Simulator-Zeitraum:",
    df['Unternehmen'].unique(),
    default=df['Unternehmen'].head(3).tolist()
)

if comp_select:
    # Ticker holen
    sel_tickers = df[df['Unternehmen'].isin(comp_select)]['Ticker'].tolist()
    
    # Daten schneiden ab sim_start_date
    chart_data = prices[sel_tickers].copy()
    chart_data = chart_data[chart_data.index >= pd.to_datetime(sim_start_date)]
    
    if not chart_data.empty:
        # Rebase auf Start-Investment (500€ = 100%)
        # Formel: (Preis_t / Preis_0) * Investment
        sim_chart = (chart_data / chart_data.iloc[0]) * sim_amount
        st.line_chart(sim_chart)
        st.caption(f"Entwicklung des Startkapitals von {sim_amount} € über die Zeit.")
