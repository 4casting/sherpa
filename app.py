import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Aerospace Finance & Bilanzen", page_icon="✈️", layout="wide")

st.title("✈️ Luft- & Raumfahrt: Markt & Bilanzen")

# --- SIDEBAR ---
st.sidebar.header("⚙️ Konfiguration")

companies = {
    'Airbus SE': 'AIR.PA',
    'Boeing Co.': 'BA',
    'Lockheed Martin': 'LMT',
    'Northrop Grumman': 'NOC',
    'RTX Corp': 'RTX',
    'General Dynamics': 'GD',
    'MTU Aero Engines': 'MTX.DE',
    'Rheinmetall': 'RHM.DE',
    'Safran SA': 'SAF.PA'
}

selected_companies = st.sidebar.multiselect(
    "Unternehmen auswählen:",
    options=list(companies.keys()),
    default=['Airbus SE', 'Boeing Co.', 'Lockheed Martin']
)

start_date = st.sidebar.date_input("Startdatum", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("Enddatum", value=datetime.now())

selected_tickers = [companies[name] for name in selected_companies]

# --- DATEN LADEN (PREISE) ---
@st.cache_data
def load_price_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    data = yf.download(tickers, start=start, end=end)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()
        data.columns = tickers
    return data.dropna(how='all')

# --- DATEN LADEN (BILANZEN) ---
@st.cache_data
def load_balance_sheet(ticker_symbol):
    """Lädt die Jährliche Bilanz"""
    stock = yf.Ticker(ticker_symbol)
    return stock.balance_sheet

# --- HAUPTTEIL ---

if len(selected_tickers) > 0:
    
    # === 1. CHART & INDEX ===
    st.subheader("📈 Kursentwicklung (Normalisiert)")
    df = load_price_data(selected_tickers, start_date, end_date)
    
    if not df.empty:
        normalized_df = df / df.iloc[0]
        df['Portfolio_Index'] = normalized_df.mean(axis=1)
        
        plot_data = (normalized_df * 100) - 100
        plot_data['Durchschnitt'] = (df['Portfolio_Index'] * 100) - 100
        
        fig = go.Figure()
        for column in plot_data.columns:
            if column != 'Durchschnitt':
                fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data[column], mode='lines', name=column, opacity=0.5))
        
        fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['Durchschnitt'], mode='lines', name='DURCHSCHNITT', line=dict(color='white', width=4)))
        fig.update_layout(yaxis_title="Performance %", hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === 2. BILANZEN & FUNDAMENTALDATEN ===
    st.subheader("📚 Unternehmensbilanzen (Balance Sheets)")
    st.info("Hinweis: Die Daten zeigen die letzten verfügbaren Jahresabschlüsse. Beträge sind in der jeweiligen Landeswährung.")

    # Wir erstellen Tabs für jedes ausgewählte Unternehmen
    tabs = st.tabs(selected_companies)

    for i, company_name in enumerate(selected_companies):
        ticker = selected_tickers[i]
        
        with tabs[i]:
            # Spinner anzeigen, da das Laden der Bilanz 1-2 Sek dauern kann
            with st.spinner(f"Lade Bilanz für {company_name}..."):
                bs = load_balance_sheet(ticker)
            
            if not bs.empty:
                # --- Wichtige KPIs extrahieren (falls vorhanden) ---
                try:
                    # Hinweis: yfinance Labels sind auf Englisch
                    # Wir nutzen .get(), um Fehler zu vermeiden, falls Daten fehlen
                    total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else None
                    total_liab = bs.loc['Total Liabilities Net Minority Interest'].iloc[0] if 'Total Liabilities Net Minority Interest' in bs.index else None
                    equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else None
                    cash = bs.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in bs.index else None
                    
                    # Währungssymbol raten (nicht perfekt, aber hilfreich)
                    curr = "€" if ".PA" in ticker or ".DE" in ticker else "$"

                    # KPI Container
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    
                    if total_assets:
                        kpi_col1.metric("Gesamtvermögen (Assets)", f"{total_assets/1e9:.1f} Mrd. {curr}")
                    
                    if equity:
                        kpi_col2.metric("Eigenkapital", f"{equity/1e9:.1f} Mrd. {curr}")
                    
                    if cash:
                        kpi_col3.metric("Cash Bestand", f"{cash/1e9:.1f} Mrd. {curr}")

                    # Verschuldungsgrad (Debt-to-Equity)
                    if total_liab and equity and equity > 0:
                        de_ratio = total_liab / equity
                        kpi_col4.metric("Verschuldungsgrad (D/E)", f"{de_ratio:.2f}")
                    
                    st.divider()
                    
                except Exception as e:
                    st.warning(f"Konnte Schnell-Analyse nicht erstellen: {e}")

                # --- Die volle Bilanz Tabelle ---
                st.write("**Detaillierte Bilanz (Jahreswerte):**")
                # Transponieren (.T), damit Jahre oben stehen und Kategorien links
                st.dataframe(bs, height=400, use_container_width=True)
                
            else:
                st.error("Keine Bilanzdaten verfügbar.")

else:
    st.info("Bitte wähle Unternehmen in der Sidebar aus.")
