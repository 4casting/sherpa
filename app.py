import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Aerospace Index & Portfolio", page_icon="✈️", layout="wide")

st.title("✈️ Luft- & Raumfahrt: Aggregierte Performance")
st.markdown("Verfolgen Sie die Entwicklung eines **gleichgewichteten Portfolios** der gewählten Aktien.")

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
    "Unternehmen für den Index:",
    options=list(companies.keys()),
    default=['Airbus SE', 'Boeing Co.', 'Lockheed Martin', 'Rheinmetall']
)

start_date = st.sidebar.date_input("Startdatum", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("Enddatum", value=datetime.now())

# Mapping Namen -> Ticker
selected_tickers = [companies[name] for name in selected_companies]

# --- DATEN LADEN ---
@st.cache_data
def load_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    # 'Close' Preise laden
    data = yf.download(tickers, start=start, end=end)['Close']
    # Falls nur eine Spalte zurückkommt (bei 1 Aktie), sicherstellen dass es ein DataFrame bleibt
    if isinstance(data, pd.Series):
        data = data.to_frame()
        data.columns = tickers
    # Zeilen mit fehlenden Daten (NaN) am Anfang entfernen
    data = data.dropna(how='all')
    return data

if len(selected_tickers) > 0:
    df = load_data(selected_tickers, start_date, end_date)
    
    if not df.empty and len(df) > 1:
        
        # --- BERECHNUNG DER NORMALISIERTEN DATEN ---
        # Wir teilen jeden Preis durch den Preis am ersten Tag. 
        # Startwert ist immer 1.0 (also 0% Veränderung).
        normalized_df = df / df.iloc[0]
        
        # Berechnung des "Portfolios" (Durchschnitt aller normalisierten Kurse)
        # axis=1 bedeutet: Durchschnitt pro Tag über alle Spalten
        df['Portfolio_Index'] = normalized_df.mean(axis=1)
        
        # --- KENNZAHLEN BERECHNEN (AGGREGIERT) ---
        
        # 1. Gesamtrendite (Total Return)
        start_val = df['Portfolio_Index'].iloc[0]
        end_val = df['Portfolio_Index'].iloc[-1]
        total_return = (end_val - start_val) / start_val
        
        # 2. Volatilität (Risiko)
        # Standardabweichung der täglichen prozentualen Änderungen * Wurzel(252 Handelstage)
        daily_returns = df['Portfolio_Index'].pct_change()
        volatility = daily_returns.std() * (252 ** 0.5)
        
        # 3. Bester & Schlechtester Performer im Korb
        # Performance aller Einzelaktien berechnen
        perf_series = (normalized_df.iloc[-1] - 1)
        best_stock = perf_series.idxmax()
        worst_stock = perf_series.idxmin()
        
        # Umwandlung Ticker -> Name für Anzeige
        # (Umgekehrte Suche im Dictionary)
        def get_name(tick):
            for name, t in companies.items():
                if t == tick: return name
            return tick

        # --- METRIKEN ANZEIGEN ---
        st.subheader("📊 Portfolio Kennzahlen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Gesamtrendite (Zeitraum)", f"{total_return:.2%}", delta_color="normal")
        with col2:
            st.metric("Volatilität (Risiko p.a.)", f"{volatility:.2%}")
        with col3:
            st.metric("Top Performer", get_name(best_stock), f"{perf_series.max():.2%}")
        with col4:
            st.metric("Low Performer", get_name(worst_stock), f"{perf_series.min():.2%}")

        st.markdown("---")

        # --- VISUALISIERUNG ---
        st.subheader("📈 Index-Entwicklung (Rebase auf 0%)")
        
        # Umrechnen in Prozent für den Chart (Start bei 0)
        plot_data = (normalized_df * 100) - 100
        plot_data['Durchschnitt (Index)'] = (df['Portfolio_Index'] * 100) - 100
        
        fig = go.Figure()

        # 1. Die einzelnen Aktien (dünn und halbtransparent)
        for column in plot_data.columns:
            if column != 'Durchschnitt (Index)':
                fig.add_trace(go.Scatter(
                    x=plot_data.index, 
                    y=plot_data[column], 
                    mode='lines', 
                    name=get_name(column),
                    opacity=0.4,  # Transparenz
                    line=dict(width=1)
                ))

        # 2. Der Portfolio-Durchschnitt (dick und hervorstechend)
        fig.add_trace(go.Scatter(
            x=plot_data.index, 
            y=plot_data['Durchschnitt (Index)'], 
            mode='lines', 
            name='PORTFOLIO DURCHSCHNITT',
            line=dict(color='white', width=4) # Weiß hebt sich im Darkmode gut ab
        ))

        fig.update_layout(
            yaxis_title="Performance in %",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with
