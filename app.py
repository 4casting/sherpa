import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Global Market Radar", page_icon="📡", layout="wide")
st.title("📡 Global Market Radar & Valuation Matrix")
st.markdown("Analyse von **Top-Playern** in Wachstumssektoren mit automatischer **Bewertungs-Matrix**.")

# --- DATEN DEFINITIONEN (MASSIV ERWEITERT) ---
SECTORS = {
    "✈️ Luft- & Raumfahrt (Defense)": {
        'Airbus SE': 'AIR.PA', 'Boeing Co.': 'BA', 'Lockheed Martin': 'LMT',
        'Northrop Grumman': 'NOC', 'Rheinmetall': 'RHM.DE', 'Safran SA': 'SAF.PA',
        'L3Harris': 'LHX', 'General Dynamics': 'GD', 'Thales': 'HO.PA',
        'Leonardo': 'LDO.MI', 'MTU Aero Engines': 'MTX.DE', 'Dassault Aviation': 'AM.PA',
        'Hensoldt': 'HAG.DE', 'Textron': 'TXT', 'Rolls-Royce': 'RR.L',
        'BAE Systems': 'BA.L', 'TransDigm': 'TDG', 'Howmet Aerospace': 'HWM'
    },
    "🤖 KI & Halbleiter": {
        'Nvidia': 'NVDA', 'TSMC': 'TSM', 'ASML Holding': 'ASML',
        'AMD': 'AMD', 'Intel': 'INTC', 'Broadcom': 'AVGO',
        'Qualcomm': 'QCOM', 'Texas Instruments': 'TXN', 'Micron': 'MU',
        'Applied Materials': 'AMAT', 'Lam Research': 'LRCX', 'Infineon': 'IFX.DE',
        'KLA Corp': 'KLAC', 'Synopsys': 'SNPS', 'Cadence Design': 'CDNS',
        'Arm Holdings': 'ARM', 'Super Micro Computer': 'SMCI', 'Marvell Tech': 'MRVL'
    },
    "☁️ Big Tech & Software": {
        'Microsoft': 'MSFT', 'Apple': 'AAPL', 'Alphabet (Google)': 'GOOGL',
        'Amazon': 'AMZN', 'Meta Platforms': 'META', 'Salesforce': 'CRM',
        'Oracle': 'ORCL', 'Adobe': 'ADBE', 'SAP SE': 'SAP',
        'ServiceNow': 'NOW', 'Palo Alto Networks': 'PANW', 'Palantir': 'PLTR',
        'Intuit': 'INTU', 'Snowflake': 'SNOW', 'Datadog': 'DDOG',
        'CrowdStrike': 'CRWD', 'Atlassian': 'TEAM', 'Uber Technologies': 'UBER'
    },
    "🧬 Healthcare & Langlebigkeit": {
        'Novo Nordisk': 'NVO', 'Eli Lilly': 'LLY', 'Intuitive Surgical': 'ISRG',
        'Vertex Pharma': 'VRTX', 'Pfizer': 'PFE', 'Moderna': 'MRNA',
        'Johnson & Johnson': 'JNJ', 'AbbVie': 'ABBV', 'Merck & Co.': 'MRK',
        'Amgen': 'AMGN', 'Stryker': 'SYK', 'Thermo Fisher': 'TMO',
        'Boston Scientific': 'BSX', 'Abbott Labs': 'ABT', 'Danaher': 'DHR',
        'Regeneron': 'REGN', 'Sanofi': 'SAN.PA', 'Novartis': 'NOVN.SW'
    },
    "⚡ GreenTech & Energie": {
        'Siemens Energy': 'ENR.DE', 'NextEra Energy': 'NEE', 'Schneider Electric': 'SU.PA',
        'First Solar': 'FSLR', 'Vestas Wind Systems': 'VWS.CO', 'Enphase Energy': 'ENPH',
        'Orsted': 'ORSTED.CO', 'Iberdrola': 'IBE.MC', 'Enel': 'ENEL.MI',
        'SolarEdge': 'SEDG', 'Brookfield Renewable': 'BEP', 'Plug Power': 'PLUG',
        'Canadian Solar': 'CSIQ', 'SMA Solar': 'S92.DE', 'Nordex': 'NDX1.DE',
        'Bloom Energy': 'BE', 'RWE AG': 'RWE.DE'
    },
    "🚗 E-Mobilität & Auto": {
        'Tesla': 'TSLA', 'BYD Co.': 'BYDDF', 'Volkswagen Vz.': 'VOW3.DE',
        'BMW': 'BMW.DE', 'Mercedes-Benz': 'MBG.DE', 'Stellantis': 'STLA',
        'Rivian': 'RIVN', 'NIO': 'NIO', 'Toyota Motor': 'TM', 
        'Ferrari': 'RACE', 'Porsche AG': 'P911.DE', 'Honda Motor': 'HMC',
        'Ford Motor': 'F', 'General Motors': 'GM', 'Li Auto': 'LI',
        'XPeng': 'XPEV', 'Lucid Group': 'LCID'
    },
    "🌏 Emerging Markets & Konsum": {
        'MercadoLibre': 'MELI', 'HDFC Bank': 'HDB', 'LVMH': 'MC.PA',
        'Alibaba': 'BABA', 'Sea Limited': 'SE', 'Tencent': 'TCEHY',
        'JD.com': 'JD', 'Infosys': 'INFY', 'ICICI Bank': 'IBN',
        'Petrobras': 'PBR', 'Hermès': 'RMS.PA', 'Nubank': 'NU',
        'StoneCo': 'STNE', 'Coupang': 'CPNG', 'Baidu': 'BIDU',
        'PDD Holdings (Temu)': 'PDD', 'Reliance Industries': 'RELIANCE.NS'
    },
    "💰 Finanzen & Fintech": {
        'JPMorgan Chase': 'JPM', 'Visa': 'V', 'Mastercard': 'MA',
        'BlackRock': 'BLK', 'Goldman Sachs': 'GS', 'Morgan Stanley': 'MS',
        'PayPal': 'PYPL', 'Block (Square)': 'SQ', 'Allianz SE': 'ALV.DE',
        'Munich Re': 'MUV2.DE', 'Berkshire Hathaway': 'BRK-B',
        'American Express': 'AXP', 'Citigroup': 'C', 'Wells Fargo': 'WFC',
        'Bank of America': 'BAC', 'Charles Schwab': 'SCHW', 'Adyen': 'ADYEN.AS'
    }
}

# --- HILFSFUNKTIONEN ---

def format_currency_value(value, currency_symbol=""):
    """Formatiert große Zahlen (Mrd/Mio)."""
    if value is None or pd.isna(value): return "-"
    abs_val = abs(value)
    if abs_val >= 1e9: return f"{value / 1e9:.2f} Mrd. {currency_symbol}"
    elif abs_val >= 1e6: return f"{value / 1e6:.2f} Mio. {currency_symbol}"
    else: return f"{value:.2f} {currency_symbol}"

def analyze_valuation(info):
    """
    Erstellt ein Bewertungssignal und gibt strukturierte Daten zurück.
    """
    pe_ratio = info.get('trailingPE')
    peg_ratio = info.get('pegRatio')
    pb_ratio = info.get('priceToBook')
    forward_pe = info.get('forwardPE')

    signal = "⚪ Neutral / Keine Daten"
    color = "gray"
    # Einfache Logik für die Tabelle
    sort_score = 2 

    if (peg_ratio is not None and peg_ratio < 1.0) or \
       (pe_ratio is not None and 0 < pe_ratio < 15 and pb_ratio is not None and pb_ratio < 1.5):
        signal = "🟢 UNTERBEWERTET"
        color = "green"
        sort_score = 1
    
    elif (peg_ratio is not None and 1.0 <= peg_ratio <= 2.2) or \
         (pe_ratio is not None and 15 <= pe_ratio <= 35):
        signal = "🟡 FAIR"
        color = "orange"
        sort_score = 2

    elif (pe_ratio is not None and pe_ratio > 35) or (peg_ratio is not None and peg_ratio > 2.5):
        signal = "🔴 HOCH"
        color = "red"
        sort_score = 3

    return {
        "signal": signal,
        "color": color,
        "metrics": {
            "KGV": pe_ratio,
            "PEG": peg_ratio,
            "KBV": pb_ratio,
            "Fwd KGV": forward_pe
        },
        "sort_score": sort_score
    }

# --- SIDEBAR KONFIGURATION ---
st.sidebar.header("⚙️ Konfiguration")

selected_sector_name = st.sidebar.selectbox("Branche wählen:", list(SECTORS.keys()))
sector_companies = SECTORS[selected_sector_name]

# Standardmäßig die ersten 5 auswählen, damit es nicht zu langsam lädt
default_selection = list(sector_companies.keys())[:5]
selected_companies_list = st.sidebar.multiselect(
    "Unternehmen vergleichen:",
    options=list(sector_companies.keys()),
    default=default_selection
)

start_date = st.sidebar.date_input("Startdatum", value=datetime.now() - timedelta(days=365))
end_date = st.sidebar.date_input("Enddatum", value=datetime.now())

selected_tickers = [sector_companies[name] for name in selected_companies_list]

# --- DATEN LADEN ---
@st.cache_data
def load_price_data(tickers, start, end):
    if not tickers: return pd.DataFrame()
    data = yf.download(tickers, start=start, end=end)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()
        data.columns = tickers
    return data.dropna(how='all')

@st.cache_data
def get_company_info_batch(ticker_list):
    """Lädt Infos für mehrere Ticker effizient."""
    results = {}
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            # Wir holen nur info und bilanz bei Bedarf, hier nur Info für die Tabelle
            results[t] = stock.info
        except:
            results[t] = {}
    return results

@st.cache_data
def load_balance_sheet(ticker):
    try:
        return yf.Ticker(ticker).balance_sheet
    except:
        return pd.DataFrame()

# --- HAUPTTEIL ---

if len(selected_tickers) > 0:
    
    # === 1. CHART ===
    st.subheader(f"📈 Performance: {selected_sector_name}")
    with st.spinner("Lade Kursdaten..."):
        df = load_price_data(selected_tickers, start_date, end_date)
    
    if not df.empty:
        normalized_df = df / df.iloc[0]
        df['Portfolio_Index'] = normalized_df.mean(axis=1)
        
        plot_data = (normalized_df * 100) - 100
        plot_data['Durchschnitt'] = (df['Portfolio_Index'] * 100) - 100
        
        fig = go.Figure()
        for column in plot_data.columns:
            if column != 'Durchschnitt':
                fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data[column], mode='lines', name=column, opacity=0.3))
        
        fig.add_trace(go.Scatter(x=plot_data.index, y=plot_data['Durchschnitt'], mode='lines', name='DURCHSCHNITT', line=dict(color='white', width=4)))
        fig.update_layout(yaxis_title="Performance %", hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # === 2. ÜBERSICHTS-MATRIX (TABELLE) ===
    st.subheader("📊 Bewertungs-Matrix (Sektor Übersicht)")
    st.caption("Vergleich der ausgewählten Unternehmen basierend auf aktuellen Fundamentaldaten.")
    
    with st.spinner("Analysiere Fundamentaldaten für die Übersicht..."):
        # Daten für alle ausgewählten Ticker laden
        infos = get_company_info_batch(selected_tickers)
        
        table_data = []
        for i, company_name in enumerate(selected_companies_list):
            ticker = selected_tickers[i]
            info = infos.get(ticker, {})
            
            # Analyse durchführen
            val = analyze_valuation(info)
            metrics = val['metrics']
            
            # Währung
            curr = info.get('currency', '')
            price = info.get('currentPrice', 'N/A')
            
            table_data.append({
                "Unternehmen": company_name,
                "Ticker": ticker,
                "Preis": f"{price} {curr}",
                "Signal": val['signal'], # Für Sortierung/Farbe
                "KGV (P/E)": metrics['KGV'],
                "PEG Ratio": metrics['PEG'],
                "KBV (P/B)": metrics['KBV'],
                "Fwd KGV": metrics['Fwd KGV'],
            })
            
        # DataFrame erstellen
        overview_df = pd.DataFrame(table_data)
        
        # DataFrame anzeigen mit Styling
        if not overview_df.empty:
            st.dataframe(
                overview_df,
                column_config={
                    "Signal": st.column_config.TextColumn(
                        "Bewertung",
                        help="Grün = Günstig/Unterbewertet, Gelb = Fair, Rot = Hoch bewertet",
                    ),
                    "KGV (P/E)": st.column_config.NumberColumn("KGV", format="%.1f"),
                    "PEG Ratio": st.column_config.NumberColumn("PEG", format="%.2f"),
                    "KBV (P/B)": st.column_config.NumberColumn("KBV", format="%.1f"),
                    "Fwd KGV": st.column_config.NumberColumn("Fwd KGV", format="%.1f"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Keine Daten für die Matrix verfügbar.")

    st.markdown("---")

    # === 3. DETAIL-ANSICHT (TABS) ===
    st.subheader("🔍 Tiefenanalyse & Bilanzen")
    
    tabs = st.tabs(selected_companies_list)

    for i, company_name in enumerate(selected_companies_list):
        ticker = selected_tickers[i]
        
        with tabs[i]:
            # Wir nutzen die bereits geladenen Infos, laden aber die Bilanz frisch
            info = infos.get(ticker, {})
            
            with st.spinner(f"Lade Bilanz für {company_name}..."):
                bs = load_balance_sheet(ticker)
            
            # Währung bestimmen
            currency = info.get('currency', 'USD')
            sym = '€' if currency == 'EUR' else '$'
            
            # Noch mal das Signal groß anzeigen
            val = analyze_valuation(info)
            st.markdown(f"**Bewertung:** {val['signal']}")
            
            if not bs.empty:
                # KPIs
                try:
                    assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
                    equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else 0
                    debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else 0
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Gesamtvermögen", format_currency_value(assets, sym))
                    c2.metric("Eigenkapital", format_currency_value(equity, sym))
                    if equity > 0:
                        c3.metric("Verschuldungsgrad", f"{debt/equity:.2f}")
                except:
                    pass
                
                # Tabelle formatieren
                disp_df = bs.copy()
                cols = []
                for c in disp_df.columns:
                    try: cols.append(str(pd.to_datetime(c).year))
                    except: cols.append(str(c))
                disp_df.columns = cols
                disp_df = disp_df.applymap(lambda x: format_currency_value(x, sym))
                
                st.dataframe(disp_df, use_container_width=True)
            else:
                st.info("Keine detaillierte Bilanz verfügbar.")

else:
    st.info("Bitte wähle eine Branche und Unternehmen in der Sidebar aus.")
