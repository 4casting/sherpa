import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(
    page_title="Aerospace & Defense Finance Dashboard",
    page_icon="✈️",
    layout="wide"
)

# --- TITEL & HEADER ---
st.title("✈️ Luft- & Raumfahrt Finanz-Tracker")
st.markdown("""
Dieses Dashboard zeigt **Echtzeit-Finanzdaten** (verzögert) und historische Entwicklungen 
führender Unternehmen der Luft- und Raumfahrtindustrie.
""")
st.markdown("---")

# --- SIDEBAR EINSTELLUNGEN ---
st.sidebar.header("⚙️ Einstellungen")

# Liste bekannter Unternehmen (Ticker Symbole)
# AIR.PA = Airbus (Paris), BA = Boeing, LMT = Lockheed Martin, etc.
companies = {
    'Airbus SE': 'AIR.PA',
    'Boeing Co.': 'BA',
    'Lockheed Martin': 'LMT',
    'Northrop Grumman': 'NOC',
    'RTX Corp (Raytheon)': 'RTX',
    'General Dynamics': 'GD',
    'MTU Aero Engines': 'MTX.DE',
    'Rheinmetall': 'RHM.DE'
}

selected_companies = st.sidebar.multiselect(
    "Unternehmen auswählen:",
    options=list(companies.keys()),
    default=['Airbus SE', 'Boeing Co.', 'Lockheed Martin']
)

# Zeitraum Auswahl
start_date = st.sidebar.date_input(
    "Startdatum",
    value=datetime.now() - timedelta(days=365)
)
end_date = st.sidebar.date_input(
    "Enddatum",
    value=datetime.now()
)

# --- DATEN ABRUFEN (CACHED) ---
@st.cache_data
def load_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    # yfinance download
    data = yf.download(tickers, start=start, end=end)['Close']
    return data

@st.cache_data
def get_company_info(ticker):
    try:
        tick = yf.Ticker(ticker)
        return tick.info
    except:
        return None

# Mapping der Namen zu Ticker-Symbolen für die Auswahl
selected_tickers = [companies[name] for name in selected_companies]

if len(selected_tickers) > 0:
    # --- 1. AKTIENKURS ENTWICKLUNG (CHART) ---
    st.subheader("📈 Aktienkurs-Entwicklung (Schlusskurse)")
    
    df = load_data(selected_tickers, start_date, end_date)
    
    if not df.empty:
        # Plotly Chart erstellen
        fig = px.line(df, x=df.index, y=df.columns, title='Vergleich der Aktienkurse')
        fig.update_layout(xaxis_title="Datum", yaxis_title="Preis (Währung der Börse)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Keine Daten gefunden.")

    # --- 2. FUNDAMENTALDATEN VERGLEICH ---
    st.subheader("📊 Fundamentale Kennzahlen")
    
    # Container für Metriken erstellen
    cols = st.columns(len(selected_tickers))
    
    metrics_data = []

    for idx, ticker in enumerate(selected_tickers):
        info = get_company_info(ticker)
        if info:
            # Wichtige Kennzahlen extrahieren
            name = selected_companies[idx]
            price = info.get('currentPrice', 'N/A')
            currency = info.get('currency', '')
            pe_ratio = info.get('trailingPE', 'N/A') # Kurs-Gewinn-Verhältnis
            market_cap = info.get('marketCap', 0)
            
            # Marktkapitalisierung formatieren (in Milliarden)
            if isinstance(market_cap, (int, float)):
                market_cap_fmt = f"{market_cap / 1e9:.2f} Mrd."
            else:
                market_cap_fmt = "N/A"

            # Karte erstellen
            with cols[idx % len(cols)]:
                st.metric(label=name, value=f"{price} {currency}")
                st.markdown(f"**Marktkap.:** {market_cap_fmt}")
                st.markdown(f"**KGV (P/E):** {pe_ratio}")
                
            metrics_data.append({
                "Unternehmen": name,
                "Preis": price,
                "Währung": currency,
                "KGV": pe_ratio,
                "Marktkapitalisierung": market_cap
            })

    # --- 3. TABELLARISCHE ÜBERSICHT ---
    with st.expander("Detaillierte Rohdaten ansehen"):
        st.dataframe(df.sort_index(ascending=False))

else:
    st.info("Bitte wählen Sie mindestens ein Unternehmen in der Sidebar aus.")

# --- FOOTER ---
st.markdown("---")
st.caption("Datenquelle: Yahoo Finance via yfinance API. Keine Anlageberatung.")
