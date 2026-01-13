import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Trends & Valuation", page_icon="🌍", layout="wide")
st.title("🌍 Global Market Trends & Valuation Tool")
st.markdown("Analyse von über 80 Unternehmen in 8 Sektoren mit automatischer Bewertungs-Logik.")

# --- DATEN DEFINITIONEN (ERWEITERT) ---
SECTORS = {
    "✈️ Luft- & Raumfahrt (Defense)": {
        'Airbus SE': 'AIR.PA', 'Boeing Co.': 'BA', 'Lockheed Martin': 'LMT',
        'Northrop Grumman': 'NOC', 'Rheinmetall': 'RHM.DE', 'Safran SA': 'SAF.PA',
        'L3Harris': 'LHX', 'General Dynamics': 'GD', 'Thales': 'HO.PA',
        'Leonardo': 'LDO.MI', 'MTU Aero Engines': 'MTX.DE', 'Dassault Aviation': 'AM.PA',
        'Hensoldt': 'HAG.DE', 'Textron': 'TXT'
    },
    "🤖 KI & Halbleiter": {
        'Nvidia': 'NVDA', 'TSMC': 'TSM', 'ASML Holding': 'ASML',
        'AMD': 'AMD', 'Intel': 'INTC', 'Broadcom': 'AVGO',
        'Qualcomm': 'QCOM', 'Texas Instruments': 'TXN', 'Micron': 'MU',
        'Applied Materials': 'AMAT', 'Lam Research': 'LRCX', 'Infineon': 'IFX.DE'
    },
    "☁️ Big Tech & Software": {
        'Microsoft': 'MSFT', 'Apple': 'AAPL', 'Alphabet (Google)': 'GOOGL',
        'Amazon': 'AMZN', 'Meta Platforms': 'META', 'Salesforce': 'CRM',
        'Oracle': 'ORCL', 'Adobe': 'ADBE', 'SAP SE': 'SAP',
        'ServiceNow': 'NOW', 'Palo Alto Networks': 'PANW', 'Palantir': 'PLTR'
    },
    "🧬 Healthcare & Langlebigkeit": {
        'Novo Nordisk': 'NVO', 'Eli Lilly': 'LLY', 'Intuitive Surgical': 'ISRG',
        'Vertex Pharma': 'VRTX', 'Pfizer': 'PFE', 'Moderna': 'MRNA',
        'Johnson & Johnson': 'JNJ', 'AbbVie': 'ABBV', 'Merck & Co.': 'MRK',
        'Amgen': 'AMGN', 'Stryker': 'SYK', 'Thermo Fisher': 'TMO'
    },
    "⚡ GreenTech & Energie": {
        'Siemens Energy': 'ENR.DE', 'NextEra Energy': 'NEE', 'Schneider Electric': 'SU.PA',
        'First Solar': 'FSLR', 'Vestas Wind Systems': 'VWS.CO', 'Enphase Energy': 'ENPH',
        'Orsted': 'ORSTED.CO', 'Iberdrola': 'IBE.MC', 'Enel': 'ENEL.MI',
        'SolarEdge': 'SEDG', 'Brookfield Renewable': 'BEP', 'Plug Power': 'PLUG'
    },
    "🚗 E-Mobilität & Auto": {
        'Tesla': 'TSLA', 'BYD Co.': 'BYDDF', 'Volkswagen Vz.': 'VOW3.DE',
        'BMW': 'BMW.DE', 'Mercedes-Benz': 'MBG.DE', 'Stellantis': 'STLA',
        'Rivian': 'RIVN', 'NIO': 'NIO', 'Toyota Motor': 'TM', 
        'Ferrari': 'RACE', 'Porsche AG': 'P911.DE'
    },
    "🌏 Emerging Markets & Konsum": {
        'MercadoLibre': 'MELI', 'HDFC Bank': 'HDB', 'LVMH': 'MC.PA',
        'Alibaba': 'BABA', 'Sea Limited': 'SE', 'Tencent': 'TCEHY',
        'JD.com': 'JD', 'Infosys': 'INFY', 'ICICI Bank': 'IBN',
        'Petrobras': 'PBR', 'Hermès': 'RMS.PA'
    },
    "💰 Finanzen & Fintech": {
        'JPMorgan Chase': 'JPM', 'Visa': 'V', 'Mastercard': 'MA',
        'BlackRock': 'BLK', 'Goldman Sachs': 'GS', 'Morgan Stanley': 'MS',
        'PayPal': 'PYPL', 'Block (Square)': 'SQ', 'Allianz SE': 'ALV.DE',
        'Munich Re': 'MUV2.DE', 'Berkshire Hathaway': 'BRK-B'
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
    """
    pe_ratio = info.get('trailingPE')
    peg_ratio = info.get('pegRatio')
    pb_ratio = info.get('priceToBook')
    forward_pe = info.get('forwardPE')

    signal = "⚪ Keine Daten"
    color = "gray"
    reason = "Zu wenig Daten für eine Bewertung."

    # Bewertungs-Logik (Vereinfacht)
    if (peg_ratio is not None and peg_ratio < 1.0) or \
       (pe_ratio is not None and pe_ratio < 15 and pb_ratio is not None and pb_ratio < 1.5):
        signal = "🟢 UNTERBEWERTET"
        color = "#2ca02c" # Grün
        reason = "Günstig bewertet relativ zum Wachstum (PEG < 1) oder Buchwert."
    
    elif (peg_ratio is not None and 1.0 <= peg_ratio <= 2.2) or \
         (pe_ratio is not None and 15 <= pe_ratio <= 35):
        signal = "🟡 FAIR BEWERTET"
        color = "#FFD700" # Gold
        reason = "Bewertung entspricht den Wachstumsaussichten oder Marktstandard."

    elif (pe_ratio is not None and pe_ratio > 35) or (peg_ratio is not None and peg_ratio > 2.5):
        signal = "🔴 HOCH BEWERTET"
        color = "#d62728" # Rot
        reason = "Hohes KGV oder teuer im Verhältnis zum Wachstum (Premium-Bewertung)."

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

# 2. Unternehmen Auswahl
selected_companies_list = st.sidebar.multiselect(
    "Unternehmen vergleichen:",
    options=list(sector_companies.keys()),
    default=list(sector_companies.keys())[:3]
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
    try:
        stock = yf.Ticker(ticker_symbol)
        return stock.balance_sheet, stock.info
    except:
        return pd.DataFrame(), {}

# --- HAUPTTEIL ---

if len(selected_tickers) > 0:
    
    # === 1. CHART ANZEIGE ===
    st.subheader(f"📈 Performance-Vergleich: {selected_sector_name}")
    
    with st.spinner("Lade Kursdaten..."):
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
        fig.update_layout(yaxis_title="Performance %", hovermode="x unified", height=450)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === 2. FUNDAMENTAL-ANALYSE & BEWERTUNG ===
    st.subheader("🔍 Fundamentalanalyse & Bewertungssignal")
    
    if len(selected_companies_list) > 6:
        st.warning("⚠️ Hinweis: Das Laden von Detaildaten für viele Unternehmen kann einen Moment dauern.")

    tabs = st.tabs(selected_companies_list)

    for i, company_name in enumerate(selected_companies_list):
        ticker = selected_tickers[i]
        
        with tabs[i]:
            with st.spinner(f"Analysiere {company_name}..."):
                bs, info = load_company_details(ticker)
            
            if info:
                # Währung
                currency = info.get('currency', 'USD')
                if currency == 'EUR': currency_sym = '€'
                elif currency == 'USD': currency_sym = '$'
                else: currency_sym = currency

                # --- A. BEWERTUNGS-SIGNAL ---
                valuation = analyze_valuation(info)
                
                st.markdown(f"""
                <div style="padding: 15px; border-radius: 10px; border: 1px solid #444; background-color: #262730; margin-bottom: 20px;">
                    <h3 style="margin:0; color: {valuation['color']};">{valuation['signal']}</h3>
                    <p style="margin-top:5px; margin-bottom:0; font-style: italic;">"{valuation['reason']}"</p>
                </div>
                """, unsafe_allow_html=True)

                # Metriken
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                metrics = valuation['metrics']
                
                def safe_num(n): return f"{n:.2f}" if n is not None else "-"
                
                m_col1.metric("KGV (P/E)", safe_num(metrics['KGV (P/E)']))
                m_col2.metric("PEG Ratio", safe_num(metrics['PEG Ratio']))
                m_col3.metric("KBV (P/B)", safe_num(metrics['KBV (P/B)']))
                m_col4.metric("Forward P/E", safe_num(metrics['Forward P/E']))
                
                st.divider()

                # --- B. BILANZ-DATEN ---
                if not bs.empty:
                    try:
                        total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
                        equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else 0
                        debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else 0
                        
                        kpi1, kpi2, kpi3 = st.columns(3)
                        kpi1.metric("Gesamtvermögen", format_currency_value(total_assets, currency_sym))
                        kpi2.metric("Eigenkapital", format_currency_value(equity, currency_sym))
                        
                        if equity > 0:
                            debt_equity = debt / equity
                            kpi3.metric("Verschuldungsgrad (D/E)", f"{debt_equity:.2f}")
                    except:
                        pass

                    # Tabelle formatieren
                    display_df = bs.copy()
                    new_cols = []
                    for c in display_df.columns:
                        try: new_cols.append(str(pd.to_datetime(c).year))
                        except: new_cols.append(str(c))
                    display_df.columns = new_cols
                    display_df = display_df.applymap(lambda x: format_currency_value(x, currency_sym))
                    
                    with st.expander(f"Detaillierte Bilanz: {company_name}"):
                        st.dataframe(display_df, use_container_width=True)
            else:
                st.error("Keine Detaildaten verfügbar.")

else:
    st.info("Bitte wähle eine Branche und Unternehmen in der Sidebar aus.")
