import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- SEITEN KONFIGURATION ---
st.set_page_config(page_title="Strategic Market Radar", page_icon="🧠", layout="wide")
st.title("🧠 Strategic Market Radar: Porter & Rationale Erwartungen")
st.markdown("""
Kombiniert Finanzdaten mit Erkenntnissen aus **Porters Wettbewerbsstrategie** (Moat/Qualität) 
und der **Theorie Rationaler Erwartungen** (Marktstimmung/Momentum).
""")

# --- DATEN DEFINITIONEN ---
SECTORS = {
    "✈️ Luft- & Raumfahrt (Defense)": {
        'Airbus SE': 'AIR.PA', 'Boeing Co.': 'BA', 'Lockheed Martin': 'LMT',
        'Rheinmetall': 'RHM.DE', 'Safran': 'SAF.PA', 'Rolls-Royce': 'RR.L'
    },
    "🤖 KI & Halbleiter": {
        'Nvidia': 'NVDA', 'TSMC': 'TSM', 'ASML': 'ASML', 'Intel': 'INTC', 'AMD': 'AMD'
    },
    "🚗 E-Mobilität & Auto": {
        'Tesla': 'TSLA', 'BYD': 'BYDDF', 'VW': 'VOW3.DE', 'Mercedes': 'MBG.DE', 'BMW': 'BMW.DE'
    },
    "🧬 Healthcare": {
        'Novo Nordisk': 'NVO', 'Eli Lilly': 'LLY', 'Pfizer': 'PFE', 'Bayer': 'BAYN.DE'
    }
}

# --- HILFSFUNKTIONEN ---

def format_currency(value, symbol):
    if not value or pd.isna(value): return "-"
    if abs(value) >= 1e9: return f"{value/1e9:.1f} Mrd. {symbol}"
    return f"{value/1e6:.1f} Mio. {symbol}"

# === 1. PORTER-ANALYSE (STRATEGIE) ===
def calculate_porter_score(info):
    """
    Quantifiziert Porters 'Five Forces' & Generische Strategien anhand von Finanzkennzahlen.
    Score von 0 (Schlecht) bis 10 (Hervorragender Moat).
    """
    score = 0
    reasons = []
    
    # 1. Differenzierung / Pricing Power (Bruttomarge)
    # Wer hohe Margen hat, hat ein einzigartiges Produkt (Porter: Differentiation)
    gross_margin = info.get('grossMargins', 0)
    if gross_margin > 0.50: 
        score += 3
        reasons.append("💎 Extrem hohe Pricing Power (Gross Margin > 50%)")
    elif gross_margin > 0.30: 
        score += 2
        reasons.append("✅ Gute Differenzierung (Gross Margin > 30%)")
    elif gross_margin < 0.10:
        score -= 1
        reasons.append("⚠️ Preiskampf / Commodity (Niedrige Marge)")

    # 2. Eintrittsbarrieren / Effizienz (ROIC / ROE)
    # Hoher ROE bedeutet, Konkurrenten können das Kapital nicht so effizient einsetzen.
    roe = info.get('returnOnEquity', 0)
    if roe > 0.20: 
        score += 3
        reasons.append("🏰 Hohe Eintrittsbarrieren (ROE > 20%)")
    elif roe > 0.12: 
        score += 1
    
    # 3. Marktführerschaft / Skaleneffekte (Op. Marge vs. Branchendurchschnitt proxy)
    op_margin = info.get('operatingMargins', 0)
    if op_margin > 0.15: 
        score += 2
        reasons.append("⚙️ Kostenführerschaft/Effizienz (Op. Margin > 15%)")
    
    # 4. Finanzielle Festung (Verschuldung)
    # Ein strategischer Spieler braucht "Deep Pockets" für Preiskriege.
    debt_to_equity = info.get('debtToEquity', 1000) # Falls None, hoch setzen
    if debt_to_equity < 80: # < 0.8
        score += 2
        reasons.append("🛡️ Finanzielle Stärke (Wenig Schulden)")
    
    # Deckelung auf 10
    return min(score, 10), reasons

# === 2. PSYCHOLOGIE / RATIONALE ERWARTUNGEN ===
def analyze_market_psychology(info, price_data):
    """
    Prüft Momentum (Bischof: Behavioral) und Erwartungshaltung (Rational Expectations).
    """
    current_price = price_data.iloc[-1]
    
    # Momentum (200-Tage-Linie) - Trendfolge-Strategie
    sma200 = price_data.rolling(200).mean().iloc[-1]
    trend = "neutral"
    
    if pd.isna(sma200):
        trend_signal = "⚪ Zu wenig Daten"
    elif current_price > sma200:
        trend_signal = "📈 Bullish (Rationaler Aufwärtstrend)"
        trend = "bullish"
    else:
        trend_signal = "📉 Bearish (Marktpreise fallen)"
        trend = "bearish"
        
    # Erwartungs-Check (PEG Ratio)
    # Ist der Markt "irrational exuberant" (zu teuer) oder pessimistisch?
    peg = info.get('pegRatio')
    valuation_msg = ""
    
    if peg and peg > 3.0:
        valuation_msg = "🔥 Markt überhitzt (Hohe Erwartungen eingepreist)"
    elif peg and peg < 0.8:
        valuation_msg = "❄️ Markt pessimistisch (Value Chance?)"
    else:
        valuation_msg = "⚖️ Rationale Bewertung"
        
    return trend_signal, valuation_msg, trend

# --- SIDEBAR ---
st.sidebar.header("⚙️ Auswahl")
sector = st.sidebar.selectbox("Sektor", list(SECTORS.keys()))
tickers_dict = SECTORS[sector]
selected_companies = st.sidebar.multiselect("Unternehmen", list(tickers_dict.keys()), default=list(tickers_dict.keys())[:2])

start_date = datetime.now() - timedelta(days=400) # Genug für SMA200
end_date = datetime.now()

# --- HAUPTTEIL ---

if selected_companies:
    
    # Daten laden
    ticker_symbols = [tickers_dict[name] for name in selected_companies]
    price_df = yf.download(ticker_symbols, start=start_date, end=end_date)['Close']
    
    # Tabs für Analyse-Ebenen
    tab1, tab2 = st.tabs(["🛡️ Porter-Strategie (Fundamental)", "🧠 Markt-Psychologie (Trend)"])
    
    # === TAB 1: PORTER ===
    with tab1:
        st.subheader("Wettbewerbsvorteile nach Porter")
        st.markdown("Wie stark ist der 'Burggraben' (Moat) und die Preissetzungsmacht?")
        
        cols = st.columns(len(selected_companies))
        for idx, company in enumerate(selected_companies):
            ticker = tickers_dict[company]
            stock = yf.Ticker(ticker)
            info = stock.info
            
            score, reasons = calculate_porter_score(info)
            
            # Farb-Codierung für den Score
            score_color = "green" if score >= 7 else "orange" if score >= 4 else "red"
            
            with cols[idx]:
                st.markdown(f"### {company}")
                st.markdown(f"<h1 style='color:{score_color}; font-size: 50px;'>{score}/10</h1>", unsafe_allow_html=True)
                st.caption("Porter-Score (Qualität)")
                
                for r in reasons:
                    st.write(r)
                
                st.divider()
                st.metric("Bruttomarge (Pricing)", f"{info.get('grossMargins', 0):.1%}")
                st.metric("ROE (Barriers)", f"{info.get('returnOnEquity', 0):.1%}")

    # === TAB 2: PSYCHOLOGIE ===
    with tab2:
        st.subheader("Marktphasen & Rationale Erwartungen")
        st.markdown("Handelt der Markt rational oder emotional? (Momentum & Bewertung)")
        
        # Chart zeichnen
        if not price_df.empty:
            # Rebase auf 100 für Vergleichbarkeit
            norm_df = price_df / price_df.iloc[0] * 100
            st.line_chart(norm_df)
        
        p_cols = st.columns(len(selected_companies))
        for idx, company in enumerate(selected_companies):
            ticker = tickers_dict[company]
            # Einzeldaten für SMA
            single_price = price_df[ticker].dropna() if isinstance(price_df, pd.DataFrame) else price_df.dropna()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            trend_sig, val_msg, trend_dir = analyze_market_psychology(info, single_price)
            
            with p_cols[idx]:
                st.markdown(f"### {company}")
                st.info(trend_sig)
                st.write(f"**Marktstimmung:** {val_msg}")
                
                beta = info.get('beta')
                if beta:
                    risk_label = "Volatil (High Risk)" if beta > 1.3 else "Stabil (Defensiv)" if beta < 0.8 else "Marktkonform"
                    st.metric("Risiko-Faktor (Beta)", f"{beta:.2f}", risk_label)

else:
    st.info("Bitte Unternehmen wählen.")
