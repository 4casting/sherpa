import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Trends & Valuation", page_icon="🌍", layout="wide")
st.title("🌍 Global Market Trends & Valuation Tool")
st.markdown("Analyse von Wachstumsbranchen mit automatischer Bewertungs-Logik.")

# --- DATEN DEFINITIONEN (SEKTOREN & UNTERNEHMEN) ---
SECTORS = {
    "✈️ Luft- & Raumfahrt (Defense)": {
        'Airbus SE': 'AIR.PA',
        'Boeing Co.': 'BA',
        'Lockheed Martin': 'LMT',
        'Northrop Grumman': 'NOC',
        'Rheinmetall': 'RHM.DE',
        'Safran SA': 'SAF.PA'
    },
    "🧬 Healthcare & Langlebigkeit": {
        'Novo Nordisk (Adipositas)': 'NVO',
        'Eli Lilly (Pharma)': 'LLY',
        'Intuitive Surgical (Robotic)': 'ISRG',
        'Vertex Pharma (Biotech)': 'VRTX',
        'Pfizer': 'PFE',
        'Moderna': 'MRNA'
    },
    "⚡ GreenTech & Energie": {
        'Siemens Energy': 'ENR.DE',
        'NextEra Energy (Renewables)': 'NEE',
        'Schneider Electric': 'SU.PA',
        'First Solar': 'FSLR',
        'Vestas Wind Systems': 'VWS.CO',
        'Enphase Energy': 'ENPH'
    },
    "🌏 Emerging Markets & Konsum": {
        'MercadoLibre (LatAm Amazon)': 'MELI',
        'HDFC Bank (Indien)': 'HDB',
        'LVMH (Luxus)': 'MC.PA',
        'Alibaba (China)': 'BABA',
        'Sea Limited (Südostasien)': 'SE'
    }
}

# --- HILFSFUNKTIONEN ---

def format_currency_value(value, currency_symbol=""):
    """Formatiert große Zahlen (Mrd/Mio)."""
    if value is None or pd.isna(value):
        return "-"
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"{value / 1e9:.2f} Mrd. {currency_symbol}"
    elif abs_val >= 1e6:
        return f"{value / 1e6:.2f} Mio. {currency_symbol}"
    else:
        return f"{value:.2f} {currency_symbol}"

def analyze_valuation(info):
    """
    Erstellt ein Bewertungssignal basierend auf fundamentalen Daten.
    Logik: Kombination aus KGV (P/E), PEG-Ratio und Kurs-Buchwert (P/B).
    """
    pe_ratio = info.get('trailingPE')
    peg_ratio = info.get('pegRatio')
    pb_ratio = info.get('priceToBook')
    forward_pe = info.get('forwardPE')

    signal = "⚪ Keine Daten"
    color = "gray"
    reason = "Zu wenig Daten für eine Bewertung."

    # Bewertungs-Logik
    # 1. Unterbewertet (Value Chance)
    if (peg_ratio is not None and peg_ratio < 1.0) or \
       (pe_ratio is not None and pe_ratio < 15 and pb_ratio is not None and pb_ratio < 1.5):
        signal = "🟢 UNTERBEWERTET"
        color = "green"
        reason = "Niedriges KGV im Verhältnis zum Wachstum (PEG < 1) oder klassisches Value-Schnäppchen."
    
    # 2. Fair Bewertet (Growth at Reasonable Price)
    elif (peg_ratio is not None and 1.0 <= peg_ratio <= 2.0) or \
         (pe_ratio is not None and 15 <= pe_ratio <= 30):
        signal = "🟡 FAIR BEWERTET"
        color = "#FFD700" # Gold
        reason = "Bewertung entspricht den Wachstumsaussichten."

    # 3. Überbewertet / Teuer (High Growth Premium)
    elif (pe_ratio is not None and pe_ratio > 40) or (peg_ratio is not None and peg_ratio > 2.5):
        signal = "🔴 HOCH BEWERTET"
        color = "red"
        reason = "Hohes KGV oder teuer im Verhältnis zum Wachstum. Der Markt preist viel Optimismus ein."

    return {
        "signal": signal,
        "color": color,
        "reason": reason,
        "metrics": {
            "KGV (P/E)": pe_ratio,
            "PEG Ratio": peg_ratio,
            "KBV (P/B)": pb_ratio,
            "Forward P/E": forward_pe
        }
    }

# --- SIDEBAR KONFIGURATION ---
st.sidebar.header("⚙️ Konfiguration")

# 1. Sektor Auswahl
selected_sector_name = st.sidebar.selectbox("Branche wählen:", list(SECTORS.keys()))
sector_companies = SECTORS[selected_sector_name]

# 2. Unternehmen Auswahl (Basierend auf Sektor)
selected_companies_list = st.sidebar.multiselect(
    "Unternehmen vergleichen:",
    options=list(sector_companies.keys()),
    default=list(sector_companies.keys())[:3] # Standardmäßig die ersten 3
)

# Zeitraum
start_date = st.sidebar.date_input("Startdatum", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("Enddatum", value=datetime.now())

# Ticker Mapping
selected_tickers = [sector_companies[name] for name in selected_companies_list]

# --- DATEN LADEN ---
@st.cache_data
def load_price_data(tickers, start, end):
    if not tickers:
        return pd.DataFrame()
    data = yf.download(tickers, start=start, end=end)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()
        data.columns = tickers
    return data.dropna(how='all')

@st.cache_data
def load_company_details(ticker_symbol):
    """Lädt Bilanz UND Info-Daten für die Bewertung"""
    stock = yf.Ticker(ticker_symbol)
    return stock.balance_sheet, stock.info

# --- HAUPTTEIL ---

if len(selected_tickers) > 0:
    
    # === 1. CHART ANZEIGE ===
    st.subheader(f"📈 Performance-Vergleich: {selected_sector_name}")
    df = load_price_data(selected_tickers, start_date, end_date)
    
    if not df.empty:
        # Normalisierung
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

    # === 2. FUNDAMENTAL-ANALYSE & BEWERTUNG ===
    st.subheader("🔍 Fundamentalanalyse & Bewertungssignal")
    
    tabs = st.tabs(selected_companies_list)

    for i, company_name in enumerate(selected_companies_list):
        ticker = selected_tickers[i]
        
        with tabs[i]:
            with st.spinner(f"Analysiere {company_name}..."):
                bs, info = load_company_details(ticker)
            
            # Währung
            currency = info.get('currency', 'USD')
            if currency == 'EUR': currency_sym = '€'
            elif currency == 'USD': currency_sym = '$'
            else: currency_sym = currency

            # --- A. BEWERTUNGS-SIGNAL (NEU!) ---
            valuation = analyze_valuation(info)
            
            # Container mit Hintergrundfarbe für das Signal
            st.markdown(f"""
            <div style="padding: 15px; border-radius: 10px; border: 1px solid #333; background-color: #262730; margin-bottom: 20px;">
                <h3 style="margin:0; color: {valuation['color']};">{valuation['signal']}</h3>
                <p style="margin-top:5px; font-style: italic;">"{valuation['reason']}"</p>
            </div>
            """, unsafe_allow_html=True)

            # Metriken für die Bewertung anzeigen
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            metrics = valuation['metrics']
            
            def safe_num(n): return f"{n:.2f}" if n is not None else "-"
            
            m_col1.metric("KGV (P/E)", safe_num(metrics['KGV (P/E)']), help="< 15 gilt oft als günstig")
            m_col2.metric("PEG Ratio", safe_num(metrics['PEG Ratio']), help="< 1.0 gilt als unterbewertet (Wachstum vs Preis)")
            m_col3.metric("KBV (P/B)", safe_num(metrics['KBV (P/B)']), help="Preis im Verhältnis zum Buchwert (Eigenkapital)")
            m_col4.metric("Forward P/E", safe_num(metrics['Forward P/E']), help="Erwartetes KGV nächstes Jahr")
            
            st.divider()

            # --- B. BILANZ-DATEN (EXISTIEREND) ---
            if not bs.empty:
                # Schnell-KPIs aus der Bilanz
                try:
                    total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
                    equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else 0
                    debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else (
                        bs.loc['Total Liabilities Net Minority Interest'].iloc[0] if 'Total Liabilities Net Minority Interest' in bs.index else 0
                    )
                    
                    kpi1, kpi2, kpi3 = st.columns(3)
                    kpi1.metric("Gesamtvermögen", format_currency_value(total_assets, currency_sym))
                    kpi2.metric("Eigenkapital", format_currency_value(equity, currency_sym))
                    
                    if equity > 0:
                        debt_equity = debt / equity
                        kpi3.metric("Verschuldungsgrad (D/E)", f"{debt_equity:.2f}")
                except:
                    st.caption("Einige Bilanz-KPIs nicht verfügbar.")

                # Detaillierte Tabelle
                display_df = bs.copy()
                # Spalten formatieren (Jahreszahlen)
                new_cols = []
                for c in display_df.columns:
                    try: new_cols.append(str(pd.to_datetime(c).year))
                    except: new_cols.append(str(c))
                display_df.columns = new_cols
                
                # Werte formatieren
                display_df = display_df.applymap(lambda x: format_currency_value(x, currency_sym))
                
                with st.expander("Vollständige Bilanz ansehen"):
                    st.dataframe(display_df, use_container_width=True)
            else:
                st.warning("Keine detaillierten Bilanzdaten verfügbar.")

else:
    st.info("Bitte wähle eine Branche und Unternehmen in der Sidebar aus.")
