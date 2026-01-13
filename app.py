import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Strategic Market Radar", page_icon="🧠", layout="wide")
st.title("🧠 Strategic Market Radar: Porter & Rationale Erwartungen")
st.markdown("""
Dieses Tool analysiert über **80 Top-Unternehmen** durch die Brille von:
1.  **Michael E. Porter:** Wettbewerbsvorteile, Burggräben (Moats) und Preissetzungsmacht.
2.  **Martin Bischof / Rationale Erwartungen:** Marktpsychologie, Momentum und rationale Bewertung.
""")

# --- DATEN DEFINITIONEN (ALLE UNTERNEHMEN) ---
SECTORS = {
    "✈️ Luft- & Raumfahrt (Defense)": {
        'Airbus SE': 'AIR.PA', 'Boeing Co.': 'BA', 'Lockheed Martin': 'LMT',
        'Northrop Grumman': 'NOC', 'Rheinmetall': 'RHM.DE', 'Safran SA': 'SAF.PA',
        'L3Harris': 'LHX', 'General Dynamics': 'GD', 'Thales': 'HO.PA',
        'Leonardo': 'LDO.MI', 'MTU Aero Engines': 'MTX.DE', 'Dassault Aviation': 'AM.PA',
        'Hensoldt': 'HAG.DE', 'Textron': 'TXT', 'Rolls-Royce': 'RR.L'
    },
    "🤖 KI & Halbleiter": {
        'Nvidia': 'NVDA', 'TSMC': 'TSM', 'ASML Holding': 'ASML',
        'AMD': 'AMD', 'Intel': 'INTC', 'Broadcom': 'AVGO',
        'Qualcomm': 'QCOM', 'Texas Instruments': 'TXN', 'Micron': 'MU',
        'Applied Materials': 'AMAT', 'Lam Research': 'LRCX', 'Infineon': 'IFX.DE',
        'Arm Holdings': 'ARM', 'Super Micro': 'SMCI'
    },
    "☁️ Big Tech & Software": {
        'Microsoft': 'MSFT', 'Apple': 'AAPL', 'Alphabet': 'GOOGL',
        'Amazon': 'AMZN', 'Meta Platforms': 'META', 'Salesforce': 'CRM',
        'Oracle': 'ORCL', 'Adobe': 'ADBE', 'SAP SE': 'SAP',
        'ServiceNow': 'NOW', 'Palo Alto Networks': 'PANW', 'Palantir': 'PLTR',
        'CrowdStrike': 'CRWD', 'Uber': 'UBER'
    },
    "🧬 Healthcare & Langlebigkeit": {
        'Novo Nordisk': 'NVO', 'Eli Lilly': 'LLY', 'Intuitive Surgical': 'ISRG',
        'Vertex Pharma': 'VRTX', 'Pfizer': 'PFE', 'Moderna': 'MRNA',
        'Johnson & Johnson': 'JNJ', 'AbbVie': 'ABBV', 'Merck & Co.': 'MRK',
        'Amgen': 'AMGN', 'Stryker': 'SYK', 'Thermo Fisher': 'TMO',
        'Boston Scientific': 'BSX', 'Sanofi': 'SAN.PA'
    },
    "⚡ GreenTech & Energie": {
        'Siemens Energy': 'ENR.DE', 'NextEra Energy': 'NEE', 'Schneider Electric': 'SU.PA',
        'First Solar': 'FSLR', 'Vestas Wind': 'VWS.CO', 'Enphase Energy': 'ENPH',
        'Orsted': 'ORSTED.CO', 'Iberdrola': 'IBE.MC', 'Enel': 'ENEL.MI',
        'SolarEdge': 'SEDG', 'Brookfield Renew.': 'BEP', 'Plug Power': 'PLUG',
        'RWE AG': 'RWE.DE'
    },
    "🚗 E-Mobilität & Auto": {
        'Tesla': 'TSLA', 'BYD Co.': 'BYDDF', 'Volkswagen Vz.': 'VOW3.DE',
        'BMW': 'BMW.DE', 'Mercedes-Benz': 'MBG.DE', 'Stellantis': 'STLA',
        'Rivian': 'RIVN', 'NIO': 'NIO', 'Toyota Motor': 'TM', 
        'Ferrari': 'RACE', 'Porsche AG': 'P911.DE', 'Ford': 'F', 'GM': 'GM'
    },
    "🌏 Emerging Markets & Konsum": {
        'MercadoLibre': 'MELI', 'HDFC Bank': 'HDB', 'LVMH': 'MC.PA',
        'Alibaba': 'BABA', 'Sea Limited': 'SE', 'Tencent': 'TCEHY',
        'JD.com': 'JD', 'Infosys': 'INFY', 'ICICI Bank': 'IBN',
        'Petrobras': 'PBR', 'Hermès': 'RMS.PA', 'Nu Holdings': 'NU'
    },
    "💰 Finanzen & Fintech": {
        'JPMorgan Chase': 'JPM', 'Visa': 'V', 'Mastercard': 'MA',
        'BlackRock': 'BLK', 'Goldman Sachs': 'GS', 'Morgan Stanley': 'MS',
        'PayPal': 'PYPL', 'Block': 'SQ', 'Allianz SE': 'ALV.DE',
        'Munich Re': 'MUV2.DE', 'Berkshire Hathaway': 'BRK-B'
    }
}

# --- ANALYSE LOGIK (PORTER & BISCHOF) ---

def calculate_porter_score(info):
    """
    Berechnet einen Score (0-10) für Wettbewerbsvorteile (Moat).
    """
    score = 0
    reasons = []
    
    # 1. Differenzierung (Gross Margin)
    gross_margin = info.get('grossMargins', 0)
    if gross_margin and gross_margin > 0.50: 
        score += 3
        reasons.append("💎 Extrem hohe Pricing Power (Gross Margin > 50%)")
    elif gross_margin and gross_margin > 0.30: 
        score += 2
        reasons.append("✅ Gute Differenzierung (Gross Margin > 30%)")
    elif gross_margin and gross_margin < 0.10:
        score -= 1
        reasons.append("⚠️ Preiskampf-Gefahr (Niedrige Marge)")

    # 2. Eintrittsbarrieren (ROE)
    roe = info.get('returnOnEquity', 0)
    if roe and roe > 0.20: 
        score += 3
        reasons.append("🏰 Hohe Eintrittsbarrieren (ROE > 20%)")
    elif roe and roe > 0.12: 
        score += 1
    
    # 3. Operative Effizienz
    op_margin = info.get('operatingMargins', 0)
    if op_margin and op_margin > 0.15: 
        score += 2
        reasons.append("⚙️ Effiziente Operations (Op. Margin > 15%)")
    
    # 4. Verschuldung (Resilienz)
    debt_equity = info.get('debtToEquity', 100)
    if debt_equity and debt_equity < 80: # YFinance gibt D/E oft als Zahl um die 100 an (0.8 -> 80)
        score += 2
        reasons.append("🛡️ Finanzielle Stärke (Geringe Schulden)")
    
    final_score = min(max(score, 0), 10) # Clamp zwischen 0 und 10
    return final_score, reasons

def analyze_market_psychology(info, price_series):
    """
    Analysiert Marktphasen basierend auf Rationale Erwartungen (Trend & Bewertung).
    """
    # 1. Momentum / Trend (Verhalten)
    if len(price_series) > 200:
        sma200 = price_series.rolling(200).mean().iloc[-1]
        current_price = price_series.iloc[-1]
        
        if current_price > sma200:
            trend = "📈 Bullish (Rationaler Aufwärtstrend)"
            trend_color = "green"
        else:
            trend = "📉 Bearish (Preis unter 200-Tage-Linie)"
            trend_color = "red"
    else:
        trend = "⚪ Keine Trend-Daten"
        trend_color = "gray"

    # 2. Erwartungshaltung (PEG Ratio)
    peg = info.get('pegRatio')
    if peg is None:
        valuation = "⚪ Keine Daten"
    elif peg < 1.0:
        valuation = "🟢 Unterbewertet (Pessimismus eingepreist)"
    elif 1.0 <= peg <= 2.5:
        valuation = "🟡 Rationale Bewertung (Fair)"
    else:
        valuation = "🔴 Überhitzt / Hype (Hohe Erwartungen)"
        
    return trend, trend_color, valuation

# --- SIDEBAR ---
st.sidebar.header("⚙️ Konfiguration")

selected_sector_name = st.sidebar.selectbox("Branche wählen:", list(SECTORS.keys()))
sector_companies = SECTORS[selected_sector_name]

# Standard: Erste 4 Unternehmen vorselektieren
selected_companies_list = st.sidebar.multiselect(
    "Unternehmen analysieren:",
    options=list(sector_companies.keys()),
    default=list(sector_companies.keys())[:4]
)

start_date = st.sidebar.date_input("Startdatum", value=datetime.now() - timedelta(days=400)) # 400 Tage für SMA200
end_date = st.sidebar.date_input("Enddatum", value=datetime.now())

selected_tickers = [sector_companies[name] for name in selected_companies_list]

# --- HAUPTTEIL ---

if len(selected_tickers) > 0:
    
    # 1. Batch Download Preise
    with st.spinner("Lade Marktdaten..."):
        price_data = yf.download(selected_tickers, start=start_date, end=end_date)['Close']
        if isinstance(price_data, pd.Series):
            price_data = price_data.to_frame()
            price_data.columns = selected_tickers
            
    # --- TABS FÜR DIE ANALYSE-EBENEN ---
    tab_strategy, tab_psychology, tab_raw = st.tabs([
        "🛡️ Porter-Strategie (Qualität)", 
        "🧠 Markt-Psychologie (Trend)", 
        "📊 Rohdaten"
    ])

    # === TAB 1: PORTER ANALYSE ===
    with tab_strategy:
        st.subheader("Wettbewerbsstärke & Moat-Analyse")
        st.caption("Ein hoher Score (8-10) deutet auf ein Unternehmen hin, das schwer angreifbar ist (Strong Moat).")
        st.divider()
        
        cols = st.columns(len(selected_companies_list))
        
        for i, company in enumerate(selected_companies_list):
            ticker = selected_tickers[i]
            
            with cols[i]:
                # Daten laden (einzeln für Details)
                try:
                    info = yf.Ticker(ticker).info
                    score, reasons = calculate_porter_score(info)
                    
                    # Score Visualisierung
                    color = "#2ca02c" if score >= 7 else "#ff7f0e" if score >= 4 else "#d62728"
                    st.markdown(f"<h3 style='text-align: center;'>{company}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<h1 style='color:{color}; text-align: center; font-size: 60px; margin:0;'>{score}<span style='font-size:30px;'>/10</span></h1>", unsafe_allow_html=True)
                    
                    with st.expander("Details zum Score"):
                        for r in reasons:
                            st.write(r)
                            
                    # Key Porter Metrics
                    st.markdown("---")
                    gm = info.get('grossMargins')
                    roe = info.get('returnOnEquity')
                    st.metric("Bruttomarge (Pricing)", f"{gm:.1%}" if gm else "N/A")
                    st.metric("ROE (Barriere)", f"{roe:.1%}" if roe else "N/A")
                    
                except Exception as e:
                    st.error(f"Datenfehler: {e}")

    # === TAB 2: MARKT PSYCHOLOGIE ===
    with tab_psychology:
        st.subheader("Marktphasen & Rationale Erwartungen")
        st.caption("Vergleich von Chart-Trends (Momentum) und fundamentaler Bewertung (PEG).")
        
        # Chart für alle
        if not price_data.empty:
            norm_df = price_data / price_data.iloc[0] * 100
            st.line_chart(norm_df)
            
        st.divider()
        
        p_cols = st.columns(len(selected_companies_list))
        
        for i, company in enumerate(selected_companies_list):
            ticker = selected_tickers[i]
            
            with p_cols[i]:
                try:
                    # Wir nutzen hier Ticker objekt erneut, in Prod könnte man Cachen
                    info = yf.Ticker(ticker).info
                    # Preisreihe für dieses Unternehmen
                    series = price_data[ticker].dropna()
                    
                    trend_txt, trend_col, val_txt = analyze_market_psychology(info, series)
                    
                    st.markdown(f"**{company}**")
                    st.markdown(f"<div style='color: {trend_col}; font-weight: bold;'>{trend_txt}</div>", unsafe_allow_html=True)
                    st.markdown(f"Bewertung: {val_txt}")
                    
                    beta = info.get('beta')
                    st.metric("Beta (Risiko)", f"{beta:.2f}" if beta else "-")
                    
                except:
                    st.caption("Keine Psychologie-Daten")

    # === TAB 3: ROHDATEN ===
    with tab_raw:
        st.dataframe(price_data.sort_index(ascending=False), use_container_width=True)

else:
    st.info("Bitte Unternehmen auswählen.")
