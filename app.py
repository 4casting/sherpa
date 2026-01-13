import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Aerospace Finance & Bilanzen", page_icon="✈️", layout="wide")
st.title("✈️ Luft- & Raumfahrt: Markt & Bilanzen")

# --- HILFSFUNKTION FÜR ZAHLENFORMATIERUNG ---
def format_currency_value(value, currency_symbol="$"):
    """Wandelt große Zahlen in lesbare Strings um (Mio / Mrd)."""
    if value is None or pd.isna(value):
        return "-"
    
    # Absolutwert für die Größenbestimmung
    abs_val = abs(value)
    
    if abs_val >= 1e9: # Milliarden
        return f"{value / 1e9:.2f} Mrd. {currency_symbol}"
    elif abs_val >= 1e6: # Millionen
        return f"{value / 1e6:.2f} Mio. {currency_symbol}"
    elif abs_val >= 1e3: # Tausend
        return f"{value / 1e3:.2f} Tsd. {currency_symbol}"
    else:
        return f"{value:.2f} {currency_symbol}"

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
    st.subheader("📚 Unternehmensbilanzen (Formatiert)")
    
    tabs = st.tabs(selected_companies)

    for i, company_name in enumerate(selected_companies):
        ticker = selected_tickers[i]
        
        with tabs[i]:
            with st.spinner(f"Lade Bilanz für {company_name}..."):
                bs = load_balance_sheet(ticker)
            
            if not bs.empty:
                # Währungssymbol bestimmen
                currency_symbol = "€" if ".PA" in ticker or ".DE" in ticker else "$"
                
                # --- DATEN AUFBEREITEN FÜR ANZEIGE ---
                # 1. Kopie erstellen, damit wir Strings formatieren können
                display_df = bs.copy()
                
                # 2. Spaltennamen (Datum) verschönern: Nur das Jahr anzeigen
                # yfinance liefert oft Timestamp('2023-12-31 00:00:00') -> wir wollen "2023"
                new_columns = []
                for date_col in display_df.columns:
                    try:
                        new_columns.append(pd.to_datetime(date_col).year)
                    except:
                        new_columns.append(str(date_col))
                display_df.columns = new_columns

                # 3. Formatierung auf alle Zellen anwenden
                # Wir nutzen .applymap (oder .map in neueren Pandas Versionen), um die Funktion auf jede Zelle anzuwenden
                display_df = display_df.applymap(lambda x: format_currency_value(x, currency_symbol))

                # 4. KPI Berechnung (auf den Original-Zahlen 'bs', nicht auf den Strings!)
                try:
                    total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
                    equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else 0
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Gesamtvermögen", format_currency_value(total_assets, currency_symbol))
                    col2.metric("Eigenkapital", format_currency_value(equity, currency_symbol))
                    
                    if equity > 0:
                        debt_ratio = (bs.loc['Total Liabilities Net Minority Interest'].iloc[0] / equity)
                        col3.metric("Verschuldungsgrad (D/E)", f"{debt_ratio:.2f}")
                except:
                    st.caption("Schnell-KPIs nicht vollständig verfügbar.")

                st.divider()
                
                # 5. Anzeige der Tabelle
                st.markdown(f"**Detaillierte Bilanz für {company_name} (in {currency_symbol})**")
                st.dataframe(display_df, use_container_width=True, height=500)
                
            else:
                st.error("Keine Bilanzdaten verfügbar.")

else:
    st.info("Bitte wähle Unternehmen in der Sidebar aus.")
